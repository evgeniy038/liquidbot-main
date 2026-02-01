"""
Semantic text chunking with context preservation.
"""

from typing import List

from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.utils import get_logger

logger = get_logger(__name__)


def semantic_chunk(
    text: str,
    max_size: int = 500,
    overlap: int = 100,
    separators: List[str] = None,
) -> List[str]:
    """
    Split text into semantic chunks with overlap.
    
    Args:
        text: Text to chunk
        max_size: Maximum chunk size in characters
        overlap: Overlap between chunks
        separators: Custom separators (optional)
    
    Returns:
        List of text chunks
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=max_size,
        chunk_overlap=overlap,
        separators=separators,
        length_function=len,
    )
    
    chunks = splitter.split_text(text)
    
    logger.debug(
        "text_chunked",
        original_length=len(text),
        chunks_created=len(chunks),
        avg_chunk_size=sum(len(c) for c in chunks) // len(chunks) if chunks else 0,
    )
    
    return chunks


def add_context_header(chunk: str, metadata: dict) -> str:
    """
    Add contextual header to chunk for better retrieval.
    
    Args:
        chunk: Text chunk
        metadata: Document metadata
    
    Returns:
        Chunk with context header
    """
    context_parts = []
    
    if "channel_name" in metadata:
        context_parts.append(f"Channel: {metadata['channel_name']}")
    
    if "title" in metadata:
        context_parts.append(f"Document: {metadata['title']}")
    
    if context_parts:
        header = " | ".join(context_parts)
        return f"[{header}]\n\n{chunk}"
    
    return chunk
