<!-- markdownlint-disable-file -->

# Task Research Notes: Transcript Processing Workflow

## Research Executed

### File Analysis

- `workflow_spam/workflow.py`
  - Full 4-step workflow using `Executor`, `WorkflowBuilder`, `@handler`, `@response_handler`, `WorkflowContext`, `Case`, `Default`
  - Entry point is a Pydantic `BaseModel` received by the first executor's `@handler` method — this becomes the REST API body for `POST /workflow`
  - Branching via `.add_switch_case_edge_group()` with `Case(condition=lambda)` and `Default`
  - Terminal executor uses `WorkflowContext[Never, str]` and `await ctx.yield_output(result)`
  - Non-terminal executors use `await ctx.send_message(result)` to pass data to next step
  - HIL (human-in-the-loop) via `await ctx.request_info(request_data=..., response_type=...)` — not needed here

- `workflow_spam/__init__.py`
  - Exports only `workflow` object — follows the pattern `from .workflow import workflow`

- `67_agent/agent.py`
  - `Agent` instance using `FoundryChatClient` + `MCPStreamableHTTPTool` for Second Brain MCP at `http://localhost:3001/mcp`
  - Exposes `agent` object imported by `__init__.py`
  - Uses `AzureCliCredential`, `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL` env vars

- `main.py`
  - `serve(entities_dir=str(samples_dir), auto_open=True)` — auto-discovers entities from all sub-packages
  - Each sub-package (`workflow_spam/`, `67_agent/`) is discovered as a separate entity

- `in_memory_mode.py`
  - Shows `Agent.run()` is not called directly — agents are served via DevUI endpoints
  - Confirms `WorkflowBuilder` pattern with `start_executor`, `.add_edge()`, `.build()`

### Code Search Results

- `WorkflowContext` generic signature
  - `WorkflowContext[OutputType]` for non-terminal; `WorkflowContext[Never, FinalOutputType]` for terminal
- `@handler` / `@response_handler`
  - `@handler` receives messages from previous executor; `@response_handler` handles HIL responses
- `ctx.send_message` / `ctx.yield_output`
  - `send_message` passes result to next executor; `yield_output` ends the workflow and returns to caller

### Project Conventions

- Folder name pattern: `workflow_<name>` → new folder: **`workflow_transcript`**
- `__init__.py` exports single entity (`workflow` or `agent`)
- `main()` function in each module runs `serve(entities=[...], port=..., auto_open=True)`
- Pydantic `BaseModel` with `Field(description=..., default=...)` for REST request bodies
- `@dataclass` for internal data passing between executors
- `# Copyright (c) Microsoft. All rights reserved.` header on all files

## Key Discoveries

### Project Structure

```
second_brain_search_client/
├── workflow_spam/          ← reference implementation
│   ├── __init__.py         ← exports `workflow`
│   └── workflow.py         ← all executors + WorkflowBuilder
├── 67_agent/               ← agent to call for LLM tasks
│   ├── __init__.py         ← exports `agent`
│   └── agent.py            ← Agent with sb MCP tool
├── workflow_transcript/    ← NEW (to create)
│   ├── __init__.py
│   └── workflow.py
└── main.py                 ← auto-discovers all sub-packages
```

### Implementation Patterns

**REST API entry point** — the `@handler` of `start_executor` defines the POST body:
```python
class TranscriptRequest(BaseModel):
    transcript: str = Field(description="The transcript text to process.", default="")
```
DevUI auto-generates `POST /workflow` accepting this model.

**Calling the 67 agent from a workflow executor** — import and use the agent's underlying `FoundryChatClient` directly (not the `Agent` object, which is a DevUI entity). Two approaches exist:

- **Approach A (recommended)**: Create a dedicated `FoundryChatClient` inside the executor and call it directly for both question detection and answer generation. The 67 agent's MCP tool (`sb`) handles retrieval; the executor sends the transcript as a user message.
- **Approach B**: Import `67_agent.agent` and call it via the agent_framework's run API — tighter coupling, requires the agent's DevUI to be running.

Approach A is cleaner: the workflow executor owns its own LLM client, passes the transcript as the user message, and the agent's `INSTRUCTIONS` + `SKILL.md` content govern the response.

**Branching — question detected vs not**:
```python
.add_switch_case_edge_group(
    question_detector,
    [
        Case(condition=lambda x: isinstance(x, QuestionDetectionResult) and x.has_question, target=answer_generator),
        Default(target=silent_terminator),
    ],
)
```

**Terminal executor** when no question detected — yield empty/acknowledgement output:
```python
class SilentTerminator(Executor):
    @handler
    async def handle(self, result: QuestionDetectionResult, ctx: WorkflowContext[Never, str]) -> None:
        await ctx.yield_output("No question detected in transcript.")
```

### Complete Examples

```python
# Non-terminal executor passing data forward
@handler
async def handle_transcript(self, request: TranscriptRequest, ctx: WorkflowContext[QuestionDetectionResult]) -> None:
    result = QuestionDetectionResult(transcript=request.transcript, has_question=False, question_text=None)
    await ctx.send_message(result)

# Terminal executor
@handler
async def handle_answer(self, result: AnswerResult, ctx: WorkflowContext[Never, str]) -> None:
    await ctx.yield_output(result.answer)
```

