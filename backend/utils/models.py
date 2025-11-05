from pydantic import BaseModel, Field


class MessageDetail(BaseModel):
    """Represents the details of a single message line."""

    date: str = Field(..., description="Date of the message (DD.MM.YY)")
    time: str = Field(..., description="Time of the message (HH:MM:SS)")
    person: str = Field(..., description="Name of the person who sent the message")
    quote: str = Field(..., description="The text content of the message")


class CuteMessagesResult(BaseModel):
    """Structure for the result of extracting cute messages from a chat chunk."""

    cute_exchanges: list[list[MessageDetail]] = Field(
        default_factory=list,
        description="A list where each item is a list of MessageDetail objects. Each inner list represents a single cute message or a short cute exchange. Empty list if none found.",
    )
