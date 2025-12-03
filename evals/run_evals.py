import argparse
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.assistant import Assistant
from src.retriever import Retriever
from evals.harness import EvalHarness
from evals.metrics import summarize, save_report


SUITES = {
    "golden": "data/evals/golden_set.json",
    "regression": "data/evals/regression.json",
    "red_team": "data/evals/red_team.json",
}


def build_assistant() -> Assistant:
    load_dotenv()
    embed_model = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    retriever = Retriever(embed_model=embed_model)
    index_path = "data/index"
    if Path(index_path + ".npy").exists():
        retriever.load(index_path)
    else:
        retriever.index_directory("data/knowledge_base")
        retriever.save(index_path)
    client = Anthropic()
    return Assistant(retriever=retriever, client=client)


def print_summary(console: Console, suite: str, summary: dict) -> None:
    table = Table(title=f"{suite} -- {summary.get('n', 0)} cases")
    table.add_column("metric")
    table.add_column("value", justify="right")
    for k, v in summary.items():
        table.add_row(k, str(v))
    console.print(table)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", choices=list(SUITES) + ["all"], default="all")
    parser.add_argument("--out", default="data/eval_reports")
    args = parser.parse_args()

    console = Console()
    Path(args.out).mkdir(parents=True, exist_ok=True)
    assistant = build_assistant()
    harness = EvalHarness(assistant=assistant,
                          judge_model=os.getenv("JUDGE_MODEL_ID", "claude-sonnet-4-6"))

    suites = SUITES if args.suite == "all" else {args.suite: SUITES[args.suite]}

    for name, path in suites.items():
        console.rule(f"[bold cyan]Running suite: {name}")
        scores = harness.run(path)
        summary = summarize(scores)
        report_path = Path(args.out) / f"{name}.json"
        save_report(str(report_path), name, scores, summary)
        print_summary(console, name, summary)
        console.print(f"[green]report -> {report_path}")


if __name__ == "__main__":
    main()
