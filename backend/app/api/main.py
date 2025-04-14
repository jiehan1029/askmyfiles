import os
import logging
from dotenv import load_dotenv
from beanie import PydanticObjectId
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from app.services.document_stores import DEFAULT_DOCUMENT_STORE
from app.services.pipelines import DEFAULT_RAG_PIPELINE
from datetime import UTC, datetime
from app.models.chat_models import User, Message, Conversation
from app.models.status_models import SyncStatusBeanie
from app.services.database import init_mongodb_beanie, init_qdrant
from contextlib import asynccontextmanager
from app.api.utils import format_chat_history
from app.services.celery import sync_folder
from celery.result import AsyncResult
import asyncio


if os.getenv("APP_ENV", "development").lower() == "development":
    print(f'main: Loading dotenv for {os.getenv("APP_ENV", "development")} APP_ENV.')
    load_dotenv()


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO').upper()
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FastAPI app is starting up.")

    await init_mongodb_beanie()
    print("Beanie initiated.")

    init_qdrant()
    print("Qdrant initiated.")

    yield
    print("FastAPI app will shut down.")

app = FastAPI(lifespan=lifespan)

origins = [
    "http://localhost:80",
    "http://localhost:3000",
    "http://localhost:5173"
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


@app.websocket("/ws/sync_status/{task_id}")
async def sync_status_ws(websocket: WebSocket, task_id: str):
    await websocket.accept()
    try:
        while True:
            result = AsyncResult(task_id)
            if result.state == "IN_PROGRESS":
                await websocket.send_json({
                    "status": "in_progress",
                    **result.info  # this includes 'current', 'total', 'file', etc.
                })
            elif result.state == "SUCCESS":
                await websocket.send_json({"status": "complete", **(result.info or {})})
                break
            elif result.state in ("FAILURE", "REVOKED"):
                await websocket.send_json({"status": "error", "detail": str(result.result)})
                break
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass


class CreateUserRequest(BaseModel):
    username: str
    timezone: Optional[str] = "US/Pacific"


@app.post("/users")
async def create_user(request: CreateUserRequest):
    """
    todo: pause: not supporting multi user atm
    """
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


class SyncedFoldersResponse(BaseModel):
    folder_path: str
    last_synced_at: datetime | None
    total_files: int
    processed_files: int
    status: str


@app.get("/synced_folders", response_model=list[SyncedFoldersResponse])
async def get_synced_folders(request: Request):
    """
    Return folder syncing history
    """
    # get latest sync records for unique folder_path
    pipeline = [
        {"$match": {"status": "COMPLETE"}},
        {"$sort": {"last_synced_at": -1}},  # sort newest first
        {"$group": {
            "_id": "$folder_path",
            "latest_sync": {"$first": "$$ROOT"}
        }},
        {"$replaceRoot": {"newRoot": "$latest_sync"}},
        {"$sort": {"last_synced_at": -1}}
    ]
    results = await SyncStatusBeanie.aggregate(pipeline).to_list()
    # Convert raw aggregation docs to Beanie documents
    results = [SyncStatusBeanie.model_validate(doc) for doc in results]
    return results


class InsertDocumentsRequest(BaseModel):
    directory: str  # example: "~/Desktop"
    home_dir: str = "/Users"


@app.post("/insert_documents")
async def insert_documents_into_store(request: InsertDocumentsRequest):
    sync_status = await SyncStatusBeanie(
        folder_path=request.directory,
        total_files=0,
        processed_files=0,
        progress_percent=0,
        status="PENDING",
        task_id=None,
    ).insert()
    task = sync_folder.delay(folder_path=request.directory, actual_home_dir=request.home_dir, sync_status_id=str(sync_status.id))
    # then store the task ID back in Mongo
    await sync_status.set({"task_id": task.id, "status": "IN_PROGRESS"})
    return {
        "directory": request.directory,
        "status": "IN_PROGRESS",
        "task_id": task.id,
        "sync_status_id": str(sync_status.id)
    }


class SearchRequest(BaseModel):
    question: str
    # user_id: str | None = "67e83a39a5c04b8d46acd180"
    conversation_id: str | None = None


# Endpoint to accept search requests
@app.post("/search")
async def search_documents(request: SearchRequest):
    """
    Generate answers and save chat conversatios.
    """
    # user = await User.get(request.user_id)
    conversation = None
    prev_messages = []
    utcnow = datetime.now(tz=UTC)
    if getattr(request, "conversation_id", None):
        conversation = await Conversation.get(request.conversation_id)
        prev_messages = await Message.find(Message.conversation.id == PydanticObjectId(conversation.id)).to_list()
    else:
        conversation = Conversation(created_at=utcnow)
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
            # "user_id": str(user.id) if user else None,
            "conversation_id": str(conversation.id),
            "answer": str(e)}

    answer_utcnow = datetime.now(tz=UTC)
    # logger.debug(f"user_id={str(user.id)}, conversation_id={str(conversation.id)}, {answer_raw=}")

    top_answer = answer_raw["answer_builder"]["answers"][0]
    # extract relevant documents
    documents = [(lambda d: {"id": d.id,
                             "score": d.score,
                             "file_path": d.meta["file_path"],
                             "source_id": d.meta["source_id"]})(d) for d in top_answer.documents]
    new_message = Message(conversation=conversation,
                          #   user=user,
                          query=question,
                          query_created_at=utcnow,
                          response=top_answer.data,
                          model=top_answer.meta.get("model"),
                          finish_reason=top_answer.meta.get("finish_reason"),
                          documents=documents,
                          response_created_at=answer_utcnow)

    await new_message.insert()

    return {
        # "user_id": str(user.id) if user else None,
        "conversation_id": str(conversation.id),
        "answer": top_answer.data}


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    Generate answers and save chat conversatios; use websocket.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            question = data["question"]
            conversation_id = data.get("conversation_id")
            history_limit = data.get("history_limit", 10)  # default to 10 turns

            # Send "thinking" status immediately
            await websocket.send_json({
                "status": "thinking",
                "question": question
            })

            utcnow = datetime.now(tz=UTC)
            conversation = None
            prev_messages = []

            if conversation_id:
                conversation = await Conversation.get(conversation_id)
                prev_messages = await Message.find(
                    Message.conversation.id == PydanticObjectId(conversation.id)).sort("-query_created_at").limit(history_limit * 2).to_list()
            else:
                conversation = Conversation(created_at=utcnow)
                await conversation.insert()

            memories = format_chat_history(prev_messages)

            try:
                answer_raw = DEFAULT_RAG_PIPELINE.run(
                    data={
                        "text_embedder": {"text": question},
                        "prompt_builder": {"query": question, "memories": memories},
                        "answer_builder": {"query": question}
                    })
            except Exception as e:
                await websocket.send_json({
                    "status": "error",
                    "conversation_id": str(conversation.id),
                    "error": str(e)
                })
                continue

            top_answer = answer_raw["answer_builder"]["answers"][0]
            documents = [(lambda d: {
                "id": d.id,
                "score": d.score,
                "file_path": d.meta["file_path"],
                "source_id": d.meta["source_id"]
            })(d) for d in top_answer.documents]

            new_message = Message(
                conversation=conversation,
                query=question,
                query_created_at=utcnow,
                response=top_answer.data,
                model=top_answer.meta.get("model"),
                finish_reason=top_answer.meta.get("finish_reason"),
                documents=documents,
                response_created_at=datetime.now(tz=UTC)
            )
            await new_message.insert()

            await websocket.send_json({
                "status": "complete",
                "conversation_id": str(conversation.id),
                "answer": top_answer.data,
                "documents": documents
            })

    except WebSocketDisconnect:
        logger.info("Client disconnected from /ws/chat")
