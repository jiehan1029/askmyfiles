import os
from typing import Any
from haystack.components.writers import DocumentWriter
from haystack.components.converters import MarkdownToDocument, PyPDFToDocument, TextFileToDocument
from haystack.components.preprocessors import DocumentSplitter, DocumentCleaner
from haystack.components.routers import FileTypeRouter
from haystack.components.joiners import DocumentJoiner
from haystack import Pipeline
from haystack.components.embedders import (
    SentenceTransformersDocumentEmbedder,
    SentenceTransformersTextEmbedder
)
from app.services.document_stores import (
    IN_MEMORY_DOCUMENT_STORE,
    QDRANT_DOCUMENT_STORE
)
from haystack.document_stores.types import DuplicatePolicy, DocumentStore
from haystack.components.retrievers.in_memory import InMemoryEmbeddingRetriever
from haystack.components.generators.chat import HuggingFaceAPIChatGenerator
from haystack.dataclasses import ChatMessage
from haystack.utils import Secret
from haystack.utils.hf import HFGenerationAPIType
from haystack.components.builders import ChatPromptBuilder
from haystack.components.builders import AnswerBuilder
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.components.generators.google_ai import GoogleAIGeminiChatGenerator


DOCUMENT_STORE_NAME = os.getenv("DOCUMENT_STORE_NAME")


def build_preprocessing_pipeline(
        document_store: DocumentStore,
        file_types: list[str] = ["text/plain", "text/html", "application/pdf", "text/markdown"],
        document_embedder: Any | None = None) -> Pipeline:
    """
    Return an indexing pipeline that loads the document store.
    """
    preprocessing_pipeline = Pipeline()

    text_file_converter = TextFileToDocument()
    markdown_converter = MarkdownToDocument()
    pdf_converter = PyPDFToDocument()
    document_joiner = DocumentJoiner()
    document_cleaner = DocumentCleaner()
    document_splitter = DocumentSplitter(split_by="word", split_length=150, split_overlap=50)

    file_type_router = FileTypeRouter(mime_types=file_types)
    preprocessing_pipeline.add_component(instance=file_type_router, name="file_type_router")
    # todo: allow customize file_types
    # https://docs.haystack.deepset.ai/docs/converters
    preprocessing_pipeline.add_component(instance=text_file_converter, name="text_file_converter")
    preprocessing_pipeline.add_component(instance=markdown_converter, name="markdown_converter")
    preprocessing_pipeline.add_component(instance=pdf_converter, name="pypdf_converter")
    preprocessing_pipeline.add_component(instance=document_joiner, name="document_joiner")
    preprocessing_pipeline.add_component(instance=document_cleaner, name="document_cleaner")
    preprocessing_pipeline.add_component(instance=document_splitter, name="document_splitter")
    if document_embedder:
        preprocessing_pipeline.add_component(instance=document_embedder, name="document_embedder")
    # set duplicate policy to be "overwrite"
    document_writer = DocumentWriter(document_store=document_store, policy=DuplicatePolicy.OVERWRITE)
    preprocessing_pipeline.add_component(instance=document_writer, name="document_writer")

    preprocessing_pipeline.connect("file_type_router.text/plain", "text_file_converter.sources")
    preprocessing_pipeline.connect("file_type_router.application/pdf", "pypdf_converter.sources")
    preprocessing_pipeline.connect("file_type_router.text/markdown", "markdown_converter.sources")
    preprocessing_pipeline.connect("text_file_converter", "document_joiner")
    preprocessing_pipeline.connect("pypdf_converter", "document_joiner")
    preprocessing_pipeline.connect("markdown_converter", "document_joiner")
    preprocessing_pipeline.connect("document_joiner", "document_cleaner")
    preprocessing_pipeline.connect("document_cleaner", "document_splitter")
    if document_embedder:
        preprocessing_pipeline.connect("document_splitter", "document_embedder")
        preprocessing_pipeline.connect("document_embedder", "document_writer")
    else:
        preprocessing_pipeline.connect("document_splitter", "document_writer")

    return preprocessing_pipeline


