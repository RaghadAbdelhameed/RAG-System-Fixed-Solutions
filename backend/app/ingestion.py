"""
Turns an uploaded file into embedded, searchable chunks tied to one
organization. Supports PDF, DOCX, TXT, CSV.
"""
import io
from functools import lru_cache

import pandas as pd
from pypdf import PdfReader
from docx import Document as DocxDocument
from sentence_transformers import SentenceTransformer

from .config import settings


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(settings.EMBEDDING_MODEL)


def extract_text(filename: str, raw_bytes: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if lower.endswith(".docx"):
        doc = DocxDocument(io.BytesIO(raw_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    if lower.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(raw_bytes))
        return df.to_string(index=False)
    # default: treat as plain text
    return raw_bytes.decode("utf-8", errors="ignore")


def split_into_chunks(text: str, chunk_words: int = None, overlap_words: int = None):
    chunk_words = chunk_words or settings.CHUNK_WORDS
    overlap_words = overlap_words or settings.CHUNK_OVERLAP_WORDS

    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    step = max(chunk_words - overlap_words, 1)
    while start < len(words):
        piece = " ".join(words[start:start + chunk_words])
        if piece.strip():
            chunks.append(piece.strip())
        start += step
    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    return embed_texts([text])[0]
