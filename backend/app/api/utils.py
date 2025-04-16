import logging
from haystack.dataclasses import ChatMessage
from app.models.chat_models import Message, Conversation, User
from beanie import PydanticObjectId
from app.services.pipelines import build_summary_pipeline

logger = logging.getLogger(__name__)


def format_chat_history(chat_history: list[Message]) -> list[ChatMessage]:
    """
    This is equivalent of memory retriever in https://haystack.deepset.ai/cookbook/conversational_rag_using_memory
    """
    memories = []
    for chat_message in chat_history:
        if chat_message.query:
            user_chat = ChatMessage.from_user(text=chat_message.query,
                                              meta={"timestamp": chat_message.query_created_at})
            memories.append(user_chat)
        if chat_message.response:
            bot_chat = ChatMessage.from_system(text=chat_message.response,
                                               meta={
                                                    "sender": "bot",
                                                    "timestamp": chat_message.response_created_at,
                                                    "model": chat_message.model,
                                                    "finish_reason": chat_message.finish_reason,
                                                    "documents": chat_message.documents,
                                               })
            memories.append(bot_chat)
    return memories


async def extract_conversation_summary(conversation_id: str) -> dict:
    """
    Get or create summary for the conversation, save to database if created.
    """
    conversation = await Conversation.get(conversation_id)
    if not conversation:
        return {"error": "Cannot find the conversation."}

    if conversation.summary:
        return {"summary": conversation.summary, "conversation_id": conversation_id}

    prev_messages = await Message.find(
        Message.conversation.id == PydanticObjectId(conversation.id)).sort("query_created_at").to_list()

    if len(prev_messages) == 0:
        return {"error": "No message found in conversation."}

    memories = format_chat_history(prev_messages)
    user_setting = await get_user_settings()
    SUMMARY_PIPELINE = build_summary_pipeline(
        llm_provider=user_setting.llm_provider,
        llm_model=user_setting.llm_model,
        llm_api_token=user_setting.llm_api_token
    )
    answer_raw = SUMMARY_PIPELINE.run(data={
        "prompt_builder": {"memories": memories},
        "answer_builder": {"query": "Summarize this conversation"}  # dummy query
    })
    top_answer = answer_raw["answer_builder"]["answers"][0]

    # save summary to conversation
    conversation.summary = top_answer.data
    await conversation.save()
    return {"summary": conversation.summary, "conversation_id": conversation_id}


async def get_user_settings() -> User:
    users = await User.find().sort("created_at").limit(10).to_list()
    # as safeguard, only keep 1 user
    if len(users) == 0:
        user = await User(
            username="appuser",
            locale="en-US",
            timezone="America/Los_Angeles",
            llm_provider="gemini",
            llm_api_token=None,
            llm_model="gemini-2.0-flash"
        ).insert()
    elif len(users) > 1:
        user = users[0]
        user_id = user.id
        logger.info(f"Clean up users other than {user_id=}.")
        await User.find(User.id != user_id).delete()

    curr_user = await User.find().first_or_none()
    assert curr_user is not None, "No users left!"
    if not curr_user.llm_provider:
        # reset the default
        curr_user.username = "appuser"
        curr_user.locale = "en-US"
        curr_user.timezone = "America/Los_Angeles"
        curr_user.llm_provider = "gemini"
        curr_user.llm_api_token = None
        curr_user.llm_model = "gemini-2.0-flash"
        await curr_user.save()
    return curr_user