def build_rag_pipeline(retriever, text_embedder):
    """
    Return a RAG pipeline.
    """
    basic_rag_pipeline = Pipeline()

    # Add components to your pipeline
    basic_rag_pipeline.add_component("text_embedder", text_embedder)
    basic_rag_pipeline.add_component("retriever", retriever)

    user_message_template = [
        ChatMessage.from_user(
            """
            Given the conversation history and the provided supporting documents, give a brief answer to the question.
            Note that supporting documents are not part of the conversation.
            Use conversation history only if necessary.
            If the conversation history is empty, DO NOT including them in generating the answer.
            If question can't be answered from supporting documents, say so.
            Do not rewrite the query.

            Conversation history:
            {% for message in memories %}
                {{ message.text }}
            {% endfor %}

            Supporting documents:
            {% for document in documents %}
                {{ document.content }}
            {% endfor %}

            Question: {{query}}
            Answer:
            """
        )
    ]
    prompt_builder = ChatPromptBuilder(template=user_message_template,
                                       variables=["query", "documents", "memories"],
                                       required_variables=["query", "documents", "memories"])
    basic_rag_pipeline.add_component("prompt_builder", prompt_builder)

    # toggle between generators
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "hf").lower()
    if LLM_PROVIDER == "google":
        # https://ai.google.dev/gemini-api/docs/models
        # https://ai.google.dev/gemini-api/docs/rate-limits
        generator = GoogleAIGeminiChatGenerator(
            api_key=Secret.from_env_var("GOOGLE_API_KEY"),
            model="gemini-2.0-flash"
        )
    else:
        generator = HuggingFaceAPIChatGenerator(
            api_type=HFGenerationAPIType.SERVERLESS_INFERENCE_API,  # free version LLM
            api_params={"model": "HuggingFaceH4/zephyr-7b-beta"},
            token=Secret.from_env_var("HF_API_TOKEN")
        )
    basic_rag_pipeline.add_component("generator", generator)

    answer_builder = AnswerBuilder()
    basic_rag_pipeline.add_component("answer_builder", answer_builder)

    # Connect the components to each other
    basic_rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    basic_rag_pipeline.connect("retriever.documents", "prompt_builder.documents")
    basic_rag_pipeline.connect("prompt_builder.prompt", "generator.messages")
    basic_rag_pipeline.connect("generator.replies", "answer_builder.replies")
    # Pass retrieved documents to answer_builder
    # (NOT generator because HuggingFaceAPIChatGenerator does not take documents as input)
    basic_rag_pipeline.connect("retriever.documents", "answer_builder.documents")

    return basic_rag_pipeline


###
# Global pipeline instances ready to use
###
# matching document & text embedders must use the same model
in_memory_retriever = InMemoryEmbeddingRetriever(IN_MEMORY_DOCUMENT_STORE)
IN_MEMORY_PREPROCESSING_PIPELINE = build_preprocessing_pipeline(
    document_store=IN_MEMORY_DOCUMENT_STORE,
    document_embedder=SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
)
IN_MEMORY_RAG_PIPELINE = build_rag_pipeline(
    retriever=in_memory_retriever,
    text_embedder=SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
)


qdrant_retriever = QdrantEmbeddingRetriever(document_store=QDRANT_DOCUMENT_STORE)
QDRANT_PREPROCESSING_PIPELINE = build_preprocessing_pipeline(
    document_store=QDRANT_DOCUMENT_STORE,
    document_embedder=SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
)
QDRANT_RAG_PIPELINE = build_rag_pipeline(
    retriever=qdrant_retriever,
    text_embedder=SentenceTransformersTextEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
)


###
# Default selection based on config
###
DEFAULT_PREPROCESSING_PIPELINE = QDRANT_PREPROCESSING_PIPELINE if DOCUMENT_STORE_NAME == "qdrant" else IN_MEMORY_PREPROCESSING_PIPELINE
DEFAULT_RAG_PIPELINE = QDRANT_RAG_PIPELINE if DOCUMENT_STORE_NAME == "qdrant" else IN_MEMORY_RAG_PIPELINE
