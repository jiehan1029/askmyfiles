import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Optional

from beanie import PydanticObjectId
from celery.result import AsyncResult
from dotenv import load_dotenv
from fastapi import (FastAPI, HTTPException, Request, WebSocket,
                     WebSocketDisconnect)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.api.utils import (extract_conversation_summary, format_chat_history,
                           get_user_settings)
from app.models.chat_models import Conversation, Message, User
from app.models.status_models import SyncStatusBeanie
from app.services.celery import sync_folder
from app.services.database import init_mongodb_beanie, init_qdrant
from app.services.document_stores import QDRANT_DOCUMENT_STORE
from app.services.pipelines import build_rag_pipeline_in_qdrant

if os.getenv("APP_ENV", "development").lower() == "development":
    print(f'main: Loading dotenv for {os.getenv("APP_ENV", "development")} APP_ENV.')
    load_dotenv()


logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO").upper())


# global RAG_PIPELINE
RAG_PIPELINE = 0


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

origins = ["http://localhost:80", "http://localhost:3000", "http://localhost:5173"]
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
                await websocket.send_json(
                    {
                        "status": "in_progress",
                        **result.info,  # this includes 'current', 'total', 'file', etc.
                    }
                )
            elif result.state == "SUCCESS":
                await websocket.send_json({"status": "complete", **(result.info or {})})
                break
            elif result.state in ("FAILURE", "REVOKED"):
                await websocket.send_json(
                    {"status": "error", "detail": str(result.result)}
                )
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
    Endpoint not used now.
    """
    found_user = await User.find({"username": request.username}).first_or_none()
    if found_user:
        raise HTTPException(
            status_code=400, detail={"error": "Username already exists."}
        )
    user = User(username=request.username, timezone=request.timezone)
    await user.insert()
    return user


@app.get("/app_ready")
async def get_app_ready_status(request: Request):
    user_setting = await get_user_settings()
    if not user_setting.llm_provider:
        logger.info("Missing user_setting.llm_provider, app is not ready.")
        return {"settings_ready": False}
    if not user_setting.llm_model:
        logger.info("Missing user_setting.llm_model, app is not ready.")
        return {"settings_ready": False}
    if not user_setting.llm_api_token:
        if user_setting.llm_provider != "ollama":
            logger.info(
                "Missing user_setting.llm_api_token for non-ollama provider, app is not ready."
            )
            return {"settings_ready": False}

    global RAG_PIPELINE
    if not RAG_PIPELINE:
        RAG_PIPELINE = build_rag_pipeline_in_qdrant(
            llm_provider=user_setting.llm_provider,
            llm_model=user_setting.llm_model,
            llm_api_token=user_setting.llm_api_token,
        )
        logger.info(
            f"Initiated RAG_PIPELINE with {user_setting.llm_provider}/{user_setting.llm_model}/{user_setting.llm_api_token}"
        )

    return {"settings_ready": True}


class SyncedFolderRecord(BaseModel):
    folder_path: str
    last_synced_at: int | None
    total_files: int
    processed_files: int
    skipped_files: int = 0
    status: str


class SyncedFoldersResponse(BaseModel):
    results: list[SyncedFolderRecord]
    file_count: int


@app.get("/synced_folders", response_model=SyncedFoldersResponse)
async def get_synced_folders(request: Request):
    """
    Return folder syncing history
    """
    # get latest sync records for unique folder_path
    pipeline = [
        {"$match": {"status": "COMPLETE"}},
        {"$sort": {"last_synced_at": -1}},  # sort newest first
        {"$group": {"_id": "$folder_path", "latest_sync": {"$first": "$$ROOT"}}},
        {"$replaceRoot": {"newRoot": "$latest_sync"}},
        {"$sort": {"last_synced_at": -1}},
    ]
    raw_results = await SyncStatusBeanie.aggregate(pipeline).to_list()
    results = []
    total_processed = 0
    for doc in raw_results:
        model = SyncStatusBeanie.model_validate(doc)
        model_dict = model.model_dump()  # convert to a regular dict
        model_dict["last_synced_at"] = (
            int(model.last_synced_at.timestamp() * 1000) if model.last_synced_at else 0
        )
        results.append(model_dict)
        total_processed += model_dict["processed_files"]
    return {"results": results, "file_count": total_processed}


class DeleteFolderPayload(BaseModel):
    directory: str
    home_dir: str = ""


@app.post("/delete_folder", status_code=201)
async def delete_folder(payload: DeleteFolderPayload):
    """
    Remove files previously upload from this folder.
    """
    if payload.directory == "all":
        # remove all synced folders and files
        all_docs = QDRANT_DOCUMENT_STORE.filter_documents()
        doc_ids = [doc.id for doc in all_docs]
        QDRANT_DOCUMENT_STORE.delete_documents(doc_ids)
        logger.info(f"Deleted all {len(doc_ids)} documents.")
        # also delete all sync records
        await SyncStatusBeanie.find().delete()
        return

    sync_records = await SyncStatusBeanie.find(
        SyncStatusBeanie.folder_path == payload.directory,
        SyncStatusBeanie.home_dir == payload.home_dir,
    ).to_list()
    source_files = []
    for rec in sync_records:
        source_files.extend(rec.source_files)

    # delete documents
    doc_filters = {
        "operator": "AND",
        "conditions": [
            {"field": "meta.source_file", "operator": "in", "value": source_files}
        ],
    }
    docs = QDRANT_DOCUMENT_STORE.filter_documents(filters=doc_filters)
    doc_ids = [doc.id for doc in docs]
    if len(doc_ids) > 0:
        QDRANT_DOCUMENT_STORE.delete_documents(document_ids=doc_ids)
        logger.info(
            f"Deleted {len(doc_ids)} documents from {len(source_files)} source files"
        )
    else:
        logger.info(f"No documents found from {len(source_files)} source files.")

    await SyncStatusBeanie.find(
        SyncStatusBeanie.folder_path == payload.directory,
        SyncStatusBeanie.home_dir == payload.home_dir,
    ).delete()

    return


class InsertDocumentsRequest(BaseModel):
    directory: str  # example: "~/Desktop"
    home_dir: str = "/Users"


@app.post("/insert_documents")
async def insert_documents_into_store(request: InsertDocumentsRequest):
    sync_status = await SyncStatusBeanie(
        folder_path=request.directory,
        home_dir=request.home_dir,
        total_files=0,
        processed_files=0,
        progress_percent=0,
        status="PENDING",
        task_id=None,
    ).insert()
    task = sync_folder.delay(
        folder_path=request.directory,
        actual_home_dir=request.home_dir,
        sync_status_id=str(sync_status.id),
    )
    # then store the task ID back in Mongo
    await sync_status.set({"task_id": task.id, "status": "IN_PROGRESS"})
    return {
        "directory": request.directory,
        "status": "IN_PROGRESS",
        "task_id": task.id,
        "sync_status_id": str(sync_status.id),
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
    This endpoint is not used by fronten. Only to test the pipeline.
    """
    # user = await User.get(request.user_id)
    conversation = None
    prev_messages = []
    utcnow = datetime.now(tz=UTC)
    if getattr(request, "conversation_id", None):
        conversation = await Conversation.get(request.conversation_id)
        prev_messages = await Message.find(
            Message.conversation.id == PydanticObjectId(conversation.id)
        ).to_list()
    else:
        conversation = Conversation(created_at=utcnow)
        await conversation.insert()

    memories = format_chat_history(prev_messages)
    question = request.question

    user_setting = await get_user_settings()
    RAG_PIPELINE = build_rag_pipeline_in_qdrant(
        llm_provider=user_setting.llm_provider,
        llm_model=user_setting.llm_model,
        llm_api_token=user_setting.llm_api_token,
    )
    try:
        answer_raw = RAG_PIPELINE.run(
            data={
                "text_embedder": {"text": question},
                "prompt_builder": {"query": question, "memories": memories},
                "answer_builder": {"query": question},
            }
        )
    except Exception as e:
        logger.exception(e)
        return {
            # "user_id": str(user.id) if user else None,
            "conversation_id": str(conversation.id),
            "answer": str(e),
        }

    answer_utcnow = datetime.now(tz=UTC)
    # logger.debug(f"user_id={str(user.id)}, conversation_id={str(conversation.id)}, {answer_raw=}")

    top_answer = answer_raw["answer_builder"]["answers"][0]
    # extract relevant documents
    documents = [
        (
            lambda d: {
                "id": d.id,
                "score": d.score,
                "file_path": d.meta["file_path"],
                "source_id": d.meta["source_id"],
            }
        )(d)
        for d in top_answer.documents
    ]
    new_message = Message(
        conversation=conversation,
        #   user=user,
        query=question,
        query_created_at=utcnow,
        response=top_answer.data,
        model=top_answer.meta.get("model"),
        finish_reason=top_answer.meta.get("finish_reason"),
        documents=documents,
        response_created_at=answer_utcnow,
    )

    await new_message.insert()

    return {
        # "user_id": str(user.id) if user else None,
        "conversation_id": str(conversation.id),
        "answer": top_answer.data,
    }


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    Generate answers and save chat conversatios; use websocket.
    """
    await websocket.accept()
    try:
        global RAG_PIPELINE
        if not RAG_PIPELINE:
            user_setting = await get_user_settings()
            RAG_PIPELINE = build_rag_pipeline_in_qdrant(
                llm_provider=user_setting.llm_provider,
                llm_model=user_setting.llm_model,
                llm_api_token=user_setting.llm_api_token,
            )
            logger.info(
                f"Initiated RAG_PIPELINE with {user_setting.llm_provider}/{user_setting.llm_model}/{user_setting.llm_api_token}"
            )

        while True:
            data = await websocket.receive_json()
            question = data["question"]
            conversation_id = data.get("conversation_id")
            history_limit = data.get("history_limit", 10)  # default to 10 turns

            # Send "thinking" status immediately
            await websocket.send_json({"status": "thinking", "question": question})

            utcnow = datetime.now(tz=UTC)
            conversation = None
            prev_messages = []

            if conversation_id:
                conversation = await Conversation.get(conversation_id)
                prev_messages = (
                    await Message.find(
                        Message.conversation.id == PydanticObjectId(conversation.id)
                    )
                    .sort("-query_created_at")
                    .limit(history_limit * 2)
                    .to_list()
                )
            else:
                conversation = Conversation(created_at=utcnow)
                await conversation.insert()

            memories = format_chat_history(prev_messages)
            try:
                answer_raw = RAG_PIPELINE.run(
                    data={
                        "text_embedder": {"text": question},
                        "prompt_builder": {"query": question, "memories": memories},
                        "answer_builder": {"query": question},
                    }
                )
            except Exception as e:
                await websocket.send_json(
                    {
                        "status": "error",
                        "conversation_id": str(conversation.id),
                        "error": str(e),
                    }
                )
                continue

            top_answer = answer_raw["answer_builder"]["answers"][0]
            documents = [
                (
                    lambda d: {
                        "id": d.id,
                        "score": d.score,
                        "file_path": d.meta["file_path"],
                        "source_id": d.meta["source_id"],
                    }
                )(d)
                for d in top_answer.documents
            ]

            new_message = Message(
                conversation=conversation,
                query=question,
                query_created_at=utcnow,
                response=top_answer.data,
                model=top_answer.meta.get("model"),
                finish_reason=top_answer.meta.get("finish_reason"),
                documents=documents,
                response_created_at=datetime.now(tz=UTC),
            )
            await new_message.insert()

            await websocket.send_json(
                {
                    "status": "complete",
                    "conversation_id": str(conversation.id),
                    "answer": top_answer.data,
                    "documents": documents,
                }
            )

    except WebSocketDisconnect:
        logger.info("Client disconnected from /ws/chat")


class ChatHistoryResponse(BaseModel):
    conversation_id: str
    summary: str | None = None
    created_at: int


@app.get("/chat_history", response_model=list[ChatHistoryResponse])
async def get_chat_history():
    """
    Return all conversations stored. (won't differentiate user since atm not supporting multi user).
    """
    # todo: pagination
    # currently support past 10 conversations
    all_conversations = (
        await Conversation.find().sort("-created_at").limit(10).to_list()
    )
    results = []
    for convo in all_conversations:
        convo_summary = ""
        if convo.summary:
            convo_summary = convo.summary
        else:
            extracted = await extract_conversation_summary(
                conversation_id=str(convo.id)
            )
            if extracted.get("error"):
                logger.info(
                    f'Skipping conversation ({str(convo.id)}): {extracted.get("error")}'
                )
            else:
                convo_summary = extracted.get("summary", "")
        results.append(
            {
                "conversation_id": str(convo.id),
                "summary": convo_summary,
                "created_at": int(
                    convo.created_at.timestamp() * 1000
                ),  # miliseconds, for FE
            }
        )
    return results


@app.delete("/chat_history/{conversation_id}", status_code=201)
async def delete_chat_history_by_id(conversation_id: str):
    conversation = await Conversation.get(conversation_id)
    if not conversation:
        return

    await conversation.delete()
    return


class MessageRecord(BaseModel):
    query: str
    response: str


class GetChatHistoryByIdResponse(BaseModel):
    conversation_id: str
    summary: Optional[str] = None
    created_at: datetime
    messages: list[MessageRecord]


@app.get("/chat_history/{conversation_id}")
async def get_chat_history_by_id(conversation_id: str):
    conversation = await Conversation.get(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=400, detail={"error": "Cannot find the conversation."}
        )

    prev_messages = (
        await Message.find(Message.conversation.id == PydanticObjectId(conversation.id))
        .sort("query_created_at")
        .to_list()
    )
    message_list = []
    for msg in prev_messages:
        message_list.append({"query": msg.query, "response": msg.response})
    return {
        "conversation_id": conversation_id,
        "summary": conversation.summary,
        "created_at": conversation.created_at,
        "messages": message_list,
    }


@app.get("/chat_summary/{conversation_id}")
async def summarize_conversation(conversation_id: str):
    """
    Given conversation id, return its summary. If not yet have one, run pipeline to generate it.
    """
    result = await extract_conversation_summary(conversation_id=conversation_id)
    if result.get("error"):
        raise HTTPException(status_code=400, detail={"error": result.get("error")})

    return result


@app.get("/settings")
async def get_settings():
    """
    Settings are saved per user (though it's not supporting multi user atm).
    Assume there is only one.
    """
    return await get_user_settings()


class PatchSettingsPayload(BaseModel):
    locale: Optional[str]
    timezone: Optional[str]
    llm_provider: Optional[str]
    llm_api_token: Optional[str]
    llm_model: Optional[str]


@app.patch("/settings/{user_id}")
async def patch_settings(user_id: str, payload: PatchSettingsPayload):
    curr_user = await User.get(user_id)
    assert curr_user is not None, "No users left!"

    if getattr(payload, "locale", None) is not None:
        curr_user.locale = payload.locale
    if getattr(payload, "timezone", None) is not None:
        curr_user.timezone = payload.timezone
    if getattr(payload, "llm_provider", None) is not None:
        curr_user.llm_provider = payload.llm_provider
    if getattr(payload, "llm_api_token", None) is not None:
        curr_user.llm_api_token = payload.llm_api_token
    if getattr(payload, "llm_model", None) is not None:
        curr_user.llm_model = payload.llm_model
    await curr_user.save()

    # update RAG pipeline based on settings
    global RAG_PIPELINE
    RAG_PIPELINE = build_rag_pipeline_in_qdrant(
        llm_provider=curr_user.llm_provider,
        llm_model=curr_user.llm_model,
        llm_api_token=curr_user.llm_api_token,
    )
    logger.info(
        f"Updated RAG_PIPELINE with {curr_user.llm_provider}/{curr_user.llm_model}/{curr_user.llm_api_token}"
    )

    return curr_user
