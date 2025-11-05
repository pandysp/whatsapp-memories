import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import aiofiles
import asyncclick as click
import openai
from dotenv.main import load_dotenv
from pydantic import ValidationError

from backend.utils import helpers, llm_utils, prompts
from backend.utils.models import CuteMessagesResult

load_dotenv()

# Constants
script_dir = Path(__file__).resolve().parent
data_out_dir = script_dir / "data_out"
data_in_dir = script_dir / "data_in"

# Gemini 2.5 Flash pricing (per 1M tokens)
GEMINI_FLASH_INPUT_COST = 0.075  # $0.075 per 1M input tokens
GEMINI_FLASH_OUTPUT_COST = 0.30  # $0.30 per 1M output tokens


@dataclass
class ProcessingStats:
    """Track statistics during processing"""
    start_time: float = field(default_factory=time.time)
    total_input_messages: int = 0
    total_output_messages: int = 0
    total_exchanges: int = 0
    total_chunks: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    cached_chunks: int = 0
    processed_chunks: int = 0

    def add_tokens(self, input_tokens: int, output_tokens: int, from_cache: bool = False):
        """Add token usage from a completion"""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        if from_cache:
            self.cached_chunks += 1
        else:
            self.processed_chunks += 1

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def input_cost(self) -> float:
        return (self.total_input_tokens / 1_000_000) * GEMINI_FLASH_INPUT_COST

    @property
    def output_cost(self) -> float:
        return (self.total_output_tokens / 1_000_000) * GEMINI_FLASH_OUTPUT_COST

    @property
    def total_cost(self) -> float:
        return self.input_cost + self.output_cost

    @property
    def elapsed_time(self) -> float:
        return time.time() - self.start_time

    @property
    def reduction_percentage(self) -> float:
        if self.total_input_messages == 0:
            return 0.0
        return ((self.total_input_messages - self.total_output_messages) / self.total_input_messages) * 100

    def print_summary(self, logger: logging.Logger):
        """Print a comprehensive summary of processing statistics"""
        logger.warning("\n" + "="*80)
        logger.warning("PROCESSING SUMMARY")
        logger.warning("="*80)

        logger.warning(f"\n📊 Data Statistics:")
        logger.warning(f"  • Input messages:     {self.total_input_messages:,}")
        logger.warning(f"  • Output messages:    {self.total_output_messages:,}")
        logger.warning(f"  • Extracted exchanges: {self.total_exchanges}")
        logger.warning(f"  • Reduction:          {self.reduction_percentage:.1f}%")

        logger.warning(f"\n⚙️  Processing:")
        logger.warning(f"  • Total chunks:       {self.total_chunks}")
        logger.warning(f"  • Cached chunks:      {self.cached_chunks}")
        logger.warning(f"  • Processed chunks:   {self.processed_chunks}")
        logger.warning(f"  • Processing time:    {self.elapsed_time:.2f}s ({self.elapsed_time/60:.1f}m)")

        logger.warning(f"\n🔢 Token Usage:")
        logger.warning(f"  • Input tokens:       {self.total_input_tokens:,}")
        logger.warning(f"  • Output tokens:      {self.total_output_tokens:,}")
        logger.warning(f"  • Total tokens:       {self.total_tokens:,}")

        logger.warning(f"\n💰 Cost Breakdown:")
        logger.warning(f"  • Input cost:         ${self.input_cost:.4f}")
        logger.warning(f"  • Output cost:        ${self.output_cost:.4f}")
        logger.warning(f"  • Total cost:         ${self.total_cost:.4f}")

        if self.total_input_messages > 0:
            cost_per_1k_msgs = (self.total_cost / self.total_input_messages) * 1000
            logger.warning(f"  • Cost per 1k msgs:   ${cost_per_1k_msgs:.4f}")

        logger.warning("\n" + "="*80 + "\n")


