from haystack.dataclasses import ChatMessage
from app.models.chat_models import Message


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
