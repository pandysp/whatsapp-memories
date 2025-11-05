from fastapi import APIRouter, HTTPException, status, Query, Body
from typing import List, Optional  # Added Optional for ExchangeSummaryResponse
import logging

from ..utils import cache_utils
from ..api_models import (
    MessageResponse,  # Still needed for constructing ExchangeDetailResponse
    ExchangeDetailResponse,  # This is our primary response model now
    ExchangeSummaryResponse,  # Added for the list view
    PaginatedExchangeSummaryResponse,  # Added for paginated list view
    DeleteMessagesRequest,  # Added DeleteMessagesRequest
    MergeExchangesRequest,  # Added MergeExchangesRequest
    # CacheKeyExchangesResponse, SearchResultItem, SearchMessagesResponse removed
)

# Router for /exchanges specific endpoints
exchanges_router = APIRouter(
    prefix="/exchanges",  # Prefixing the router itself for /api/exchanges
    tags=["Exchanges"],  # Tagging for API docs
)

# Router for /messages specific endpoints (e.g., deleting messages by ID)
# This is separate because deleting messages by a list of IDs isn't tied to a single exchange context in the URL path.
messages_router = APIRouter(
    prefix="/messages",
    tags=["Messages"],
)

logger = logging.getLogger(__name__)


@exchanges_router.get("/", response_model=PaginatedExchangeSummaryResponse)
async def list_all_exchanges(
    page: int = Query(1, ge=1, description="Page number to retrieve"),
    page_size: int = Query(
        20, ge=1, le=100, description="Number of exchanges per page"
    ),
    sort_by_first_message_date: Optional[str] = Query(
        "asc",
        description="Sort order: 'asc' for ascending, 'desc' for descending by first message date. Defaults to ascending.",
    ),
):
    """
    Retrieve a paginated and sorted list of all exchanges,
    each with their ID, cache_key, exchange_index, and first message (for preview).
    """
    try:
        if sort_by_first_message_date and sort_by_first_message_date.lower() not in [
            "asc",
            "desc",
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid sort_by_first_message_date value. Must be 'asc' or 'desc'.",
            )

        # cache_utils.get_all_exchanges_with_first_message now returns a dict with "items" and "pagination"
        paginated_data = await cache_utils.get_all_exchanges_with_first_message(
            page=page,
            page_size=page_size,
            sort_by_first_message_date=sort_by_first_message_date,
        )

        # Map the "items" part to ExchangeSummaryResponse objects if needed,
        # though cache_utils should already return dicts compatible with ExchangeSummaryResponse fields.
        # Pydantic will handle validation and conversion for the response_model.

        # Ensure the structure from cache_utils matches PaginatedExchangeSummaryResponse
        # The utility function was designed to return a dict like:
        # { "items": [...], "pagination": {...} }
        # which Pydantic can directly use to populate PaginatedExchangeSummaryResponse.

        return paginated_data  # FastAPI will validate this against PaginatedExchangeSummaryResponse

    except (
        HTTPException
    ):  # Re-raise HTTPExceptions directly to preserve status code and detail
        raise
    except Exception as e:
        logger.error(
            f"Error retrieving all exchanges (paginated/summary): {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving exchange summaries.",
        )


@exchanges_router.get("/{exchange_id}", response_model=ExchangeDetailResponse)
async def get_exchange_detail(exchange_id: int):
    """
    Retrieve a single exchange by its unique ID, with all its embedded messages.
    """
    try:
        # This function returns a dict with "id" and "messages" or None
        exchange_data = await cache_utils.get_exchange_by_id_with_messages(exchange_id)

        if exchange_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exchange with ID {exchange_id} not found.",
            )

        messages_response = [
            MessageResponse(**msg_data)
            for msg_data in exchange_data.get("messages", [])
        ]

        return ExchangeDetailResponse(
            id=exchange_data["id"], messages=messages_response
        )

    except HTTPException:  # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(f"Error retrieving exchange ID {exchange_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while retrieving exchange ID {exchange_id}.",
        )