@click.command()
@click.option(
    "--log_level",
    default="INFO",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    help="Set log level.",
)
@click.option(
    "--file_in",
    default=str(data_in_dir / "_chat.txt"),
    help="Path to the input text file.",
)
@click.option(
    "--file_out",
    default=str(data_out_dir / "output.txt"),
    help="Path to the output text file.",
)
async def main(log_level: str, file_in: str, file_out: str) -> None:
    """
    Reads a WhatsApp chat file, chunks it by day, extracts cute messages using an LLM,
    filters the best messages using a second LLM pass (potentially with different config),
    formats them as a bulleted list, and saves the results to an output file.
    """
    logger = helpers.configure_logger(log_level)
    stats = ProcessingStats()

    logger.warning("Starting cute message extraction script...")

    # Ensure output directory exists
    data_out_dir.mkdir(exist_ok=True)

    # --- File Reading --- #
    logger.info(f"Reading data from {file_in}...")
    try:
        async with aiofiles.open(file_in, mode="r", encoding="utf-8") as f:
            content = await f.read()
    except FileNotFoundError:
        logger.error(f"Error: Could not open file {file_in}")
        raise click.FileError(filename=str(file_in))
    except Exception as e:
        logger.error(f"Error reading file {file_in}: {e}")
        raise click.ClickException(f"Error reading file: {e}")

    if not content:
        logger.error(f"Input file {file_in} is empty.")
        raise click.UsageError(f"Input file {file_in} is empty.")

    # Count input messages
    input_message_count = content.count('\n')
    stats.total_input_messages = input_message_count
    logger.info(f"Input file contains approximately {input_message_count:,} lines")

    # --- Chunking --- #
    logger.info(f"Chunking text from {file_in} by day...")
    chunks = helpers.chunk_whatsapp_by_day(content)
    stats.total_chunks = len(chunks)
    logger.info(f"Created {len(chunks)} daily chunks.")

    # --- First Pass: Extraction --- #
    logger.info("Creating LLM tasks for extracting cute messages from each chunk...")
    tasks = []
    async with openai.AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        max_retries=10,
    ) as extract_client:
        for i, chunk in enumerate(chunks):
            prompt = prompts.create_extract_cute_messages_prompt(chat_chunk=chunk)
            hash_key = f"{file_in}_day_chunk_{i}"
            logger.info(f"Creating extract task for day chunk {i+1}/{len(chunks)}")

            tasks.append(
                asyncio.create_task(
                    process_chunk_llm(
                        client=extract_client,
                        logger=logger,
                        prompt=prompt,
                        hash_key=hash_key,
                        calling_context="process_chunk_llm",
                        temperature=0.0,
                        stats=stats,
                    )
                )
            )

        logger.info(f"Running {len(tasks)} extraction LLM tasks...")
        results: list[tuple[CuteMessagesResult | None, bool]] = await asyncio.gather(*tasks)

    # --- Collect Initial Exchanges --- #
    logger.info("Collecting all cute exchanges for filtering...")
    all_exchanges = []
    for result_tuple in results:
        result, _ = result_tuple
        if result and result.cute_exchanges:
            all_exchanges.extend(result.cute_exchanges)

    # Count output messages
    output_message_count = sum(
        len(exchange.messages)
        for result_tuple in results
        for result, _ in [result_tuple]
        if result and result.cute_exchanges
        for exchange in result.cute_exchanges
    )

    stats.total_exchanges = len(all_exchanges)
    stats.total_output_messages = output_message_count

    logger.info(f"Found {len(all_exchanges)} total memorable exchanges")
    logger.info("Extraction complete - results stored in database via cache layer")

    # Print comprehensive summary
    stats.print_summary(logger)


async def process_chunk_llm(
    client: openai.AsyncOpenAI,
    logger: logging.Logger,
    prompt: str,
    hash_key: str,
    calling_context: str,
    stats: ProcessingStats,
    model_name: str = "gemini-2.5-flash-preview-05-20",
    reasoning_effort: Literal["low", "medium", "high"] | None = None,
    temperature: float = 0.0,
) -> tuple[CuteMessagesResult | None, bool]:
    """Processes a text chunk using OpenAI and returns the parsed result with cache status."""
    cache_key_display = helpers.create_cache_key(hash_key)
    logger.info(f"Processing chunk with hash: {cache_key_display}, Model: {model_name}")

    try:
        parsed_result, token_usage, from_cache = (
            await llm_utils.generate_openai_parsed_completion_with_stats(
                client=client,
                logger=logger,
                hash_key=hash_key,
                prompt=prompt,
                response_model=CuteMessagesResult,
                model_name=model_name,
                reasoning_effort=reasoning_effort,
                temperature=temperature,
                calling_context=calling_context,
            )
        )

        # Track token usage
        if token_usage:
            stats.add_tokens(
                input_tokens=token_usage.get("prompt_tokens", 0),
                output_tokens=token_usage.get("completion_tokens", 0),
                from_cache=from_cache
            )

    except (ValidationError, Exception) as e:
        logger.warning(
            f"Failed to process chunk {cache_key_display}. Returning None. Error: {e}"
        )
        raise e

    return parsed_result, from_cache


if __name__ == "__main__":
    # TODO: When running directly, asyncclick requires calling the async function
    # This setup is basic; consider using asyncio.run() if needed outside click
    main()
