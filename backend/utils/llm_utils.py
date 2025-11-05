import asyncio
import inspect
import logging
import os
from typing import Literal, Type, TypedDict, TypeVar

import openai
from openai import ContentFilterFinishReasonError, LengthFinishReasonError
from openai.types.chat import ParsedChatCompletion
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)
from pydantic import BaseModel

from backend.utils import cache_utils, helpers

logger = logging.getLogger(__name__)


# Define a TypeVar for Pydantic models
T = TypeVar("T", bound=BaseModel)


class TextResponseFormat(TypedDict):
    type: Literal["text"]


class JsonResponseFormat(TypedDict):
    type: Literal["json_object"]


async def generate_openai_parsed_completion(
    client: openai.AsyncOpenAI,
    logger: logging.Logger,
    hash_key: str,
    prompt: str,
    response_model: Type[T],
    model_name: str,
    temperature: float,
    reasoning_effort: Literal["low", "medium", "high"] | None = None,
    url: str | None = None,
    sema: asyncio.Semaphore = asyncio.Semaphore(5),
    calling_context: str | None = None,
) -> T:
    """Generates a completion using OpenAI and parses it into a Pydantic model."""
    full_calling_context = calling_context
    try:
        # Get the frame of the caller (1 level up)
        caller_frame = inspect.stack()[1]
        caller_filename = os.path.basename(caller_frame.filename)
        if calling_context:
            full_calling_context = f"{caller_filename}::{calling_context}"
        else:
            pass
    except IndexError:
        logger.warning("Could not determine caller filename for context prefixing.")

    # Use the full calling context to disambiguate the cache key
    cache_key = helpers.create_cache_key(hash_key, context=full_calling_context)
    cached_data = await cache_utils.read_cache(cache_key)

    if cached_data:
        logger.debug(
            f"Using cached parsed OpenAI response {f'for URL: {url}' if url else ''}"
        )
        try:
            # read_cache returns dict/list/primitive already parsed from JSON
            return response_model.model_validate(cached_data)
        except Exception as e:
            logger.warning(
                f"Failed to parse cached data for {hash_key} ({type(cached_data)}): {e}. Re-fetching."
            )

    async with sema:
        try:
            messages: list[ChatCompletionMessageParam] = [
                ChatCompletionUserMessageParam(role="user", content=prompt),
            ]

            # Log the arguments being sent
            logger.debug(f"Calling client.beta.chat.completions.parse for {hash_key}:")
            logger.debug(f"  Model: {model_name}")
            logger.debug(f"  Temperature: {temperature}")
            logger.debug(f"  Response Model: {response_model.__name__}")
            logger.debug(
                f"  Messages: {messages}"
            )  # Log the whole messages list for structure check
            # logger.debug(f"  Prompt Snippet: {prompt[:500]}...") # Optionally log a snippet

            completion: ParsedChatCompletion[
                T
            ] = await client.beta.chat.completions.parse(
                model=model_name,
                reasoning_effort=reasoning_effort,
                messages=messages,
                temperature=temperature,
                response_format=response_model,
            )

            choice = completion.choices[0]
            if choice.message.parsed is None:
                logger.error(
                    f"Failed to parse response for {hash_key}. Refusal: {choice.message.refusal}"
                )
                raise Exception(
                    f"Failed to parse OpenAI response. Refusal: {choice.message.refusal}"
                )

            result = choice.message.parsed
            # Cache the result as a dictionary (write_cache handles JSON serialization)
            logger.debug(f"Writing OpenAI cache for key: {cache_key}")
            await cache_utils.write_cache(
                cache_key, result.model_dump(), calling_context=full_calling_context
            )
            return result

        except (LengthFinishReasonError, ContentFilterFinishReasonError) as e:
            logger.error(f"Completion failed for {hash_key} due to finish reason: {e}")
            raise e
        except openai.APIConnectionError as e:
            logger.error(
                f"The OpenAI server could not be reached for {hash_key}: {e.__cause__}"
            )
            raise e
        except openai.APIStatusError as e:
            logger.error(
                f"HTTP error while generating parsed OpenAI completion for {hash_key}: {e}"
            )
            raise e
        except Exception as e:
            logger.error(
                f"Unexpected error generating parsed OpenAI completion for {hash_key}: {e}"
            )
            raise e
