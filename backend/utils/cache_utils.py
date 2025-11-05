import json
import logging
import os
import asyncio
from typing import Any, List, Dict, Optional
from collections import defaultdict

import aiosqlite
from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)

# SQLite database path
# Use /data volume on Fly.io, local file for development
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "/data/backend_cache.db" if os.path.exists("/data") else "backend_cache.db")
logger.info(f"SQLite cache database path: {SQLITE_DB_PATH}")

DB_INITIALIZED = False
DB_INIT_LOCK = asyncio.Lock()


async def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    global DB_INITIALIZED
    async with aiosqlite.connect(SQLITE_DB_PATH) as db:
        # Enable Foreign Keys for this connection if not enabled by default by aiosqlite version
        await db.execute("PRAGMA foreign_keys = ON;")

        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS cache_data (
            key TEXT PRIMARY KEY,
            value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS indexed_keys (
            key TEXT PRIMARY KEY,
            FOREIGN KEY(key) REFERENCES cache_data(key) ON DELETE CASCADE
        )
        """
        )
        # New/updated tables for normalization
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS exchanges (
            exchange_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT NOT NULL,
            exchange_index INTEGER NOT NULL,
            FOREIGN KEY(cache_key) REFERENCES cache_data(key) ON DELETE CASCADE,
            UNIQUE(cache_key, exchange_index)
        )
        """
        )
        await db.execute(
            """
        CREATE TABLE IF NOT EXISTS messages_normalized (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            exchange_id INTEGER NOT NULL,
            message_index_in_exchange INTEGER NOT NULL,
            date TEXT,
            time TEXT,
            person TEXT,
            quote TEXT,
            FOREIGN KEY(exchange_id) REFERENCES exchanges(exchange_id) ON DELETE CASCADE
        )
        """
        )
        await db.commit()
    DB_INITIALIZED = True


async def _ensure_db_initialized():
    """Ensures that the database is initialized, performing initialization if needed."""
    if not DB_INITIALIZED:
        async with DB_INIT_LOCK:
            if not DB_INITIALIZED:  # Double check after acquiring lock
                await init_db()


# Define a generic index key name - This concept is now handled by the 'indexed_keys' table
# Removed: DEFAULT_DATA_INDEX_KEY = "data_keys_index"


async def _add_to_indexed_keys(db: aiosqlite.Connection, key_to_add: str):
    """Helper to add a key to the indexed_keys table."""
    try:
        await db.execute(
            "INSERT OR IGNORE INTO indexed_keys (key) VALUES (?)", (key_to_add,)
        )
        # No separate commit here, assumes it's part of a larger transaction
        logger.info(f"Added/Ensured key in indexed_keys: {key_to_add}")
    except Exception as e:
        logger.error(
            f"Failed to add key '{key_to_add}' to indexed_keys ({type(e).__name__}): {e}"
        )


async def read_cache(cache_key: str) -> Any | None:
    """Reads data from the SQLite cache (raw JSON value).
    Returns None if key not found. No expiration check.
    Handles JSON decoding.
    """
    await _ensure_db_initialized()
    try:
        async with aiosqlite.connect(SQLITE_DB_PATH) as db:
            async with db.execute(
                "SELECT value FROM cache_data WHERE key = ?", (cache_key,)
            ) as cursor:
                row = await cursor.fetchone()

            if row is None:
                logger.debug(f"Cache miss for key: {cache_key}")
                return None

            value = row[0]  # Only value is selected now
            
            logger.debug(f"Cache hit for key: {cache_key}")
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                logger.warning(
                    f"Cache data for key {cache_key} is not valid JSON. Returning raw string."
                )
                return value
    except Exception as e:
        logger.error(f"SQLite read error for key {cache_key} ({type(e).__name__}): {e}")
        raise


