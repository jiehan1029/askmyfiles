"""
Define schema for the MongoDB collection that holds user chat histories.
"""
from beanie import Document, Link
from datetime import UTC, datetime
from typing import Optional


class User(Document):
    username: str
    timezone: str = "US/Pacific"
    created_at: datetime = datetime.now(tz=UTC)

    class Settings:
        name = "users"

    class Config:
        arbitrary_types_allowed = True  # This allows Pydantic to handle ObjectId


class Conversation(Document):
    user: Link[User]
    created_at: datetime = datetime.now(tz=UTC)

    class Settings:
        name = "conversations"

    class Config:
        arbitrary_types_allowed = True


class Message(Document):
    """
    Save user query and bot response in the same document to avoid duplicated storage of queries.
    """
    conversation: Link[Conversation]
    user: Link[User]
    query: str | None = None   # user's question
    response: str | None = None  # bot's response
    model: Optional[str] = None  # the model used for response generation
    finish_reason: Optional[str | int] = None  # why the generation stopped
    documents: Optional[list[dict]] = None  # relevant documents by retriever
    query_created_at: datetime | None = None
    response_created_at: datetime | None = None

    class Settings:
        name = "messages"

    class Config:
        arbitrary_types_allowed = True
