"""
Shared Ingestion Utilities for Source Connectors (US-006, US-007).

Provides reusable helper functions for text chunking, checksum calculation,
vector embedding generation, and HTML stripping.
"""

from typing import List
import hashlib
import re
from bs4 import BeautifulSoup


def strip_html_to_text(html_content: str) -> str:
    """Strips HTML/Confluence markup to plain text using BeautifulSoup."""
    if not html_content or not html_content.strip():
        return ""

    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script, style, and navigation elements
    for element in soup(["script", "style", "nav", "header", "footer"]):
        element.decompose()

    text = soup.get_text(separator="\n")
    # Clean up excess whitespace
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def chunk_text(content: str, max_tokens: int = 512, overlap_tokens: int = 50) -> List[str]:
    """Splits text content into overlapping token-budget chunks (default: 512 tokens, 50 overlap)."""
    if not content or not content.strip():
        return []

    # Token-budget word chunking (~1 word = ~1.3 tokens)
    words = content.split()
    if not words:
        return []

    chunks: List[str] = []
    # Target word budget: ~400 words ≈ 512 tokens
    target_words = max(1, int(max_tokens / 1.3))
    target_overlap = max(0, int(overlap_tokens / 1.3))
    step = max(1, target_words - target_overlap)

    i = 0
    while i < len(words):
        chunk_words = words[i : i + target_words]
        chunk_str = " ".join(chunk_words)
        if chunk_str.strip():
            chunks.append(chunk_str)
        if i + target_words >= len(words):
            break
        i += step

    return chunks



def compute_checksum(text: str) -> str:
    """Computes SHA-256 checksum for change detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


from backend.app.services.embedding_provider import get_embedding_provider


def generate_embedding_vector(text: str, dimension: int = 768) -> List[float]:
    """Generates 768-dim float vector using configured EmbeddingProvider."""
    provider = get_embedding_provider()
    return provider.embed_text(text)

