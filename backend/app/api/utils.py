from haystack.dataclasses import ChatMessage
from app.models.chat_models import Message, Conversation
from beanie import PydanticObjectId
from app.services.pipelines import SUMMARY_PIPELINE


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
    answer_raw = SUMMARY_PIPELINE.run(data={
        "prompt_builder": {"memories": memories},
        "answer_builder": {"query": "Summarize this conversation"}  # dummy query
    })
    top_answer = answer_raw["answer_builder"]["answers"][0]

    # save summary to conversation
    conversation.summary = top_answer.data
    await conversation.save()
    return {"summary": conversation.summary, "conversation_id": conversation_id}
