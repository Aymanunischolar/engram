import asyncio
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from pathlib import Path

import cognee
from cognee import SearchType
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from engram.ingest.code_parser import ingest_repo
from engram.memory import config  # noqa: F401

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ingest_lock = asyncio.Lock()
_ingested = False
_ingest_error: str | None = None

_RATE_LIMIT_WINDOW_S = 60
_RATE_LIMIT_MAX_REQUESTS = 5
_request_log: dict[str, list[float]] = defaultdict(list)


async def _ensure_ingested() -> None:
    global _ingested, _ingest_error
    if _ingested:
        return
    async with _ingest_lock:
        if _ingested:
            return
        try:
            await ingest_repo(REPO_ROOT / "engram")
            readme = REPO_ROOT / "README.md"
            if readme.exists():
                await cognee.add(str(readme))
            await cognee.cognify()
            _ingested = True
        except Exception as e:
            _ingest_error = str(e)
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(_ensure_ingested())
    yield


app = FastAPI(title="Engram API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    ready: bool = True


def _check_rate_limit(client_ip: str) -> None:
    now = time.time()
    recent = [t for t in _request_log[client_ip] if now - t < _RATE_LIMIT_WINDOW_S]
    if len(recent) >= _RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Too many requests - please wait a minute.")
    recent.append(now)
    _request_log[client_ip] = recent


@app.get("/")
async def root():
    return {
        "name": "Engram API",
        "description": "Persistent, graph-native engineering memory for AI coding agents.",
        "endpoints": {
            "POST /ask": "ask a question about this codebase",
            "GET /health": "health check",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok", "ingested": _ingested, "ingest_error": _ingest_error}


@app.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    if not _ingested:
        if _ingest_error:
            raise HTTPException(
                status_code=503, detail=f"Startup ingestion failed: {_ingest_error}"
            )
        return AskResponse(
            answer="Still warming up (ingesting Engram's own codebase) - try again in a few seconds.",
            ready=False,
        )

    try:
        results = await cognee.search(payload.question, query_type=SearchType.GRAPH_COMPLETION)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Search temporarily unavailable: {e}") from e

    if not results:
        return AskResponse(answer="No relevant memory found for that question.")
    return AskResponse(answer=" ".join(str(r) for r in results))
