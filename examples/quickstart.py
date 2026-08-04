import asyncio
from pathlib import Path

import cognee

from engram.memory import config  # noqa: F401  (validates LLM_API_KEY on import)


async def main():
    readme = Path(__file__).resolve().parent.parent / "README.md"
    await cognee.add(str(readme))
    await cognee.cognify()

    results = await cognee.search("What is Engram built on, and why does that matter?")
    for result in results:
        print(result)

    graph_html = Path(__file__).resolve().parent / "graph.html"
    await cognee.visualize_graph(destination_file_path=str(graph_html))
    print(f"\nGraph visualization written to {graph_html}")
    print("Open it directly in a browser -- no server required.")


if __name__ == "__main__":
    asyncio.run(main())
