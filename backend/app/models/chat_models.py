"""
Define schema for the MongoDB collection that holds user chat histories.
"""
from beanie import Document, Link
from datetime import UTC, datetime
from typing import Optional


class User(Document):
    """
    todo: pause: not supporting multi user now
    """
    username: str
    locale: str = "en-US"  # IETF BCP 47 locale tags for frontend compatibility
    timezone: str = "America/Los_Angeles"  # BCP 47 language tags (FE compatible)
    llm_provider: str = "gemini"  # atm support "gemini", "huggingFace" and "ollama"
    llm_api_token: Optional[str] = None
    llm_model: str = "gemini-2.0-flash"  # default
    created_at: datetime = datetime.now(tz=UTC)

    class Settings:
        name = "users"

    class Config:
        arbitrary_types_allowed = True  # This allows Pydantic to handle ObjectId

    @classmethod
    def map_default_model(cls, provider: str) -> str:
        if provider == "gemini":
            return "gemini-2.0-flash"
        if provider == "huggingFace":
            return "HuggingFaceH4/zephyr-7b-beta"
        if provider == "ollama":
            return "mistral:7b"
        return None


class Conversation(Document):
    user: Optional[Link[User]] | None = None
    created_at: datetime = datetime.now(tz=UTC)
    summary: Optional[str] | None = None

    class Settings:
        name = "conversations"

    class Config:
        arbitrary_types_allowed = True


class Message(Document):
    """
    Save user query and bot response in the same document to avoid duplicated storage of queries.
    """
    conversation: Link[Conversation]
    user: Optional[Link[User]] | None = None
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
