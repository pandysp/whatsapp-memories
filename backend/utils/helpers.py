import hashlib
import logging
import re

import coloredlogs

from collections import defaultdict


logger = logging.getLogger(__name__)


def configure_logger(level: str) -> logging.Logger:
    """Configures the root 'backend' logger and returns it."""
    app_logger = logging.getLogger("backend")

    app_logger.handlers.clear()
    app_logger.propagate = True  # Explicitly enable propagation

    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")

    app_logger.setLevel(numeric_level)

    # Install coloredlogs (this will add its own handler to the specified logger)
    # Let coloredlogs install on the root logger by default
    coloredlogs.install(
        level=numeric_level,
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",  # Added %(name)s
        datefmt="%H:%M:%S",
    )

    return app_logger


def create_cache_key(hash_key: str, context: str | None = None) -> str:
    key_string = hash_key
    if context:
        key_string += f"::{context}"
    return hashlib.md5(key_string.encode()).hexdigest()


def chunk_whatsapp_by_day(text: str) -> list[str]:
    """
    Chunks WhatsApp chat text by day.

    Handles multi-line messages by appending them to the previous message's day.
    """
    # Regex to match the WhatsApp timestamp format [DD.MM.YY, HH:MM:SS]
    # Allow optional Left-to-Right Mark (U+200E) at the start
    timestamp_pattern = re.compile(
        r"^\u200e?\[(\d{2}\.\d{2}\.\d{2}), (\d{2}:\d{2}:\d{2})\]"
    )
    # Regex to extract just the date part from the first group of the match
    date_pattern = re.compile(r"^(\d{2}\.\d{2}\.\d{2})")

    lines = text.strip().split("\n")
    # Use defaultdict to group lines by date
    daily_chunks = defaultdict(list)
    current_date = None

    for line in lines:
        match = timestamp_pattern.match(line)
        if match:
            # Extract just the date "DD.MM.YY" from the timestamp part
            date_match = date_pattern.search(match.group(1))
            if date_match:
                current_date = date_match.group(1)  # This is the DD.MM.YY
                daily_chunks[current_date].append(line)
            # else: This case should not happen if timestamp_pattern matched
        elif current_date:
            # Append multi-line messages or system messages (like '‎Messages and calls...')
            # or attached file lines to the current day's chunk
            daily_chunks[current_date].append(line)
        # else: Ignore lines before the first valid timestamp message

    # Combine lines for each day into single strings
    result_chunks = ["\n".join(lines) for lines in daily_chunks.values()]

    return result_chunks
