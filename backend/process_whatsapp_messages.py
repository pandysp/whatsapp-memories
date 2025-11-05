import asyncio
import logging
import os
import time
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

    logger.warning("Starting cute message extraction script...")
    start_time = time.time()

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

    # --- Chunking --- #
    logger.info(f"Chunking text from {file_in} by day...")
    chunks = helpers.chunk_whatsapp_by_day(content)
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
                    )
                )
            )

        logger.info(f"Running {len(tasks)} extraction LLM tasks...")
        results: list[CuteMessagesResult | None] = await asyncio.gather(*tasks)

    # --- Collect Initial Exchanges --- #
    logger.info("Collecting all cute exchanges for filtering...")
    all_exchanges = []
    for result in results:
        if result and result.cute_exchanges:
            all_exchanges.extend(result.cute_exchanges)

    logger.info(f"Found {len(all_exchanges)} total memorable exchanges")
    logger.info("Extraction complete - results stored in database via cache layer")

    end_time = time.time()
    logger.warning(f"Processing completed in {end_time - start_time:.2f} seconds")
    logger.warning(f"Extracted {len(all_exchanges)} exchanges from {len(chunks)} daily chunks")


async def process_chunk_llm(
    client: openai.AsyncOpenAI,
    logger: logging.Logger,
    prompt: str,
    hash_key: str,
    calling_context: str,
    model_name: str = "gemini-2.5-flash-preview-05-20",
    reasoning_effort: Literal["low", "medium", "high"] | None = None,
    temperature: float = 0.0,
) -> CuteMessagesResult | None:
    """Processes a text chunk using OpenAI and returns the parsed result."""
    cache_key_display = helpers.create_cache_key(hash_key)
    logger.info(f"Processing chunk with hash: {cache_key_display}, Model: {model_name}")

    try:
        parsed_result: CuteMessagesResult = (
            await llm_utils.generate_openai_parsed_completion(
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

    except (ValidationError, Exception) as e:
        logger.warning(
            f"Failed to process chunk {cache_key_display}. Returning None. Error: {e}"
        )
        raise e

    return parsed_result


if __name__ == "__main__":
    # TODO: When running directly, asyncclick requires calling the async function
    # This setup is basic; consider using asyncio.run() if needed outside click
    main()
