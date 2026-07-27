# Tasks: Local AI Meeting Assistant "67" with Second Brain MCP

**Source Spec**: `67_agent.promt.md`
**Target Directory**: `samples/02-agents/devui/67_agent/`
**DevUI Discovery**: Auto-discovered by `devui/main.py`

## Project Layout

```
67_agent/
├── __init__.py      # Must export: agent = ...
├── agent.py         # Agent implementation — single file, follows agent_foundry/agent.py pattern
└── .env.example     # Environment variable reference
```

> **Key decision**: The MCP server (`sb.cmd mcp`) handles all semantic, keyword, and hybrid
> search internally. No separate retrieval or prompt-builder files are needed. The agent
> passes meeting transcript in the user message; the model calls MCP tools autonomously.

---

## Phase 1: Setup

**Purpose**: Scaffold the three files

- [x] T001 Create `67_agent/__init__.py` — single line: `from .agent import agent as agent  # noqa: F401`
- [x] T002 Create `67_agent/.env.example` — add `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL` (defaults to `gpt-4o`) with comments; include optional `# PROVIDER=local` for FoundryLocalClient fallback

---

## Phase 2: Agent Implementation (US1 + US2 + US3 combined) 🎯 MVP

**Goal**: A single `agent.py` that:
- Connects to Remote Foundry (FoundryChatClient + AzureCliCredential)
- Attaches the second-brain MCP server (MCPStdioTool → sb.cmd mcp)
- Carries the full meeting-assistant system prompt from the spec
- Is discoverable by DevUI and runnable standalone

**Independent Test**: Run `devui/main.py` → `"67MeetingAssistant"` appears in sidebar.
Paste the example transcript ending with `"What is .NET MVC?"` → agent answers with a grounded response citing knowledge sources; does NOT summarize the full transcript.

### Implementation

- [x] T003 [US1] Implement `67_agent/agent.py` following `agent_foundry/agent.py` exactly:

  ```
  Imports:
    import os, logging
    from agent_framework import Agent, MCPStdioTool
    from agent_framework.foundry import FoundryChatClient
    from azure.identity.aio import AzureCliCredential
    from dotenv import load_dotenv

  MCP tool:
    second_brain = MCPStdioTool(
        name="second-brain",
        description="sb util (Second Brain) knowledge base — semantic, keyword, and hybrid search over markdown notes",
        command="C:\\Users\\Konstantin_Ivinsky\\AppData\\Local\\CodeMie\\npm-prefix\\sb.cmd",
        args=["mcp"],
    )

  Client (FoundryChatClient):
    client = FoundryChatClient(
        project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
        model=os.environ.get("FOUNDRY_MODEL", "gpt-4o"),
        credential=AzureCliCredential(),
    )

  System instructions (VERBATIM from spec):
    You are an "67" AI meeting assistant.
    You receive:
      1. A complete meeting transcript.
      2. Relevant knowledge retrieved from a personal knowledge base.
      3. The current meeting context.
    Your task is to answer ONLY the latest meaningful question asked during the meeting.
    Rules:
    - Ignore previous discussions unless they help answer the latest question.
    - Determine the latest question primarily from SPEAKER messages.
    - Use MIC messages only when SPEAKER messages do not contain the question.
    - Ignore greetings, acknowledgements, interruptions, and incomplete sentences.
    - If multiple questions exist, answer only the most recent one.
    - Use the provided knowledge base (second-brain tools) whenever it contains relevant information.
    - ALWAYS call semantic_search, keyword_search, or hybrid_search before answering.
    - Do not invent facts.
    - If insufficient information exists, explicitly state that.
    - Keep the answer concise and focused.
    Return:
    - Detected latest question
    - Answer based on Knowledge Base
    - Knowledge sources used (if any) — references

  Agent:
    agent = Agent(
        client=client,
        name="67MeetingAssistant",
        instructions=INSTRUCTIONS,
        tools=[second_brain],
    )

  main():
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)
    logger.info("Starting 67 Meeting Assistant")
    logger.info("Available at: http://localhost:8091")
    logger.info("Note: Make sure 'az login' has been run for authentication")
    from agent_framework.devui import serve
    serve(entities=[agent], port=8091, auto_open=True)

  if __name__ == "__main__":
    main()
  ```

---

## Phase 3: Polish

- [x] T004 [P] Update `67_agent/.env.example` — verify all required vars are documented; add usage comment `# Run: python -m 67_agent.agent` and `# DevUI: python devui/main.py`
- [x] T005 [P] Add one-line docstring to `67_agent/agent.py` header: `"""Meeting assistant agent — answers the latest question using Second Brain MCP retrieval."""`

---

## Dependencies & Execution Order

```
T001 → T002 (parallel fine)
T003 depends on T001, T002
T004, T005 → parallel after T003
```

**Critical path**: T001/T002 → T003 → done (T004/T005 optional polish)

---

## Key Implementation Notes

| Item | Value |
|---|---|
| MCP command | `C:\Users\Konstantin_Ivinsky\AppData\Local\CodeMie\npm-prefix\sb.cmd` |
| MCP args | `["mcp"]` |
| MCP tools exposed | `semantic_search`, `keyword_search`, `hybrid_search` |
| MCP tool params | `query: str`, `top_k: int = 5`, `path_prefix: str = ""` |
| MCP response fields | `file_path`, `heading_path`, `content`, `score`, `source` |
| Client | `FoundryChatClient` + `AzureCliCredential` |
| Env vars | `FOUNDRY_PROJECT_ENDPOINT`, `FOUNDRY_MODEL` |
| DevUI port | `8091` (avoids collision with `agent_foundry` on 8090) |
| Module-level var | `agent` (required for DevUI discovery) |

---

## Notes

- All retrieval is delegated to MCP tools — agent instructs itself to call them before answering
- Transcript is passed as part of the user message in the DevUI chat input (no pre-processing needed)
- Tests not included — PoC; add only if explicitly requested
