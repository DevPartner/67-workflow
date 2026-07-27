# 67 Meeting Assistant

An AI-powered meeting assistant built on the [Agent Framework](https://github.com/microsoft/agent-framework) with DevUI. It provides two entities served as OpenAI-compatible REST endpoints:

- **67 Assistant** — a chat agent that answers questions by searching your Second Brain knowledge base
- **Transcript Q&A** — a workflow that fetches a live meeting transcript, detects whether it contains a question, and answers it using Second Brain

## Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                      DevUI (port 8080)                  │
│  ┌─────────────────────┐  ┌──────────────────────────┐  │
│  │    67 Assistant     │  │   Transcript Q&A         │  │
│  │    (67_agent/)      │  │   (workflow_transcript/) │  │
│  └──────────┬──────────┘  └────────────┬─────────────┘  │
└─────────────┼──────────────────────────┼────────────────┘
              │                          │
              │              ┌───────────┴────────────┐
              │              │  Transcript Server     │
              │              │  (Rust, :3000)         │
              │              └────────────────────────┘
              │
    ┌─────────┴──────────┐
    │  Azure AI Foundry  │
    │  + Second Brain    │
    │  MCP (:3001)       │
    └────────────────────┘
```

### 67 Assistant (`67_agent/`)

A chat agent backed by Azure AI Foundry that enforces retrieval-first answers. Every response must start with a Second Brain search — the agent's middleware hard-blocks any response that skips this step.

### Transcript Q&A (`workflow_transcript/`)

A four-step workflow:

1. **TranscriptReceiver** — fetches the live transcript from the Rust server (`GET :{port}/transcript`)
2. **QuestionDetector** — asks the LLM whether the transcript contains a question
3. **AnswerGenerator** _(question path)_ — calls Second Brain MCP to answer the detected question
4. **SilentTerminator** _(no-question path)_ — returns `"No question detected in transcript."`

## Prerequisites

- Python 3.12+
- [Agent Framework](https://github.com/microsoft/agent-framework) with DevUI (`agent-framework-devui`)
- Azure CLI authenticated: `az login`
- Second Brain MCP server running at `http://localhost:3001/mcp`
- Rust transcript server running (default port `3000`) for the Transcript Q&A workflow

## Setup

1. Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
FOUNDRY_PROJECT_ENDPOINT=https://<resource>.services.ai.azure.com/api/projects/<project>
FOUNDRY_MODEL=gpt-4o

TRANSCRIPT_BASE_URL=http://localhost
TRANSCRIPT_PORT=3000
```

2. Authenticate with Azure:

```bash
az login
```

## Running

### All entities (recommended)

Starts DevUI on port 8080 and auto-discovers both the agent and the workflow:

```bash
python main.py
```

DevUI opens at `http://localhost:8080` with both entities listed.

### Individual entities

**67 Assistant only** (port 8091):

```bash
python -m 67_agent.agent
```

**Transcript Q&A workflow only** (port 8092):

```bash
python -m workflow_transcript.workflow
```

### In-memory demo

`in_memory_mode.py` shows programmatic entity registration without directory discovery — useful as a minimal reference for building your own DevUI setup:

```bash
python in_memory_mode.py
```

## API Usage

DevUI exposes OpenAI-compatible endpoints. List available entities:

```bash
curl http://localhost:8080/v1/entities
```

Trigger the Transcript Q&A workflow:

```bash
curl -X POST http://localhost:8080/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "agent-framework",
    "input": "{}",
    "extra_body": {
      "entity_id": "<workflow-entity-id>",
      "data": {"port": 3000}
    }
  }'
```

The workflow POST body accepts:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `port` | `int` | `TRANSCRIPT_PORT` env or `3000` | Port of the running transcript server |
| `base_url` | `str` | `TRANSCRIPT_BASE_URL` env or `http://localhost` | Base URL of the transcript server |

## Project Structure

```text
67-workflow/
├── main.py                     # Launch DevUI with auto-discovery (port 8080)
├── in_memory_mode.py           # Minimal example of programmatic entity registration
├── subprocess_script_runner.py # Skill script runner for file-based skills
├── .env.example                # Shared environment variable template
├── 67_agent/
│   ├── agent.py                # 67 Assistant definition + SbToolRequiredMiddleware
│   ├── __init__.py
│   ├── .env.example
│   └── skills/
│       └── second-brain/
│           └── SKILL.md        # sb MCP tool usage rules injected into agent instructions
└── workflow_transcript/
    ├── workflow.py             # All executors + WorkflowBuilder wiring
    └── __init__.py
```

## Second Brain MCP Tools

The `sb` tool exposes three operations used by both the agent and the workflow:

| Tool | Best for |
|------|----------|
| `keyword_search` | Exact names, titles, code identifiers, acronyms |
| `semantic_search` | Concepts, ideas, natural-language questions |
| `get_document` | Full document by ID from a prior search result |

> [!NOTE]
> The agent enforces a hard limit of two `sb` calls per turn: one search (keyword or semantic) plus an optional `get_document`. Retrying with different parameters is not allowed.

## Troubleshooting

**`az login` required** — Both the agent and workflow use `AzureCliCredential`. Run `az login` before starting.

**Second Brain MCP not reachable** — Ensure the MCP server is running at `http://localhost:3001/mcp` before starting the agent or the `AnswerGenerator` step of the workflow.

**Transcript server not running** — The Transcript Q&A workflow will fail at step 1 if `GET :{port}/transcript` is unreachable. Start the Rust transcript server first.

**Port conflicts** — Default ports are 8080 (main), 8091 (agent standalone), 8092 (workflow standalone). Adjust in the respective `main()` calls if another service occupies them.
