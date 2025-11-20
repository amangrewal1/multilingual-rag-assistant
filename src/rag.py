import re
import time
from dataclasses import dataclass, field
from typing import List, Optional

from anthropic import Anthropic

from .prompts import RAG_SYSTEM, RAG_USER_TEMPLATE, SUPPORTED_DIALECTS
from .retriever import Hit, Retriever


CITATION_RX = re.compile(r"\[#(\d+)\]")


@dataclass
class Citation:
    index: int
    source: str
    title: str
    excerpt: str


@dataclass
class RAGResponse:
    answer: str
    dialect: str
    citations: List[Citation]
    hits: List[Hit]
    latency_ms: int
    refused: bool = False
    refusal_reason: str = ""
    meta: dict = field(default_factory=dict)


class RAGPipeline:
    def __init__(
        self,
        client: Anthropic,
        retriever: Retriever,
        model: str = "claude-haiku-4-5-20251001",
        top_k: int = 4,
    ):
        self.client = client
        self.retriever = retriever
        self.model = model
        self.top_k = top_k

    def _format_context(self, hits: List[Hit]) -> str:
        if not hits:
            return "(no relevant documents retrieved)"
        out = []
        for i, h in enumerate(hits, start=1):
            out.append(
                f"[#{i}] ({h.chunk.source} -- {h.chunk.title})\n{h.chunk.text.strip()}"
            )
        return "\n\n".join(out)

    def _extract_citations(self, answer: str, hits: List[Hit]) -> List[Citation]:
        cites = []
        seen = set()
        for m in CITATION_RX.finditer(answer):
            n = int(m.group(1))
            if n in seen or n < 1 or n > len(hits):
                continue
            seen.add(n)
            h = hits[n - 1]
            excerpt = h.chunk.text.strip().split("\n")[0][:160]
            cites.append(Citation(index=n, source=h.chunk.source, title=h.chunk.title, excerpt=excerpt))
        return cites

    def answer(
        self,
        question: str,
        dialect: str = "en",
        retrieval_query: Optional[str] = None,
    ) -> RAGResponse:
        t0 = time.time()
        q_for_retrieval = retrieval_query or question
        hits = self.retriever.search(q_for_retrieval, top_k=self.top_k)

        if not hits:
            return RAGResponse(
                answer="I don't have any indexed material that covers that. Try rephrasing or ask about WCAG, screen readers, captions, or keyboard navigation.",
                dialect=dialect,
                citations=[],
                hits=[],
                latency_ms=int((time.time() - t0) * 1000),
                refused=False,
                meta={"reason": "no_hits"},
            )

        dialect_name = SUPPORTED_DIALECTS.get(dialect, "English")
        context = self._format_context(hits)
        user_msg = RAG_USER_TEMPLATE.format(
            context_blocks=context, dialect_name=dialect_name, question=question
        )

        msg = self.client.messages.create(
            model=self.model,
            max_tokens=700,
            system=RAG_SYSTEM.format(dialect_name=dialect_name),
            messages=[{"role": "user", "content": user_msg}],
        )
        text = msg.content[0].text.strip()
        cites = self._extract_citations(text, hits)
        latency = int((time.time() - t0) * 1000)

        return RAGResponse(
            answer=text,
            dialect=dialect,
            citations=cites,
            hits=hits,
            latency_ms=latency,
            refused=False,
            meta={
                "input_tokens": getattr(msg.usage, "input_tokens", None),
                "output_tokens": getattr(msg.usage, "output_tokens", None),
            },
        )
