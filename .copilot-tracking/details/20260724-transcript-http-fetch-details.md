<!-- markdownlint-disable-file -->

# Task Details: Transcript HTTP Fetch Workflow

## Research Reference

**Source Research**: `.copilot-tracking/research/20260723-transcript-workflow-research.md`

---

## Phase 1: Package Scaffold

### Task 1.1: Create `workflow_transcript/__init__.py`

Create the package init file that exports the `workflow` object, mirroring `workflow_spam/__init__.py`.

```python
# Copyright (c) Microsoft. All rights reserved.

from .workflow import workflow

__all__ = ["workflow"]
```

- **Files**:
  - `workflow_transcript/__init__.py` — package init exporting `workflow`
- **Success**:
  - File exists; `from workflow_transcript import workflow` succeeds
- **Research references**:
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 17–18) — `__init__.py` export pattern
- **Dependencies**:
  - None

---

### Task 1.2: Define data models in `workflow_transcript/workflow.py`

Create `workflow_transcript/workflow.py` with the copyright header, all imports, the `TranscriptRequest` Pydantic model, and the four dataclasses used for inter-executor communication.

```python
# Copyright (c) Microsoft. All rights reserved.

"""Transcript Q&A Workflow — fetches live transcript, detects questions, answers via Second Brain."""

import os
from dataclasses import dataclass, field
from typing import Never

import httpx
from agent_framework import Case, Default, Executor, WorkflowBuilder, WorkflowContext, handler
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing_extensions import Never  # noqa: F811

load_dotenv()


class TranscriptRequest(BaseModel):
    """Trigger the transcript fetch workflow."""

    port: int = Field(
        description="Port of the transcript server. Defaults to TRANSCRIPT_PORT env var or 3001.",
        default_factory=lambda: int(os.environ.get("TRANSCRIPT_PORT", "3001")),
    )


@dataclass
class TranscriptEntry:
    timestamp: str
    source: str
    text: str


@dataclass
class TranscriptData:
    entries: list[TranscriptEntry] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class QuestionDetectionResult:
    transcript_data: TranscriptData
    has_question: bool = False
    question_text: str | None = None


@dataclass
class AnswerResult:
    question: str
    answer: str
```

Note: use `from typing_extensions import Never` if `from typing import Never` is unavailable (Python < 3.11).
Check the existing `workflow_spam/workflow.py` import pattern — it uses `from typing_extensions import Never`.

- **Files**:
  - `workflow_transcript/workflow.py` — created with all imports, models, and dataclasses
- **Success**:
  - File parses without errors; all symbols importable
- **Research references**:
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 44–50) — copyright header, Pydantic `Field`, `@dataclass` convention
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 182–228) — `TranscriptRequest` with `port` field, `TranscriptEntry` response schema
- **Dependencies**:
  - `httpx` (transitive via `openai>=1.97.0`)
  - `agent_framework`, `azure-identity`, `python-dotenv`, `pydantic`, `typing_extensions`

---

## Phase 2: TranscriptReceiver Executor

### Task 2.1: Implement `TranscriptReceiver` in `workflow_transcript/workflow.py`

Add the `TranscriptReceiver` executor class that fetches from `GET http://0.0.0.0:{port}/transcript`, parses the JSON response into `TranscriptData`, and passes it to the next executor.

```python
class TranscriptReceiver(Executor):
    """Step 1: Fetches the live transcript from the Rust REST server."""

    @handler
    async def handle_request(self, request: TranscriptRequest, ctx: WorkflowContext[TranscriptData]) -> None:
        url = f"http://0.0.0.0:{request.port}/transcript"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
            raw = response.json()

        entries = [
            TranscriptEntry(timestamp=e["timestamp"], source=e["source"], text=e["text"])
            for e in raw
        ]
        raw_text = "\n".join(f"[{e.timestamp}] {e.source}: {e.text}" for e in entries)

        await ctx.send_message(TranscriptData(entries=entries, raw_text=raw_text))
```

- **Files**:
  - `workflow_transcript/workflow.py` — append `TranscriptReceiver` class after dataclasses
- **Success**:
  - HTTP GET to `http://0.0.0.0:{port}/transcript` succeeds
  - `TranscriptData.raw_text` is `"[HH:MM:SS.mmm] SOURCE: text\n..."` for all entries
  - `ctx.send_message(TranscriptData(...))` called
