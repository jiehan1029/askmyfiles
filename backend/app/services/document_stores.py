from haystack.document_stores.in_memory import InMemoryDocumentStore
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from app.core.configs import QDRANT_DOCUMENT_STORE_STORAGE_DIR, DOCUMENT_STORE_NAME
from pathlib import Path

###
# Global document store instances ready to use
###
IN_MEMORY_DOCUMENT_STORE = InMemoryDocumentStore()

QDRANT_DOCUMENT_STORE = QdrantDocumentStore(
    path=Path(QDRANT_DOCUMENT_STORE_STORAGE_DIR),
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
