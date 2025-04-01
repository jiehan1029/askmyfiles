import os
import logging
from dotenv import load_dotenv
from beanie import PydanticObjectId
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
from app.services.document_stores import DEFAULT_DOCUMENT_STORE
from app.services.pipelines import DEFAULT_PREPROCESSING_PIPELINE, DEFAULT_RAG_PIPELINE
from datetime import UTC, datetime
from app.models.chat_models import User, Message, Conversation
from app.services.database import init_mongodb, init_qdrant
from contextlib import asynccontextmanager
from app.api.utils import format_chat_history


if os.getenv("APP_ENV", "development").lower() == "development":
    print(f'Loading dotenv for {os.getenv("APP_ENV", "development")} APP_ENV.')
    load_dotenv()


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper()
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FastAPI app is starting up.")

    await init_mongodb()
    print("Beanie initiated.")

    init_qdrant()
    print("Qdrant initiated.")

    yield
    print("FastAPI app will shut down.")

app = FastAPI(lifespan=lifespan)

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


class CreateUserRequest(BaseModel):
    username: str
    timezone: Optional[str] = "US/Pacific"


@app.post("/users")
async def create_user(request: CreateUserRequest):
    found_user = await User.find({"username": request.username}).first_or_none()
    if found_user:
        raise HTTPException(status_code=400, detail={"error": "Username already exists."})
    user = User(username=request.username, timezone=request.timezone)
    await user.insert()
    return user


@app.get("/info")
async def get_app_info(request: Request):
    return {
        "document_store": os.getenv("DOCUMENT_STORE_NAME"),
        "num_documents": DEFAULT_DOCUMENT_STORE.count_documents()
    }


class InsertDocumentsRequest(BaseModel):
    directory: str


@app.post("/insert_documents")
async def insert_documents_into_store(request: InsertDocumentsRequest):
    output_dir = Path(request.directory).expanduser()
    logger.info(f"{output_dir=}")

    DEFAULT_PREPROCESSING_PIPELINE.run({"file_type_router": {"sources": list(output_dir.glob("**/*"))}})
    return {"inserted": DEFAULT_DOCUMENT_STORE.count_documents()}


class SearchRequest(BaseModel):
    question: str
    user_id: str
    conversation_id: str | None = None


# Endpoint to accept search requests
@app.post("/search")
async def search_documents(request: SearchRequest):
    """
    Generate answers and save chat conversatios.
    """
    user = await User.get(request.user_id)
    conversation = None
    prev_messages = []
    utcnow = datetime.now(tz=UTC)
    if getattr(request, "conversation_id", None):
        conversation = await Conversation.get(request.conversation_id)
        prev_messages = await Message.find(Message.conversation.id == PydanticObjectId(conversation.id)).to_list()
    else:
        conversation = Conversation(user=user, created_at=utcnow)
        await conversation.insert()

    memories = format_chat_history(prev_messages)

    question = request.question
    try:
        answer_raw = DEFAULT_RAG_PIPELINE.run(
            data={
                "text_embedder": {"text": question},
                "prompt_builder": {"query": question, "memories": memories},
                "answer_builder": {"query": question}
            })
    except Exception as e:
        logger.exception(e)
        return {
            "user_id": str(user.id),
            "conversation_id": str(conversation.id),
            "answer": str(e)}

    answer_utcnow = datetime.now(tz=UTC)
    logger.debug(f"user_id={str(user.id)}, conversation_id={str(conversation.id)}, {answer_raw=}")

    top_answer = answer_raw["answer_builder"]["answers"][0]
    # extract relevant documents
    documents = [(lambda d: {"id": d.id,
                             "score": d.score,
                             "file_path": d.meta["file_path"],
                             "source_id": d.meta["source_id"]})(d) for d in top_answer.documents]
    new_message = Message(conversation=conversation,
                          user=user,
                          query=question,
                          query_created_at=utcnow,
                          response=top_answer.data,
                          model=top_answer.meta.get("model"),
                          finish_reason=top_answer.meta.get("finish_reason"),
                          documents=documents,
                          response_created_at=answer_utcnow)

    await new_message.insert()

    return {
        "user_id": str(user.id),
        "conversation_id": str(conversation.id),
        "answer": top_answer.data}