### API and Schema Documentation

**WorkflowBuilder chain**:
```python
workflow = (
    WorkflowBuilder(name="...", description="...", start_executor=transcript_receiver)
    .add_edge(transcript_receiver, question_detector)
    .add_switch_case_edge_group(question_detector, [
        Case(condition=lambda x: isinstance(x, QuestionDetectionResult) and x.has_question, target=answer_generator),
        Default(target=silent_terminator),
    ])
    .build()
)
```

**FoundryChatClient for LLM calls inside executor**:
```python
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential

client = FoundryChatClient(
    project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
    model=os.environ.get("FOUNDRY_MODEL", "gpt-4o"),
    credential=AzureCliCredential(),
)
```

Exact method for calling the client from inside an executor needs to be confirmed — the `Agent` wraps client calls, but a raw `FoundryChatClient` call for a single prompt is the right pattern for the question-detection step.

### Technical Requirements

- `FOUNDRY_PROJECT_ENDPOINT` and `FOUNDRY_MODEL` env vars (same as `67_agent`)
- Second Brain MCP server at `http://localhost:3001/mcp` must be running for answer generation
- `az login` must be completed for `AzureCliCredential`
- The workflow is auto-discovered by `main.py` via `serve(entities_dir=...)`

## Recommended Approach

**3-step workflow in `workflow_transcript/workflow.py`**:

1. **`TranscriptReceiver`** (`start_executor`) — receives `TranscriptRequest` (POST body), passes `TranscriptData` dataclass to next step. Minimal processing.

2. **`QuestionDetector`** — calls LLM (`FoundryChatClient`) with the transcript, asks "Does this transcript contain a question? Reply YES or NO and extract the question text if yes." Produces `QuestionDetectionResult(has_question: bool, question_text: str | None, transcript: str)`.

3. **`AnswerGenerator`** (question path) — calls the `67_agent.agent` (or its underlying client) with the detected question + transcript context. Uses Second Brain MCP for retrieval. Produces `AnswerResult(answer: str)` → `yield_output`.

4. **`SilentTerminator`** (no-question path) — `yield_output("No question detected.")`.

Folder name: **`workflow_transcript`** — mirrors `workflow_spam`, simple and consistent.

## Implementation Guidance

- **Objectives**: REST-accessible workflow that detects questions in transcripts and answers them using Second Brain
- **Key Tasks**:
  1. Create `workflow_transcript/` folder with `__init__.py` and `workflow.py`
  2. Define `TranscriptRequest` (Pydantic), `TranscriptData`, `QuestionDetectionResult`, `AnswerResult` dataclasses
  3. Implement `TranscriptReceiver`, `QuestionDetector`, `AnswerGenerator`, `SilentTerminator` executors
  4. Wire `WorkflowBuilder` with switch-case branching after `QuestionDetector`
  5. Add `main()` with `serve(entities=[workflow], port=8092, auto_open=True)`
- **Dependencies**: `agent_framework`, `pydantic`, `azure-identity`, `python-dotenv`; Second Brain MCP at `http://localhost:3001/mcp`; `FOUNDRY_PROJECT_ENDPOINT` + `FOUNDRY_MODEL` env vars
- **Success Criteria**: `POST /workflow` with `{}` or `{"port": 3001}` returns an answer when a question is present, and "No question detected." otherwise; workflow visible in DevUI auto-discovery via `main.py`

## Transcript Server API (Rust)

**Source file**: `../../../rust/transcript-merger/src/main.rs`

### REST Endpoint

`GET http://0.0.0.0:{port}/transcript` — returns full transcript history as JSON array.

**Response schema**:
```json
[
  {"timestamp": "14:30:00.123", "source": "MIC", "text": "Hello there"},
  {"timestamp": "14:30:01.456", "source": "SPEAKER", "text": "What do you mean?"}
]
```

Fields:
- `timestamp`: formatted as `%H:%M:%S%.3f` (e.g. `"14:30:00.123"`)
- `source`: `"MIC"` (microphone input) or `"SPEAKER"` (system audio)
- `text`: transcribed text fragment

### Port Configuration

Rust server port is set via `PORT` env var (default `3001`). Python workflow reads `TRANSCRIPT_PORT` env var (same service) with default `3001`.

### Python HTTP Fetch Pattern

Use `httpx` — available transitively via `openai>=1.97.0`:

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(f"http://0.0.0.0:{port}/transcript", timeout=10.0)
    response.raise_for_status()
    raw_entries = response.json()  # list[dict]
```

### Transcript Formatting

Format entries into a readable string for LLM processing:
```python
raw_text = "\n".join(f"[{e['timestamp']}] {e['source']}: {e['text']}" for e in raw_entries)
```

### Updated `TranscriptRequest` Model

The POST body accepts `port` (not `transcript` text) — the workflow fetches its own transcript:
```python
class TranscriptRequest(BaseModel):
    port: int = Field(
        description="Port of the transcript server. Defaults to TRANSCRIPT_PORT env var or 3001.",
        default_factory=lambda: int(os.environ.get("TRANSCRIPT_PORT", "3001")),
    )
```
