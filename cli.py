import argparse
import os
import sys
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.assistant import Assistant
from src.retriever import Retriever


def load_assistant(rebuild: bool = False) -> Assistant:
    load_dotenv()
    embed_model = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    retriever = Retriever(embed_model=embed_model)
    idx = "data/index"
    if rebuild or not Path(idx + ".npy").exists():
        n = retriever.index_directory("data/knowledge_base")
        retriever.save(idx)
        print(f"[index] built {n} chunks -> {idx}")
    else:
        retriever.load(idx)
    return Assistant(retriever=retriever, client=Anthropic())


def ask_once(asst: Assistant, q: str, console: Console) -> None:
    res = asst.ask(q)
    if res.refused:
        console.print(Panel.fit(res.answer, title=f"[red]REFUSED ({res.refusal_category})",
                                border_style="red"))
        return
    body = res.answer
    if res.citations:
        body += "\n\n" + "\n".join(
            f"  [#{c.index}] {c.title} ({c.source}) -- {c.excerpt}" for c in res.citations
        )
    console.print(Panel.fit(
        body,
        title=f"[cyan]{res.detected_dialect}{'* (code-switched)' if res.code_switched else ''} -- {res.latency_ms}ms",
        border_style="cyan",
    ))


def repl(asst: Assistant, console: Console) -> None:
    console.print("[bold]Multilingual Accessibility Assistant[/bold] -- Ctrl+C to exit")
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nbye")
            return
        if not q:
            continue
        ask_once(asst, q, console)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--q", help="one-shot question")
    parser.add_argument("--rebuild-index", action="store_true")
    args = parser.parse_args()
    console = Console()
    asst = load_assistant(rebuild=args.rebuild_index)
    if args.q:
        ask_once(asst, args.q, console)
    else:
        repl(asst, console)


if __name__ == "__main__":
    main()
