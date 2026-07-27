<!-- markdownlint-disable-file -->

# Task Checklist: Transcript HTTP Fetch Workflow

## Overview

Create `workflow_transcript/` package that fetches the live transcript via `GET http://0.0.0.0:{port}/transcript`, detects questions with an LLM, and answers them using Second Brain MCP retrieval.

## Objectives

- Workflow accepts `POST /workflow` with optional `port` (default: `TRANSCRIPT_PORT` env var or `3001`)
- Fetches transcript entries from the Rust `transcript-merger` REST server
- Detects questions in the transcript using `FoundryChatClient`
- Routes to `AnswerGenerator` (Second Brain MCP) when a question is found, or `SilentTerminator` otherwise
- Auto-discovered by `main.py` via `serve(entities_dir=...)`

## Research Summary

### Project Files

- `workflow_spam/workflow.py` — reference implementation for executor and WorkflowBuilder patterns
- `workflow_spam/__init__.py` — reference for `__init__.py` export pattern
- `67_agent/agent.py` — `Agent`, `MCPStreamableHTTPTool`, `FoundryChatClient`, `AzureCliCredential` usage
- `../../../rust/transcript-merger/src/main.rs` — Rust REST server: `GET /transcript` returns `Vec<Entry>` as JSON

### External References

- `.copilot-tracking/research/20260723-transcript-workflow-research.md` — workflow framework patterns, FoundryChatClient usage, WorkflowBuilder chain
- `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 181–228) — transcript server API, response schema, httpx fetch pattern, updated `TranscriptRequest`

## Implementation Checklist

### [x] Phase 1: Package Scaffold

- [x] Task 1.1: Create `workflow_transcript/__init__.py` with `workflow` export
  - Details: `.copilot-tracking/details/20260724-transcript-http-fetch-details.md` (Lines 13–34)

- [x] Task 1.2: Create `workflow_transcript/workflow.py` with imports, `TranscriptRequest`, and dataclasses
  - Details: `.copilot-tracking/details/20260724-transcript-http-fetch-details.md` (Lines 36–111)

### [x] Phase 2: TranscriptReceiver Executor

- [x] Task 2.1: Implement `TranscriptReceiver` — fetch `GET /transcript`, parse JSON, pass `TranscriptData`
  - Details: `.copilot-tracking/details/20260724-transcript-http-fetch-details.md` (Lines 113–152)

### [x] Phase 3: QuestionDetector and Terminal Executors

- [x] Task 3.1: Implement `QuestionDetector` — LLM call to detect question in transcript
  - Details: `.copilot-tracking/details/20260724-transcript-http-fetch-details.md` (Lines 154–209)

- [x] Task 3.2: Implement `AnswerGenerator` (Second Brain MCP) and `SilentTerminator`
  - Details: `.copilot-tracking/details/20260724-transcript-http-fetch-details.md` (Lines 211–273)

### [x] Phase 4: WorkflowBuilder and Entry Point

- [x] Task 4.1: Wire `WorkflowBuilder` with switch-case branching on `QuestionDetectionResult.has_question`
  - Details: `.copilot-tracking/details/20260724-transcript-http-fetch-details.md` (Lines 275–318)

- [x] Task 4.2: Add `main()` function with `serve(entities=[workflow], port=8092, auto_open=True)`
  - Details: `.copilot-tracking/details/20260724-transcript-http-fetch-details.md` (Lines 320–355)

## Dependencies

- `httpx` (transitive via `openai>=1.97.0`)
- `agent_framework` (`Executor`, `WorkflowBuilder`, `WorkflowContext`, `handler`, `Case`, `Default`, `Agent`, `MCPStreamableHTTPTool`)
- `agent_framework.foundry.FoundryChatClient`
- `azure-identity` (`AzureCliCredential`)
- `pydantic` (`BaseModel`, `Field`)
- `python-dotenv`
- `typing_extensions` (`Never`)
- Rust `transcript-merger` running (default port `3001`)
- Second Brain MCP running at `http://localhost:3001/mcp`
- `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL` env vars set
- `az login` completed

## Success Criteria

- `POST /workflow` with `{}` fetches live transcript, returns Second Brain answer when question detected
- `POST /workflow` with `{}` returns `"No question detected in transcript."` when no question present
- `workflow_transcript` package auto-discovered by `main.py`
- Workflow visible in DevUI at `http://localhost:8092`
