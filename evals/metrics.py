import json
import statistics
from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class CaseScore:
    case_id: str
    faithfulness: float
    answer_relevance: float
    citation_precision: float
    refusal_correct: float
    overall: float
    latency_ms: int
    refused: bool
    dialect: str
    notes: str = ""


def citation_precision(cited_docs: List[str], must_cite_docs: List[str]) -> float:
    if not must_cite_docs:
        return 1.0
    if not cited_docs:
        return 0.0
    hits = sum(1 for d in must_cite_docs if d in cited_docs)
    return hits / len(must_cite_docs)


def refusal_correctness(expected_refusal: bool, refused: bool) -> float:
    return 1.0 if expected_refusal == refused else 0.0


def summarize(scores: Iterable[CaseScore]) -> dict:
    scores = list(scores)
    if not scores:
        return {}
    by = lambda k: [getattr(s, k) for s in scores]
    latencies = by("latency_ms")
    return {
        "n": len(scores),
        "faithfulness_mean": round(statistics.mean(by("faithfulness")), 3),
        "answer_relevance_mean": round(statistics.mean(by("answer_relevance")), 3),
        "citation_precision_mean": round(statistics.mean(by("citation_precision")), 3),
        "refusal_accuracy": round(statistics.mean(by("refusal_correct")), 3),
        "overall_mean": round(statistics.mean(by("overall")), 3),
        "latency_p50_ms": int(statistics.median(latencies)),
        "latency_p95_ms": int(sorted(latencies)[max(0, int(0.95 * (len(latencies) - 1)))]),
        "refused_share": round(sum(1 for s in scores if s.refused) / len(scores), 3),
    }


def save_report(path: str, suite_name: str, scores: List[CaseScore], summary: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "suite": suite_name,
                "summary": summary,
                "cases": [s.__dict__ for s in scores],
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
