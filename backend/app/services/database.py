"""
MongoDB and Qdrant
"""

import os

from beanie import init_beanie
from bunnet import init_bunnet
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from app.models.chat_models import Conversation, Message, User
from app.models.status_models import SyncStatusBeanie, SyncStatusBunnet

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "chat_db")
QDRANT_URI = os.getenv("QDRANT_URI")
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "documents")


async def init_mongodb_beanie():
    print(f"init_mongodb_beanie: {MONGO_URI=}")
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    await init_beanie(
        database=db, document_models=[User, Conversation, Message, SyncStatusBeanie]
    )
    return client, db


def init_mongodb_bunnet():
    print(f"init_mongodb_bunnet: {MONGO_URI=}")
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    init_bunnet(database=db, document_models=[SyncStatusBunnet])
    return client, db


def init_qdrant():
    print(f"{QDRANT_URI=}")
    client = QdrantClient(url=QDRANT_URI)
    if client.collection_exists(QDRANT_COLLECTION_NAME):
        print(f"Qdrant collection {QDRANT_COLLECTION_NAME} already registered.")
    else:
        client.create_collection(
            collection_name=QDRANT_COLLECTION_NAME,
            # NOTE: vector size 385 to match the embedding model "sentence-transformers/all-MiniLM-L6-v2"
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
        print(f"Registered new Qdrant collection {QDRANT_COLLECTION_NAME}.")
    return