- **Research references**:
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 107–112) — non-terminal `@handler` pattern with `ctx.send_message`
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 195–213) — httpx async fetch and response parsing
- **Dependencies**:
  - Task 1.2 completion

---

## Phase 3: QuestionDetector and Terminal Executors

### Task 3.1: Implement `QuestionDetector` in `workflow_transcript/workflow.py`

Add the `QuestionDetector` executor that calls the LLM to detect whether the transcript contains a question.

```python
_QUESTION_DETECT_PROMPT = (
    "You are an assistant that detects questions in meeting transcripts.\n"
    "Analyze the transcript below.\n"
    "If it contains a question, reply with exactly: QUESTION: <question text>\n"
    "If no question is present, reply with exactly: NO_QUESTION\n\n"
    "Transcript:\n{transcript}"
)


class QuestionDetector(Executor):
    """Step 2: Calls the LLM to detect whether the transcript contains a question."""

    @handler
    async def handle_transcript(
        self, data: TranscriptData, ctx: WorkflowContext[QuestionDetectionResult]
    ) -> None:
        client = FoundryChatClient(
            project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
            model=os.environ.get("FOUNDRY_MODEL", "gpt-4o"),
            credential=AzureCliCredential(),
        )
        prompt = _QUESTION_DETECT_PROMPT.format(transcript=data.raw_text)
        response_text = await client.complete([{"role": "user", "content": prompt}])

        if response_text.strip().startswith("QUESTION:"):
            question = response_text.strip()[len("QUESTION:"):].strip()
            result = QuestionDetectionResult(transcript_data=data, has_question=True, question_text=question)
        else:
            result = QuestionDetectionResult(transcript_data=data, has_question=False)

        await ctx.send_message(result)
```

**IMPORTANT**: Verify the `FoundryChatClient.complete()` method signature before implementing.
- Check `agent_framework.foundry` module for the correct method name (`complete`, `chat_completion`, `generate`, etc.)
- The method should accept a list of message dicts and return a string
- Fallback: instantiate an `Agent` with no tools and call `agent.run(prompt)` for a simple completion

- **Files**:
  - `workflow_transcript/workflow.py` — append `_QUESTION_DETECT_PROMPT` constant and `QuestionDetector` class
- **Success**:
  - LLM called with transcript text; response parsed correctly
  - `has_question=True` + `question_text` populated when response starts with `"QUESTION:"`
  - `has_question=False` when response is `"NO_QUESTION"`
- **Research references**:
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 134–146) — `FoundryChatClient` instantiation pattern
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 107–112) — non-terminal `@handler` with `ctx.send_message`
- **Dependencies**:
  - Task 2.1 completion; `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL` env vars; `az login` completed

---

### Task 3.2: Implement `AnswerGenerator` and `SilentTerminator`

Add the two terminal executor classes that handle the branching paths after question detection.

```python
class AnswerGenerator(Executor):
    """Step 3a: Answers the detected question using Second Brain MCP retrieval."""

    @handler
    async def handle_question(
        self, result: QuestionDetectionResult, ctx: WorkflowContext[Never, str]
    ) -> None:
        from agent_framework import Agent, MCPStreamableHTTPTool

        second_brain = MCPStreamableHTTPTool(
            name="sb",
            description="Second Brain knowledge base — semantic and keyword search over markdown notes",
            url="http://localhost:3001/mcp",
        )
        client = FoundryChatClient(
            project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
            model=os.environ.get("FOUNDRY_MODEL", "gpt-4o"),
            credential=AzureCliCredential(),
        )
        answer_agent = Agent(
            name="transcript-answer-agent",
            client=client,
            instructions=(
                "You have access to the Second Brain (sb) tool.\n"
                "For every request, call sb (keyword_search or semantic_search) first, then answer.\n"
                "Use only the tool result to answer. Never answer from memory."
            ),
            tools=[second_brain],
        )
        answer = await answer_agent.run(result.question_text)
        await ctx.yield_output(answer)


class SilentTerminator(Executor):
    """Step 3b: No question detected — terminate gracefully."""

    @handler
    async def handle_no_question(
        self, result: QuestionDetectionResult, ctx: WorkflowContext[Never, str]
    ) -> None:
        await ctx.yield_output("No question detected in transcript.")
```

- **Files**:
  - `workflow_transcript/workflow.py` — append `AnswerGenerator` and `SilentTerminator` classes
