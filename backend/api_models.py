from pydantic import BaseModel, field_validator
from typing import List, Optional
from pydantic import validator


class MessageResponse(BaseModel):
    message_id: int
    date: Optional[str] = None
    time: Optional[str] = None
    person: Optional[str] = None
    quote: Optional[str] = None


class ExchangeSummaryResponse(BaseModel):
    id: int  # Represents the exchange_id from the database
    cache_key: str  # The original cache_key (source identifier)
    exchange_index: (
        int  # The index of this exchange within its original cache_key group
    )
    first_message: Optional[MessageResponse] = None


class ExchangeDetailResponse(BaseModel):
    id: int  # Represents the exchange_id from the database
    messages: List[MessageResponse]


class PaginationInfo(BaseModel):
    currentPage: int
    pageSize: int
    totalItems: int
    totalPages: int
    hasMore: bool


class PaginatedExchangeSummaryResponse(BaseModel):
    items: List[ExchangeSummaryResponse]
    pagination: PaginationInfo


class DeleteMessagesRequest(BaseModel):
    message_ids: List[int]


class MergeExchangesRequest(BaseModel):
    exchange_ids: List[int]

    @field_validator('exchange_ids')
    @classmethod
    def check_list_contains_at_least_two_ids(cls, v: List[int]):
        if len(v) < 2:
            raise ValueError('exchange_ids must contain at least two IDs to merge')
        return v


# Removed CacheKeyExchangesResponse, SearchResultItem, and SearchMessagesResponse
# as per the new requirements focusing on /exchanges/ and /exchanges/{id}
