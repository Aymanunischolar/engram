import asyncio
from pathlib import Path

import cognee
import yaml
from cognee import SearchType

from engram.memory import config  # noqa: F401  (validates LLM_API_KEY on import)

QUESTIONS_PATH = Path(__file__).parent / "questions.yaml"
RESULTS_PATH = Path(__file__).parent / "results.md"


async def ask(question: str, query_type: SearchType) -> str:
    results = await cognee.search(question, query_type=query_type)
    if not results:
        return "(no results)"
    return " ".join(str(r) for r in results)


def _sanitize(answer: str) -> str:
    return answer.replace("\n", " ").replace("|", "\\|")


async def main():
    questions = yaml.safe_load(QUESTIONS_PATH.read_text(encoding="utf-8"))

    rows = []
    for item in questions:
        print(f"\n=== {item['id']}: {item['question']} ===")

        graph_answer = await ask(item["question"], SearchType.GRAPH_COMPLETION)
        print(f"[GRAPH_COMPLETION] {graph_answer}")

        vector_answer = await ask(item["question"], SearchType.RAG_COMPLETION)
        print(f"[RAG_COMPLETION]   {vector_answer}")

        rows.append((item["id"], item["question"], graph_answer, vector_answer))

    lines = [
        "# Engram eval: GRAPH_COMPLETION vs RAG_COMPLETION",
        "",
        "Target repo: Engram itself.",
        "",
        "| id | question | graph_completion | rag_completion (vector baseline) |",
        "|---|---|---|---|",
    ]
    for row_id, question, graph_answer, vector_answer in rows:
        lines.append(
            f"| {row_id} | {question} | {_sanitize(graph_answer)} | {_sanitize(vector_answer)} |"
        )

    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nResults written to {RESULTS_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
