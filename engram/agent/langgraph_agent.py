import cognee
from cognee import SearchType
from langchain_core.tools import tool


@tool
async def recall_codebase_memory(query: str) -> str:
    """Search Engram's cognee-backed knowledge graph for architectural
    context, call-graph relationships, or past session decisions about
    the codebase."""
    results = await cognee.search(query, query_type=SearchType.GRAPH_COMPLETION)
    if not results:
        return "No relevant memory found."
    return "\n\n".join(str(result) for result in results)
