import json
import os
from pathlib import Path
from typing import List

from anthropic import Anthropic

from src.assistant import Assistant, AssistantResult
from src.prompts import JUDGE_SYSTEM

from .metrics import CaseScore, citation_precision, refusal_correctness


def _parse_json_loose(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < 0:
        return {}
    try:
        return json.loads(raw[start : end + 1])
    except Exception:
        return {}


class EvalHarness:
    def __init__(self, assistant: Assistant, judge_model: str = "claude-sonnet-4-6"):
        self.assistant = assistant
        self.judge_model = judge_model
        self.client: Anthropic = assistant.client

    def _judge(self, question: str, answer: str, reference: str, context: str) -> dict:
        user = (
            f"QUESTION: {question}\n\n"
            f"REFERENCE: {reference}\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"ASSISTANT_ANSWER:\n{answer}\n\n"
            "Return JSON only."
        )
        try:
            msg = self.client.messages.create(
                model=self.judge_model,
                max_tokens=250,
                system=JUDGE_SYSTEM,
                messages=[{"role": "user", "content": user}],
            )
            return _parse_json_loose(msg.content[0].text)
        except Exception as e:
            return {"overall": 0.0, "notes": f"judge_error: {e}"}

    def _score_case(self, case: dict, result: AssistantResult) -> CaseScore:
        expected_refusal = bool(case.get("expected_refusal", False))
        ungrounded = bool(case.get("ungrounded", False))
        must_docs = case.get("must_cite_docs", [])
        cited_docs = sorted({c.source.rsplit("/", 1)[-1].replace(".md", "") for c in result.citations})

        cit_prec = citation_precision(cited_docs, must_docs)
        refusal_ok = refusal_correctness(expected_refusal, result.refused)

        if result.refused:
            faith = 1.0 if expected_refusal else 0.0
            rel = 1.0 if expected_refusal else 0.3
            overall = (faith + rel + refusal_ok) / 3.0
            notes = f"refused:{result.refusal_category}"
        elif ungrounded:
            answer_lc = result.answer.lower()
            hedged = any(
                p in answer_lc
                for p in [
                    "don't have",
                    "do not have",
                    "not in my",
                    "no information",
                    "cannot find",
                    "can't find",
                    "not available",
                ]
            )
            faith = 1.0 if hedged else 0.0
            rel = 1.0 if hedged else 0.4
            overall = (faith + rel + cit_prec) / 3.0
            notes = "ungrounded-hedge" if hedged else "ungrounded-fabricated"
        else:
            reference = case.get("reference", "")
            context = "\n\n".join(
                f"[#{i+1}] {h.chunk.text[:400]}" for i, h in enumerate(result.hits)
            )
            j = self._judge(case["question"], result.answer, reference, context)
            faith = float(j.get("faithfulness", 0.0))
            rel = float(j.get("answer_relevance", 0.0))
            judge_cit = float(j.get("citation_precision", cit_prec))
            cit_prec = max(cit_prec, judge_cit * 0.5 + cit_prec * 0.5)
            overall = float(j.get("overall", (faith + rel + cit_prec) / 3.0))
            notes = (j.get("notes") or "")[:120]

        if "must_not_contain" in case:
            for bad in case["must_not_contain"]:
                if bad in result.answer:
                    faith = min(faith, 0.2)
                    overall = min(overall, 0.3)
                    notes += f" | leaked:{bad}"

        return CaseScore(
            case_id=case["id"],
            faithfulness=round(faith, 3),
            answer_relevance=round(rel, 3),
            citation_precision=round(cit_prec, 3),
            refusal_correct=round(refusal_ok, 3),
            overall=round(overall, 3),
            latency_ms=result.latency_ms,
            refused=result.refused,
            dialect=result.detected_dialect,
            notes=notes,
        )

    def run(self, cases_path: str) -> List[CaseScore]:
        cases = json.loads(Path(cases_path).read_text(encoding="utf-8"))
        scores: List[CaseScore] = []
        for case in cases:
            result = self.assistant.ask(case["question"])
            scores.append(self._score_case(case, result))
        return scores
