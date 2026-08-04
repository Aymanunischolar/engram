# Engram

Persistent, graph-native engineering memory for AI coding agents — built on [cognee](https://github.com/topoteretes/cognee).

> Early scaffolding stage. Architecture notes, usage docs, and eval results will land here as each build tier completes.

## Live demo

- UI: https://engram-navy.vercel.app
- API: https://engram-api-6dxu.onrender.com

Both ingest and query Engram's own codebase on first request. Running on free tiers: the API cold-starts after inactivity (~50s), and shared LLM quota means it may occasionally be rate-limited — if so, the error message will say so explicitly rather than fail silently.

## What this is

Engram gives a coding agent cross-session memory of a real codebase: not just "what's in this file," but what calls what, what changed and why, and what was already tried and rejected in a past session. It's built on cognee's graph-native memory pipeline (`add` → `cognify` → `memify` → `search`), exposed both as a LangGraph agent tool and as an MCP server for direct use from Claude Code or any other MCP client.

## Status

Following a tiered build plan (weekend MVP → solid core → production polish). This README will be rewritten into a full technical writeup, including an eval comparing graph-completion retrieval against a plain-vector baseline, once there's a working pipeline to report on.

## License

MIT — see [LICENSE](LICENSE).