@exchanges_router.delete("/{exchange_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exchange(exchange_id: int):
    """
    Delete an exchange by its unique ID. 
    This will also delete all associated messages due to cascading deletes in the database.
    """
    try:
        deleted = await cache_utils.delete_exchange_by_id(exchange_id)
        if not deleted:
            logger.warning(
                f"Attempt to delete non-existent exchange ID: {exchange_id} from API."
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exchange with ID {exchange_id} not found.",
            )
        # If deleted, a 204 No Content response is automatically sent by FastAPI
        # due to the status_code in the decorator and no return value.
        logger.info(f"Successfully processed API request to delete exchange ID: {exchange_id}")
    except HTTPException: # Re-raise HTTPExceptions directly
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error deleting exchange ID {exchange_id} via API: {e}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while attempting to delete exchange ID {exchange_id}.",
        )


# Removing the clear_exchange_messages endpoint as it's superseded by delete_exchange
# @exchanges_router.post("/{exchange_id}/clear", status_code=status.HTTP_204_NO_CONTENT)
# async def clear_exchange_messages(exchange_id: int):
#     """
#     Clear all messages from a specific exchange. The exchange itself will remain.
#     """
#     try:
#         success = await cache_utils.clear_messages_from_exchange(exchange_id)
#         if not success:
#             logger.warning(
#                 f"Attempt to clear messages for non-existent exchange ID: {exchange_id} from API."
#             )
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail=f"Exchange with ID {exchange_id} not found, cannot clear messages.",
#             )
#         logger.info(f"Successfully processed API request to clear messages for exchange ID: {exchange_id}")
#         # 204 No Content is returned automatically
#     except HTTPException: # Re-raise HTTPExceptions directly
#         raise
#     except Exception as e:
#         logger.error(
#             f"Unexpected error clearing messages for exchange ID {exchange_id} via API: {e}",
#             exc_info=True,
#         )
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"An unexpected error occurred while attempting to clear messages for exchange ID {exchange_id}.",
#         )


@exchanges_router.post("/merge", response_model=dict) # Returning target_exchange_id or error
async def merge_exchanges_endpoint(request: MergeExchangesRequest = Body(...)):
    """
    Merge multiple exchanges into one. 
    The exchange with the smallest ID in the list becomes the target.
    Messages are moved, and source exchanges are deleted.
    Messages in the target exchange are re-indexed chronologically.
    """
    # Validation for at least two IDs is handled by Pydantic model

    try:
        target_exchange_id = await cache_utils.merge_exchanges_by_ids(request.exchange_ids)
        
        if target_exchange_id is None:
            # More specific error messages would come from logs in cache_utils
            logger.error(f"API call to merge exchanges {request.exchange_ids} failed. See cache_utils logs for details.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, # Or 404 if some IDs not found, or 500 if other internal error
                detail="Failed to merge exchanges. One or more exchange IDs might be invalid, or an internal error occurred."
            )
        
        logger.info(f"Successfully processed API request to merge exchanges {request.exchange_ids} into target {target_exchange_id}.")
        return {"message": "Exchanges merged successfully", "target_exchange_id": target_exchange_id}
        
    except HTTPException: # Re-raise HTTPExceptions from model validation or explicitly raised
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error merging exchanges {request.exchange_ids} via API: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while attempting to merge exchanges.",
        )


# Removed old /exchanges/{cache_key} endpoint
# Removed /messages/search endpoint

# --- Mount endpoints to messages_router --- 
@messages_router.delete("/", response_model=dict) # Returning a dict like {"deleted_count": count}
async def delete_messages_by_id_list(request: DeleteMessagesRequest = Body(...)):
    """
    Delete a list of messages by their unique IDs.
    """
    if not request.message_ids:
        # Or return 200 with deleted_count: 0, depending on desired behavior for empty list
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="message_ids list cannot be empty."
        )
    try:
        deleted_count = await cache_utils.delete_messages_by_ids(request.message_ids)
        
        logger.info(f"API request to delete messages by IDs: {request.message_ids}. Deleted: {deleted_count}.")
        # Even if deleted_count is 0 (none found), it's a successful execution of the request.
        return {"deleted_count": deleted_count}
        
    except Exception as e: # Catch generic exceptions from cache_utils or other issues
        logger.error(
            f"Unexpected error deleting messages by IDs {request.message_ids} via API: {e}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred while attempting to delete messages.",
        )


# Note: The main FastAPI app will need to include both exchanges_router and messages_router.
# For example, in main.py or app.py:
# from .routers import messages
# app.include_router(messages.exchanges_router)
# app.include_router(messages.messages_router)