- **Success**:
  - `AnswerGenerator.handle_question` calls Second Brain MCP and yields an answer string
  - `SilentTerminator.handle_no_question` yields `"No question detected in transcript."`
  - Both use `ctx.yield_output(...)` (terminal executor pattern)
- **Research references**:
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 95–103) — terminal executor `WorkflowContext[Never, str]` and `ctx.yield_output` pattern
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 21–22) — `MCPStreamableHTTPTool` with Second Brain at `http://localhost:3001/mcp`
- **Dependencies**:
  - Task 3.1 completion; Second Brain MCP running at `http://localhost:3001/mcp`

---

## Phase 4: WorkflowBuilder and Entry Point

### Task 4.1: Wire `WorkflowBuilder` with switch-case branching

Add executor instances and the `WorkflowBuilder` chain at module level after the executor classes.

```python
transcript_receiver = TranscriptReceiver(id="transcript_receiver")
question_detector = QuestionDetector(id="question_detector")
answer_generator = AnswerGenerator(id="answer_generator")
silent_terminator = SilentTerminator(id="silent_terminator")

workflow = (
    WorkflowBuilder(
        name="Transcript Q&A",
        description="Fetches live transcript, detects questions, answers via Second Brain.",
        start_executor=transcript_receiver,
    )
    .add_edge(transcript_receiver, question_detector)
    .add_switch_case_edge_group(
        question_detector,
        [
            Case(
                condition=lambda x: isinstance(x, QuestionDetectionResult) and x.has_question,
                target=answer_generator,
            ),
            Default(target=silent_terminator),
        ],
    )
    .build()
)
```

- **Files**:
  - `workflow_transcript/workflow.py` — append executor instances and `WorkflowBuilder` chain
- **Success**:
  - `workflow` object created without runtime errors
  - `QuestionDetectionResult(has_question=True)` routes to `answer_generator`
  - All other messages (including `has_question=False`) route to `silent_terminator` via `Default`
- **Research references**:
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 119–132) — `WorkflowBuilder` chain with switch-case
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 85–96) — `Case` / `Default` branching pattern
- **Dependencies**:
  - Task 3.2 completion

---

### Task 4.2: Add `main()` function

Append the `main()` function and `if __name__ == "__main__"` guard at the end of `workflow_transcript/workflow.py`.

```python
def main():
    """Launch the Transcript Q&A workflow in DevUI."""
    import logging

    from agent_framework.devui import serve

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    logger.info("Starting Transcript Q&A Workflow")
    logger.info("Available at: http://localhost:8092")
    logger.info("Note: transcript server must be running (default port 3001)")
    logger.info("Note: Second Brain MCP must be running at http://localhost:3001/mcp")

    serve(entities=[workflow], port=8092, auto_open=True)


if __name__ == "__main__":
    main()
```

- **Files**:
  - `workflow_transcript/workflow.py` — append `main()` and `if __name__` guard
- **Success**:
  - `python -m workflow_transcript.workflow` launches DevUI on port 8092
  - Workflow auto-discovered by `main.py` via `serve(entities_dir=...)`
- **Research references**:
  - `.copilot-tracking/research/20260723-transcript-workflow-research.md` (Lines 44–46) — `main()` with `serve(entities=[...], port=..., auto_open=True)` pattern
- **Dependencies**:
  - Task 4.1 completion

---

## Dependencies

- `httpx` — transitive via `openai>=1.97.0`; used for async HTTP GET to transcript server
- `agent_framework` — `Executor`, `WorkflowBuilder`, `WorkflowContext`, `handler`, `Case`, `Default`, `Agent`, `MCPStreamableHTTPTool`
- `agent_framework.foundry.FoundryChatClient` — LLM client for question detection
- `azure-identity` — `AzureCliCredential` for Azure auth
- `pydantic` — `BaseModel`, `Field` for `TranscriptRequest`
- `python-dotenv` — `load_dotenv()` for env var loading
- `typing_extensions` — `Never` (for Python < 3.11 compatibility)

## Success Criteria

- `POST /workflow` with `{}` (or `{"port": 3001}`) fetches transcript, detects question, returns Second Brain answer
- `POST /workflow` with `{}` returns `"No question detected in transcript."` when no question present
- `workflow_transcript` package auto-discovered by `main.py` via `serve(entities_dir=...)`
- Workflow visible in DevUI at `http://localhost:8092`
