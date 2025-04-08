"""
MongoDB and Qdrant
"""

import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.chat_models import User, Conversation, Message
from app.models.status_models import SyncStatus
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams


MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "chat_db")
QDRANT_URI = os.getenv("QDRANT_URI")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "documents")
QDRANT_VECTOR_SIZE = os.getenv("QDRANT_VECTOR_SIZE", 384)


async def init_mongodb():
    print(f"{MONGO_URI=}")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    await init_beanie(database=db, document_models=[User, Conversation, Message, SyncStatus])
    return client, db


def init_qdrant():
    print(f"{QDRANT_URI=}")
    client = QdrantClient(url=QDRANT_URI)
    if client.collection_exists(QDRANT_COLLECTION_NAME):
        print(f"Qdrant collection {QDRANT_COLLECTION_NAME} already registered.")
    else:
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            vectors_config=VectorParams(size=int(QDRANT_VECTOR_SIZE), distance=Distance.COSINE),
        )
        print(f"Registered new Qdrant collection {QDRANT_COLLECTION_NAME}.")
    return
