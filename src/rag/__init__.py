"""RAG indexing and retrieval modules."""

from .chunker import add_context_header, semantic_chunk
from .embedder import ImageEmbedder, MultimodalEmbedder, TextEmbedder
from .indexer import DocumentMetadata, MultimodalIndexer
from .retriever import Document, HybridRetriever
from .sqlite_storage import (
    SQLiteMessageStorage,
    StoredMessage,
    get_message_storage,
)

__all__ = [
    "semantic_chunk",
    "add_context_header",
    "TextEmbedder",
    "ImageEmbedder",
    "MultimodalEmbedder",
    "MultimodalIndexer",
    "DocumentMetadata",
    "HybridRetriever",
    "Document",
    # SQLite storage for messages (no AI costs for indexing)
    "SQLiteMessageStorage",
    "StoredMessage",
    "get_message_storage",
]
