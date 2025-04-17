"""
Haystack document stores
"""

import os
from dotenv import load_dotenv
from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore


if os.getenv("APP_ENV", "development").lower() == "development":
    print(f'document_stores: Loading dotenv for {os.getenv("APP_ENV", "development")} APP_ENV.')
    load_dotenv()


DOCUMENT_STORE_NAME = os.getenv("DOCUMENT_STORE_NAME", "qdrant")
QDRANT_URI_HOST = os.getenv("QDRANT_URI_HOST", "http://host.docker.internal")
QDRANT_URI_PORT = int(os.getenv("QDRANT_URI_PORT", 6333))

###
# Global document store instances ready to use
###
IN_MEMORY_DOCUMENT_STORE = InMemoryDocumentStore()

QDRANT_DOCUMENT_STORE = QdrantDocumentStore(
    url=QDRANT_URI_HOST,
    port=QDRANT_URI_PORT,
    index="doc_collection",  # collection name
    embedding_dim=384,  # based on the embedding model, sentence-transformers/all-MiniLM-L6-v2 has 384 vector size
    recreate_index=False,  # make sure it's false to persist data
    return_embedding=True,
    wait_result_from_api=True,
)


###
# Default selection based on config
###
DEFAULT_DOCUMENT_STORE = QDRANT_DOCUMENT_STORE if DOCUMENT_STORE_NAME == "qdrant" else IN_MEMORY_DOCUMENT_STORE
