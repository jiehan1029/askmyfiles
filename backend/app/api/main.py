import os
import logging
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
from app.services.document_stores import IN_MEMORY_DOCUMENT_STORE
from app.services.pipelines import IN_MEMORY_PREPROCESSING_PIPELINE, IN_MEMORY_RAG_PIPELINE
from app.core.configs import IN_MEMORY_DOCUMENT_STORE_BACKUP_DIR
from datetime import UTC, datetime

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper()
)


app = FastAPI()

origins = [
    "http://localhost:80",
    "http://localhost:3000"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/health")
def health_check(request: Request):
    return {"health": "ok"}


class InsertDocumentsRequest(BaseModel):
    directory: str
    local_backup: bool = False
    local_backup_name: str | None = None


@app.post("/insert_documents")
async def insert_documents_into_store(request: InsertDocumentsRequest):
    output_dir = Path(request.directory).expanduser()
    logger.info(f"{output_dir=}")

    IN_MEMORY_PREPROCESSING_PIPELINE.run({"file_type_router": {"sources": list(output_dir.glob("**/*"))}})

    # save document store to local backup file
    backup_dir = None
    if request.local_backup:
        if request.local_backup_name:
            backup_dir = Path(IN_MEMORY_DOCUMENT_STORE_BACKUP_DIR + f"/{request.local_backup_name}.json").expanduser()
        else:
            backup_dir = Path(IN_MEMORY_DOCUMENT_STORE_BACKUP_DIR + f"/my_document_store_{int(datetime.now(tz=UTC).timestamp())}.json").expanduser()
        IN_MEMORY_DOCUMENT_STORE.save_to_disk(str(backup_dir))
        logger.info(f'Saved to backup directory: {backup_dir}')

    return {"inserted": IN_MEMORY_DOCUMENT_STORE.count_documents(), "local_backup": request.local_backup, "backup_dir": backup_dir}


class RestoreDocumentsRequest(BaseModel):
    local_backup_name: str


@app.post("/restore_documents")
async def restore_documents_from_backup(request: RestoreDocumentsRequest):
    # TODO: backup files with embeddings are not compatible with in memory document store!!
    backup_dir = Path(IN_MEMORY_DOCUMENT_STORE_BACKUP_DIR + f"/{request.local_backup_name}.json").expanduser()

    if backup_dir.exists():
        print("File exists")
    else:
        print("File does not exist")
        return {"error": "File does not exist."}

    # from haystack.document_stores.in_memory import InMemoryDocumentStore
    # new_store = InMemoryDocumentStore()
    before_count = IN_MEMORY_DOCUMENT_STORE.count_documents()
    print(f'before restoration, store has {before_count} documents. will restore from {backup_dir}')

    IN_MEMORY_DOCUMENT_STORE.load_from_disk(str(backup_dir))
    after_count = IN_MEMORY_DOCUMENT_STORE.count_documents()
    print(f'after restoration, store has {after_count} documents.')

    print(f'*** the other documentstore? {IN_MEMORY_DOCUMENT_STORE.count_documents()}')
    return {
        "restored": IN_MEMORY_DOCUMENT_STORE.count_documents(),
        "from_backup": backup_dir
    }


class SearchRequest(BaseModel):
    question: str


# Endpoint to accept search requests
@app.post("/search")
async def search_documents(request: SearchRequest):
    question = request.question
    answer_raw = IN_MEMORY_RAG_PIPELINE.run(
        {
            "text_embedder": {"text": question},
            "prompt_builder": {"question": question},
            "answer_builder": {"query": question}
        })
    logger.debug(f"{question=}, {answer_raw=}")
    # answer = answer_raw["answer_builder"]["answers"][0].data
    return {"answer": answer_raw}