async def _normalize_and_store_exchanges(
    db: aiosqlite.Connection, cache_key: str, data: Any
):
    """Normalizes and stores exchange data if present in the expected format."""
    if not isinstance(data, dict) or "cute_exchanges" not in data:
        logger.debug(
            f"Data for cache_key '{cache_key}' is not in the expected format for normalization (missing 'cute_exchanges')."
        )
        return

    list_of_exchanges = data["cute_exchanges"]
    if not isinstance(list_of_exchanges, list):
        logger.warning(
            f"'cute_exchanges' for cache_key '{cache_key}' is not a list. Skipping normalization."
        )
        return

    # First, delete any old normalized data for this cache_key
    # This cascades to messages_normalized.
    await db.execute("DELETE FROM exchanges WHERE cache_key = ?", (cache_key,))
    logger.debug(f"Cleared previous normalized exchanges for cache_key: {cache_key}")

    for exchange_idx, current_exchange_list in enumerate(list_of_exchanges):
        if not isinstance(current_exchange_list, list):
            logger.warning(
                f"Item at index {exchange_idx} in 'cute_exchanges' for cache_key '{cache_key}' is not a list. Skipping this exchange."
            )
            continue

        cursor = await db.execute(
            "INSERT INTO exchanges (cache_key, exchange_index) VALUES (?, ?)",
            (cache_key, exchange_idx),
        )
        exchange_id = cursor.lastrowid
        logger.debug(
            f"Inserted exchange for cache_key '{cache_key}', index {exchange_idx}, new exchange_id: {exchange_id}"
        )

        for message_idx, message_data in enumerate(current_exchange_list):
            if not isinstance(message_data, dict):
                logger.warning(
                    f"Message data at index {message_idx} in exchange {exchange_idx} for cache_key '{cache_key}' is not a dict. Skipping."
                )
                continue

            await db.execute(
                """INSERT INTO messages_normalized 
                   (exchange_id, message_index_in_exchange, date, time, person, quote) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    exchange_id,
                    message_idx,
                    message_data.get("date"),
                    message_data.get("time"),
                    message_data.get("person"),
                    message_data.get("quote"),
                ),
            )
    logger.info(
        f"Successfully normalized and stored exchanges for cache_key: {cache_key}"
    )


async def write_cache(
    cache_key: str,
    result: Any,  # This is the Python object, not the JSON string
    calling_context: str | None = None,
) -> None:
    """Writes data to the SQLite cache. Stores raw JSON and also normalizes if structure matches.
    If calling_context matches a specific value, updates the indexed_keys table.
    Data persists indefinitely (no TTL).
    Uses explicit BEGIN/COMMIT/ROLLBACK for transaction control.
    """
    await _ensure_db_initialized()

    db_conn = None  # Define db_conn here to ensure it's available in finally
    try:
        data_to_store_json = json.dumps(result, ensure_ascii=False)

        db_conn = await aiosqlite.connect(SQLITE_DB_PATH)
        await db_conn.execute("PRAGMA foreign_keys = ON;")
        await db_conn.execute("BEGIN")  # Explicitly start transaction

        # 1. Store the raw JSON (no expires_at)
        await db_conn.execute(
            "INSERT OR REPLACE INTO cache_data (key, value) VALUES (?, ?)",
            (cache_key, data_to_store_json),
        )
        logger.debug(f"Wrote raw JSON to cache_data for key: {cache_key}")

        # 2. Normalize and store structured data
        await _normalize_and_store_exchanges(db_conn, cache_key, result)

        # 3. Update index if context matches
        if calling_context == "process_whatsapp_messages::process_chunk_llm":
            logger.info(
                f"Calling context match: '{calling_context}'. Updating indexed_keys for {cache_key}."
            )
            await _add_to_indexed_keys(db_conn, cache_key)

        await db_conn.commit()  # Commit if all operations succeeded
        logger.debug(
            f"Cache entry for key: {cache_key} (no TTL) processed and committed."
        )

    except TypeError as e:  # For json.dumps error
        if db_conn:  # Check if connection was established before trying to rollback
            try:
                await db_conn.rollback()
                logger.error(
                    f"Rolled back transaction for key {cache_key} due to TypeError."
                )
            except Exception as rb_exc:
                logger.error(
                    f"Exception during rollback for key {cache_key} after TypeError: {rb_exc}"
                )
        logger.error(f"JSON serialization error for key {cache_key}: {e}")
        raise
    except Exception as e:
        if db_conn:  # Check if connection was established
            try:
                await db_conn.rollback()
                logger.error(
                    f"Rolled back transaction for key {cache_key} due to Exception."
                )
            except Exception as rb_exc:
                logger.error(
                    f"Exception during rollback for key {cache_key} after Exception: {rb_exc}"
                )
        logger.error(
            f"SQLite write/normalization error for key {cache_key} ({type(e).__name__}): {e}"
        )
        raise
    finally:
        if db_conn:
            await db_conn.close()
            logger.debug(f"Closed SQLite connection for cache_key: {cache_key}")


# Example of how to get all indexed keys (if needed)
async def get_all_indexed_keys() -> list[str]:
    """Retrieves all keys from the indexed_keys table."""
    await _ensure_db_initialized()
    keys = []
    try:
        async with aiosqlite.connect(SQLITE_DB_PATH) as db:
            async with db.execute("SELECT key FROM indexed_keys") as cursor:
                async for row in cursor:
                    keys.append(row[0])
        return keys
    except Exception as e:
        logger.error(
            f"Failed to retrieve keys from indexed_keys ({type(e).__name__}): {e}"
        )
        return []


# --- Example functions to query normalized data (illustrative) ---


async def get_normalized_messages_for_cache_key(cache_key_to_find: str) -> list[dict]:
    """Retrieves all normalized messages associated with a given cache_key."""
    await _ensure_db_initialized()
    messages = []
    try:
        async with aiosqlite.connect(SQLITE_DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            sql = """
            SELECT m.date, m.time, m.person, m.quote, e.exchange_index
            FROM messages_normalized m
            JOIN exchanges e ON m.exchange_id = e.exchange_id
            WHERE e.cache_key = ?
            ORDER BY e.exchange_index, m.message_index_in_exchange;
            """
            async with db.execute(sql, (cache_key_to_find,)) as cursor:
                async for row in cursor:
                    messages.append(
                        dict(zip([col[0] for col in cursor.description], row))
                    )
        logger.info(
            f"Retrieved {len(messages)} normalized messages for cache_key '{cache_key_to_find}'."
        )
        return messages
    except Exception as e:
        logger.error(
            f"Error retrieving normalized messages for cache_key '{cache_key_to_find}': {e}"
        )
        return []


async def search_normalized_messages_by_person(person_to_find: str) -> list[dict]:
    """Searches normalized messages by person across all cache keys."""
    await _ensure_db_initialized()
    messages = []
    try:
        async with aiosqlite.connect(SQLITE_DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON;")
            sql = """
            SELECT m.date, m.time, m.person, m.quote, e.cache_key, e.exchange_index
            FROM messages_normalized m
            JOIN exchanges e ON m.exchange_id = e.exchange_id
            WHERE m.person = ?
            ORDER BY e.cache_key, e.exchange_index, m.message_index_in_exchange;
            """
            async with db.execute(sql, (person_to_find,)) as cursor:
                async for row in cursor:
                    messages.append(
                        dict(zip([col[0] for col in cursor.description], row))
                    )
        logger.info(
            f"Found {len(messages)} normalized messages for person '{person_to_find}'."
        )
        return messages
    except Exception as e:
        logger.error(
            f"Error searching normalized messages by person '{person_to_find}': {e}"
        )
        return []


async def get_all_exchanges_with_first_message(
    page: int = 1,
    page_size: int = 20,
    sort_by_first_message_date: Optional[str] = "asc",  # "asc" or "desc"
) -> Dict[str, Any]:  # Returning a dict with pagination info and results
    """Fetches a paginated and sorted list of all exchanges,
    each with its ID, cache_key, exchange_index, and its first message (if any)."""
    await _ensure_db_initialized()

    offset = (page - 1) * page_size

    results_list: List[Dict[str, Any]] = []

    # Base SQL to get each exchange and its first message details along with a sortable datetime string
    base_sql = """
    SELECT 
        e.exchange_id, 
        e.cache_key, 
        e.exchange_index,
        fm.message_id AS first_message_id,
        fm.date AS first_message_date, 
        fm.time AS first_message_time, 
        fm.person AS first_message_person, 
        fm.quote AS first_message_quote,
        CASE
            WHEN fm.date IS NOT NULL AND fm.time IS NOT NULL THEN
                ('20' || substr(fm.date, 7, 2) || '-' || substr(fm.date, 4, 2) || '-' || substr(fm.date, 1, 2) || 'T' || fm.time)
            ELSE NULL
        END as sortable_datetime_str
    FROM exchanges e
    LEFT JOIN messages_normalized fm ON e.exchange_id = fm.exchange_id AND fm.message_index_in_exchange = 0
    """

    count_sql = "SELECT COUNT(DISTINCT e.exchange_id) FROM exchanges e"

    order_clause = ""
    if sort_by_first_message_date:
        direction = "ASC" if sort_by_first_message_date.lower() == "asc" else "DESC"
        # Handle NULLs: SQLite by default puts NULLs first for ASC, last for DESC.
        # To make chronological (older first for asc), NULLs should effectively be very late.
        # For ASC (older first): NULLS LAST
        # For DESC (newer first): NULLS FIRST (or keep default as NULLs would be considered "less than" any date)
        # Let's use explicit NULLS LAST for ASC and NULLS FIRST for DESC for clarity.
        if direction == "ASC":
            order_clause = (
                f"ORDER BY sortable_datetime_str ASC NULLS LAST, e.exchange_id ASC"
            )
        else:  # DESC
            order_clause = (
                f"ORDER BY sortable_datetime_str DESC NULLS FIRST, e.exchange_id DESC"
            )
    else:  # Default ordering if no sort specified
        order_clause = "ORDER BY e.exchange_id ASC"

    query_sql = f"{base_sql} {order_clause} LIMIT ? OFFSET ?"

    total_exchanges = 0

    try:
        async with aiosqlite.connect(SQLITE_DB_PATH) as db:
            await db.execute("PRAGMA foreign_keys = ON;")

            # Get total count
            async with db.execute(count_sql) as cursor:
                count_row = await cursor.fetchone()
                if count_row:
                    total_exchanges = count_row[0]

            async with db.execute(query_sql, (page_size, offset)) as cursor:
                async for row in cursor:
                    (
                        exchange_id,
                        cache_key,
                        exchange_index,
                        first_msg_id,
                        msg_date,
                        msg_time,
                        msg_person,
                        msg_quote,
                        _,  # sortable_datetime_str - not directly needed in output dict
                    ) = row

                    first_message_data = None
                    if msg_date is not None:  # Indicates a first message was found
                        first_message_data = {
                            "message_id": first_msg_id,
                            "date": msg_date,
                            "time": msg_time,
                            "person": msg_person,
                            "quote": msg_quote,
                        }
                    results_list.append(
                        {
                            "id": exchange_id,
                            "cache_key": cache_key,
                            "exchange_index": exchange_index,
                            "first_message": first_message_data,
                        }
                    )

        has_more = (page * page_size) < total_exchanges
        response_data = {
            "items": results_list,
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalItems": total_exchanges,
                "totalPages": (
                    (total_exchanges + page_size - 1) // page_size
                    if page_size > 0
                    else 0
                ),
                "hasMore": has_more,
            },
        }
        return response_data
    except Exception as e:
        logger.error(
            f"Error retrieving paginated/sorted exchanges with first message: {e}",
            exc_info=True,
        )
        return {
            "items": [],
            "pagination": {
                "currentPage": page,
                "pageSize": page_size,
                "totalItems": 0,
                "totalPages": 0,
                "hasMore": False,
            },
        }  # Return empty structure on error


async def get_exchange_by_id_with_messages(
    exchange_id_to_find: int,
) -> Optional[Dict[str, Any]]:
    """Retrieves a specific exchange by its global ID, including all its messages."""
    await _ensure_db_initialized()
    try:
        async with aiosqlite.connect(SQLITE_DB_PATH) as db:
            async with db.execute(
                """
                SELECT e.exchange_id, e.cache_key, e.exchange_index,
                       m.message_id, m.message_index_in_exchange, m.date, m.time, m.person, m.quote
                FROM exchanges e
                LEFT JOIN messages_normalized m ON e.exchange_id = m.exchange_id
                WHERE e.exchange_id = ?
                ORDER BY m.message_index_in_exchange ASC
                """,
                (exchange_id_to_find,),
            ) as cursor:
                rows = await cursor.fetchall()

            if not rows:
                logger.warning(
                    f"No exchange found with ID: {exchange_id_to_find}"
                )
                return None

            # Process rows to structure the exchange with its messages
            # All rows will have the same exchange_id, cache_key, exchange_index
            # because we're selecting a specific exchange_id.
            exchange_data = {
                "id": rows[0][0],  # exchange_id
                "cache_key": rows[0][1],
                "exchange_index": rows[0][2],
                "messages": [],
            }

            for row in rows:
                # Check if there's message data (due to LEFT JOIN, message fields can be NULL if no messages)
                if row[3] is not None:  # row[3] is message_id
                    message = {
                        "message_id": row[3],
                        "message_index_in_exchange": row[4],
                        "date": row[5],
                        "time": row[6],
                        "person": row[7],
                        "quote": row[8],
                    }
                    exchange_data["messages"].append(message)
            
            logger.info(f"Retrieved exchange ID {exchange_id_to_find} with {len(exchange_data['messages'])} messages.")
            return exchange_data

    except Exception as e:
        logger.error(
            f"SQLite error retrieving exchange ID {exchange_id_to_find} ({type(e).__name__}): {e}",
            exc_info=True
        )
        raise # Re-raise after logging


async def delete_exchange_by_id(exchange_id: int) -> bool:
    """Deletes an exchange and its associated messages from the database by its global ID.
    
    Returns:
        bool: True if the exchange was found and deleted, False otherwise.
    """
    await _ensure_db_initialized()
    db_conn = None 
    try:
        db_conn = await aiosqlite.connect(SQLITE_DB_PATH)
        await db_conn.execute("PRAGMA foreign_keys = ON;")
        
        await db_conn.execute("BEGIN")

        cursor = await db_conn.execute(
            "DELETE FROM exchanges WHERE exchange_id = ?", (exchange_id,)
        )
        
        if cursor.rowcount > 0:
            await db_conn.commit()
            logger.info(
                f"Successfully deleted exchange with ID: {exchange_id} and its associated messages (cascaded)."
            )
            return True
        else:
            await db_conn.rollback() 
            logger.warning(
                f"Attempted to delete exchange with ID: {exchange_id}, but it was not found."
            )
            return False
            
    except Exception as e:
        if db_conn:
            try:
                await db_conn.rollback()
            except Exception as rb_exc:
                logger.error(f"Exception during rollback for exchange ID {exchange_id} after initial error: {rb_exc}")
        logger.error(
            f"SQLite error deleting exchange ID {exchange_id} ({type(e).__name__}): {e}",
            exc_info=True
        )
        return False
    finally:
        if db_conn:
            await db_conn.close()


async def clear_messages_from_exchange(exchange_id: int) -> bool:
    """Clears all messages associated with a given exchange_id from the messages_normalized table.
    
    The exchange entry itself in the 'exchanges' table remains.

    Returns:
        bool: True if the exchange was found and its messages cleared (or if it had no messages),
              False if the exchange_id itself was not found.
    """
    await _ensure_db_initialized()
    db_conn = None
    try:
        db_conn = await aiosqlite.connect(SQLITE_DB_PATH)
        await db_conn.execute("PRAGMA foreign_keys = ON;") # Good practice, though not strictly needed for this op if not cascading
        
        await db_conn.execute("BEGIN")

        # First, check if the exchange_id exists
        async with db_conn.execute("SELECT 1 FROM exchanges WHERE exchange_id = ?", (exchange_id,)) as cursor:
            if await cursor.fetchone() is None:
                logger.warning(f"Attempted to clear messages for non-existent exchange ID: {exchange_id}")
                await db_conn.rollback() # Nothing to do, rollback any implicit transaction start
                return False

        # If exchange exists, delete its messages
        # No need to check cursor.rowcount here, as it's okay if an exchange has no messages (rowcount would be 0)
        await db_conn.execute(
            "DELETE FROM messages_normalized WHERE exchange_id = ?", (exchange_id,)
        )
        
        await db_conn.commit()
        logger.info(f"Successfully cleared messages for exchange ID: {exchange_id}.")
        return True
            
    except Exception as e:
        if db_conn:
            try:
                await db_conn.rollback()
            except Exception as rb_exc:
                logger.error(f"Exception during rollback for clearing messages for exchange ID {exchange_id}: {rb_exc}")
        logger.error(
            f"SQLite error clearing messages for exchange ID {exchange_id} ({type(e).__name__}): {e}",
            exc_info=True
        )
        return False # Indicate failure
    finally:
        if db_conn:
            await db_conn.close()


async def delete_messages_by_ids(message_ids: List[int]) -> int:
    """Deletes specific messages from the messages_normalized table based on a list of message_ids.

    Args:
        message_ids (List[int]): A list of message_id integers to delete.

    Returns:
        int: The number of messages actually deleted.
    """
    if not message_ids: # If the list is empty, no action is needed.
        return 0
        
    await _ensure_db_initialized()
    db_conn = None
    try:
        db_conn = await aiosqlite.connect(SQLITE_DB_PATH)
        # PRAGMA foreign_keys = ON; is not strictly necessary for deleting from messages_normalized directly,
        # as it doesn't cascade further down from here based on current schema for this operation.
        
        await db_conn.execute("BEGIN")

        # Create placeholders for the IN clause
        placeholders = ",".join("?" for _ in message_ids)
        sql = f"DELETE FROM messages_normalized WHERE message_id IN ({placeholders})"
        
        cursor = await db_conn.execute(sql, tuple(message_ids))
        deleted_count = cursor.rowcount
        
        await db_conn.commit()
        
        if deleted_count > 0:
            logger.info(f"Successfully deleted {deleted_count} messages with IDs: {message_ids}")
        else:
            logger.warning(f"Attempted to delete messages with IDs: {message_ids}, but none were found or matched.")
            
        return deleted_count
            
    except Exception as e:
        if db_conn:
            try:
                await db_conn.rollback()
            except Exception as rb_exc:
                logger.error(f"Exception during rollback for deleting messages by IDs {message_ids}: {rb_exc}")
        logger.error(
            f"SQLite error deleting messages by IDs {message_ids} ({type(e).__name__}): {e}",
            exc_info=True
        )
        return 0 # Indicate failure or no messages deleted due to error
    finally:
        if db_conn:
            await db_conn.close()


async def merge_exchanges_by_ids(exchange_ids: List[int]) -> Optional[int]:
    """Merges multiple exchanges into a single target exchange (the one with the smallest ID).
    
    Messages from source exchanges are moved to the target exchange, and then
    the source exchanges are deleted. Messages in the target exchange are re-indexed
    chronologically.

    Args:
        exchange_ids (List[int]): A list of at least two exchange_ids to merge.

    Returns:
        Optional[int]: The exchange_id of the target exchange if successful, None otherwise.
    """
    if not exchange_ids or len(exchange_ids) < 2:
        logger.error("Merge operation requires at least two exchange IDs.")
        return None

    await _ensure_db_initialized()
    db_conn = None
    try:
        db_conn = await aiosqlite.connect(SQLITE_DB_PATH)
        await db_conn.execute("PRAGMA foreign_keys = ON;")
        await db_conn.execute("BEGIN")

        # Validate all exchange_ids exist
        placeholders = ",".join("?" for _ in exchange_ids)
        async with db_conn.execute(f"SELECT exchange_id FROM exchanges WHERE exchange_id IN ({placeholders})", tuple(exchange_ids)) as cursor:
            found_ids = {row[0] for row in await cursor.fetchall()}
        
        if len(found_ids) != len(set(exchange_ids)):
            logger.error(f"Merge failed: Not all provided exchange IDs found. Provided: {exchange_ids}, Found: {found_ids}")
            await db_conn.rollback()
            return None

        target_exchange_id = min(exchange_ids)
        source_exchange_ids = [eid for eid in exchange_ids if eid != target_exchange_id]

        if not source_exchange_ids: # Should not happen if len(exchange_ids) >= 2
            logger.error("Merge logic error: No source exchange IDs identified.")
            await db_conn.rollback()
            return None

        # Move messages from source exchanges to the target exchange
        source_placeholders = ",".join("?" for _ in source_exchange_ids)
        await db_conn.execute(
            f"UPDATE messages_normalized SET exchange_id = ? WHERE exchange_id IN ({source_placeholders})",
            (target_exchange_id, *source_exchange_ids)
        )
        logger.info(f"Moved messages from source exchanges {source_exchange_ids} to target {target_exchange_id}.")

        # Delete the source exchanges (their messages are now moved)
        # This won't cascade-delete the moved messages due to the previous UPDATE.
        await db_conn.execute(
            f"DELETE FROM exchanges WHERE exchange_id IN ({source_placeholders})",
            tuple(source_exchange_ids)
        )
        logger.info(f"Deleted source exchanges: {source_exchange_ids}.")

        # Re-index messages for the target exchange
        # 1. Fetch all messages for the target exchange
        messages_to_reindex = []
        async with db_conn.execute(
            "SELECT message_id, date, time FROM messages_normalized WHERE exchange_id = ?", (target_exchange_id,)
        ) as cursor:
            async for row in cursor:
                messages_to_reindex.append({"message_id": row[0], "date": row[1], "time": row[2]})
        
        # 2. Sort messages chronologically (handle potential None dates/times or malformed data carefully)
        def get_sort_key(message):
            try:
                # Basic date parsing: DD.MM.YY and time HH:MM:SS or HH:MM
                # This needs to be robust or match the exact format stored.
                # Assuming date is like 'DD.MM.YY' and time 'HH:MM' or 'HH:MM:SS'
                if message['date'] and message['time']:
                    day, month, year_short = map(int, message['date'].split('.'))
                    year = 2000 + year_short # Assuming 21st century
                    time_parts = list(map(int, message['time'].split(':')))
                    hour = time_parts[0]
                    minute = time_parts[1]
                    second = time_parts[2] if len(time_parts) > 2 else 0
                    return (year, month, day, hour, minute, second)
            except Exception:
                # Fallback for unparseable date/time - sort these last or first based on policy
                return (float('inf'),) # Sorts unparseable ones last
            return (float('inf'),) # Default if date or time is None
            
        messages_to_reindex.sort(key=get_sort_key)

        # 3. Update message_index_in_exchange
        for new_index, message in enumerate(messages_to_reindex):
            await db_conn.execute(
                "UPDATE messages_normalized SET message_index_in_exchange = ? WHERE message_id = ?",
                (new_index, message["message_id"])
            )
        logger.info(f"Re-indexed {len(messages_to_reindex)} messages for target exchange ID: {target_exchange_id}.")

        await db_conn.commit()
        logger.info(f"Successfully merged exchanges {exchange_ids} into target {target_exchange_id}.")
        return target_exchange_id

    except Exception as e:
        if db_conn:
            try:
                await db_conn.rollback()
            except Exception as rb_exc:
                logger.error(f"Exception during rollback for merging exchanges {exchange_ids}: {rb_exc}")
        logger.error(
            f"SQLite error merging exchanges {exchange_ids} ({type(e).__name__}): {e}",
            exc_info=True
        )
        return None
    finally:
        if db_conn:
            await db_conn.close()

# Further development notes for cache_utils.py:
# - Consider how to handle deletion of entries from `cache_data` if all exchanges
#   referencing a `cache_key` are deleted. This might involve checking reference counts.
# - For other modification operations (clear messages, merge), similar functions
#   will be needed here to interact with the SQLite DB.
