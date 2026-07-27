<!-- markdownlint-disable-file -->
# Release Changes: Transcript HTTP Fetch Workflow

**Related Plan**: `20260724-transcript-http-fetch-plan.md`
**Implementation Date**: 2026-07-24

## Summary

Created the `workflow_transcript` package that triggers via `POST /workflow`, fetches the live transcript from `GET http://0.0.0.0:{port}/transcript`, detects questions with an LLM, and answers them via Second Brain MCP retrieval.

## Changes

### Added

- `workflow_transcript/__init__.py` — package init exporting the `workflow` object
- `workflow_transcript/workflow.py` — full workflow: `TranscriptRequest`, data models, `TranscriptReceiver`, `QuestionDetector`, `AnswerGenerator`, `SilentTerminator`, `WorkflowBuilder` chain, and `main()`

### Modified

- `.copilot-tracking/research/20260723-transcript-workflow-research.md` — appended transcript server API section: response schema, httpx fetch pattern, updated `TranscriptRequest` with `port` field

## Divergences from Plan

- `FoundryChatClient.complete()` does not exist; used `client.get_response([Message("user", [prompt])])` instead — the public API is `get_response()` returning an awaitable `ChatResponse` with a `.text` property.
- `AnswerResult` dataclass omitted — not needed in the final workflow; `AnswerGenerator` passes the answer string directly to `ctx.yield_output()`.

## Release Summary

**Total Files Affected**: 3

### Files Created (2)

- `workflow_transcript/__init__.py` — package init
- `workflow_transcript/workflow.py` — full workflow implementation

### Files Modified (1)

- `.copilot-tracking/research/20260723-transcript-workflow-research.md` — transcript server API added

### Dependencies & Infrastructure

- **New dependencies**: none (`httpx` available transitively via `openai>=1.97.0`)
- **Runtime prerequisites**: Rust `transcript-merger` running on `TRANSCRIPT_PORT` (default 3001); Second Brain MCP at `http://localhost:3001/mcp`; `FOUNDRY_PROJECT_ENDPOINT` + `FOUNDRY_MODEL` env vars; `az login` completed

### Deployment Notes

Workflow is auto-discovered by `main.py` via `serve(entities_dir=...)`. To run standalone: `python -m workflow_transcript.workflow` → DevUI at `http://localhost:8092`.
