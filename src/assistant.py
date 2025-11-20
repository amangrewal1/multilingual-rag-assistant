import os
import time
from dataclasses import dataclass, field
from typing import List, Optional

from anthropic import Anthropic

from .rag import RAGPipeline, RAGResponse
from .retriever import Retriever
from .safety import SafetyGate, SafetyVerdict
from .translator import Translator, detect_language, LangGuess


REFUSAL_TEMPLATES = {
    "harmful": "I can't help with that. If you're in crisis, please reach out to local emergency services or a trusted person.",
    "medical_advice": "I can't give medical advice. Please consult a licensed clinician for your specific situation.",
    "legal_advice": "I can't give legal advice. Please consult a qualified attorney for guidance on your situation.",
    "prompt_injection": "I can't follow instructions that override my safety or grounding rules. Ask me an accessibility question instead.",
    "pii_request": "I can't share or extract personal data. Let me know what accessibility topic you'd like help with.",
    "out_of_scope": "That's outside what I'm set up to help with. I can answer questions about accessibility, WCAG, screen readers, captions, and keyboard navigation.",
    "ambiguous": "Could you clarify? I want to make sure I answer the right question.",
}


@dataclass
class AssistantResult:
    answer: str
    detected_dialect: str
    code_switched: bool
    refused: bool
    refusal_category: str
    citations: list
    hits: list
    latency_ms: int
    stages: dict = field(default_factory=dict)


class Assistant:
    def __init__(
        self,
        retriever: Retriever,
        client: Optional[Anthropic] = None,
        model: Optional[str] = None,
    ):
        self.client = client or Anthropic()
        self.model = model or os.getenv("MODEL_ID", "claude-haiku-4-5-20251001")
        self.retriever = retriever
        self.rag = RAGPipeline(self.client, retriever, model=self.model,
                               top_k=int(os.getenv("TOP_K", "4")))
        self.safety = SafetyGate(self.client, model=self.model)
        self.translator = Translator(self.client, model=self.model)

    def _refuse(self, category: str, reason: str, dialect: str, t0: float) -> AssistantResult:
        base = REFUSAL_TEMPLATES.get(category, REFUSAL_TEMPLATES["out_of_scope"])
        msg = base
        if dialect != "en":
            try:
                msg = self.translator.translate(base, source="en", target=dialect)
            except Exception:
                pass
        return AssistantResult(
            answer=msg,
            detected_dialect=dialect,
            code_switched=False,
            refused=True,
            refusal_category=category,
            citations=[],
            hits=[],
            latency_ms=int((time.time() - t0) * 1000),
            stages={"refusal_reason": reason},
        )

    def ask(self, question: str) -> AssistantResult:
        t0 = time.time()
        stages = {}

        lang: LangGuess = detect_language(question, client=self.client, model=self.model)
        stages["lang_detect_ms"] = int((time.time() - t0) * 1000)

        verdict: SafetyVerdict = self.safety.check(question)
        stages["safety_ms"] = int((time.time() - t0) * 1000) - stages["lang_detect_ms"]
        stages["safety_verdict"] = verdict.verdict
        stages["safety_category"] = verdict.category

        if verdict.verdict != "allow":
            return self._refuse(verdict.category, verdict.reason, lang.dialect, t0)

        retrieval_query = self.translator.normalize_for_retrieval(question, source=lang.dialect)
        stages["retrieval_query"] = retrieval_query

        rag_resp: RAGResponse = self.rag.answer(
            question=question, dialect=lang.dialect, retrieval_query=retrieval_query
        )

        return AssistantResult(
            answer=rag_resp.answer,
            detected_dialect=lang.dialect,
            code_switched=lang.code_switched,
            refused=False,
            refusal_category="ok",
            citations=rag_resp.citations,
            hits=rag_resp.hits,
            latency_ms=int((time.time() - t0) * 1000),
            stages=stages,
        )
