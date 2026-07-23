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


def chunk_text(content: str, max_chars: int = 1500, overlap_chars: int = 150) -> List[str]:
    """Splits text content into overlapping character chunks."""
    if not content or not content.strip():
        return []

    chunks: List[str] = []
    start = 0
    length = len(content)

    while start < length:
        end = min(start + max_chars, length)
        chunk_str = content[start:end]
        if chunk_str.strip():
            chunks.append(chunk_str)
        if end == length:
            break
        start += max_chars - overlap_chars

    return chunks


def compute_checksum(text: str) -> str:
    """Computes SHA-256 checksum for change detection."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_embedding_vector(text: str, dimension: int = 768) -> List[float]:
    """Generates a deterministic 768-dim float vector for embeddings."""
    seed = int(hashlib.md5(text.encode("utf-8")).hexdigest()[:8], 16)
    return [(float((seed + i * 31) % 100) / 100.0) for i in range(dimension)]
