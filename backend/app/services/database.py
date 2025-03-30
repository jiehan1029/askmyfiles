import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.chat_models import User, Conversation, Message


MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "chat_db")


async def init_mongodb() -> tuple:
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    await init_beanie(database=db, document_models=[User, Conversation, Message])
    return client, db
