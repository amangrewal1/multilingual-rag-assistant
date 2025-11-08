import json
import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

import numpy as np


@dataclass
class Chunk:
    doc_id: str
    chunk_id: int
    source: str
    title: str
    text: str


@dataclass
class Hit:
    chunk: Chunk
    score: float


def _split_chunks(text: str, max_tokens: int = 180) -> List[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, buf, count = [], [], 0
    for p in paragraphs:
        tokens = len(p.split())
        if count + tokens > max_tokens and buf:
            chunks.append("\n\n".join(buf))
            buf, count = [], 0
        buf.append(p)
        count += tokens
    if buf:
        chunks.append("\n\n".join(buf))
    return chunks


class Retriever:
    def __init__(self, embed_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        from sentence_transformers import SentenceTransformer  # lazy import
        self.model = SentenceTransformer(embed_model)
        self.chunks: List[Chunk] = []
        self.matrix: Optional[np.ndarray] = None

    def _embed(self, texts: List[str]) -> np.ndarray:
        vecs = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return np.asarray(vecs, dtype=np.float32)

    def index_directory(self, path: str) -> int:
        base = Path(path)
        chunks: List[Chunk] = []
        for file in sorted(base.glob("**/*.md")):
            text = file.read_text(encoding="utf-8")
            title = text.splitlines()[0].lstrip("# ").strip() if text else file.stem
            for i, chunk in enumerate(_split_chunks(text)):
                chunks.append(
                    Chunk(
                        doc_id=file.stem,
                        chunk_id=i,
                        source=str(file.relative_to(base)),
                        title=title,
                        text=chunk,
                    )
                )
        if not chunks:
            raise RuntimeError(f"No markdown found under {path}")
        self.chunks = chunks
        self.matrix = self._embed([c.text for c in chunks])
        return len(chunks)

    def save(self, path: str) -> None:
        assert self.matrix is not None
        np.save(path + ".npy", self.matrix)
        with open(path + ".json", "w", encoding="utf-8") as f:
            json.dump([asdict(c) for c in self.chunks], f, ensure_ascii=False)

    def load(self, path: str) -> None:
        self.matrix = np.load(path + ".npy")
        with open(path + ".json", "r", encoding="utf-8") as f:
            self.chunks = [Chunk(**c) for c in json.load(f)]

    def search(self, query: str, top_k: int = 4, min_score: float = 0.15) -> List[Hit]:
        assert self.matrix is not None, "index first"
        q = self._embed([query])[0]
        scores = self.matrix @ q
        order = np.argsort(-scores)[:top_k]
        return [
            Hit(chunk=self.chunks[i], score=float(scores[i]))
            for i in order
            if scores[i] >= min_score
        ]
