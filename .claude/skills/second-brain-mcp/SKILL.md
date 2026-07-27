# Skill: Second Brain MCP Integration

Use this skill whenever you need to connect an Agent Framework agent to the local
sb util (Second Brain) knowledge base MCP server (`sb.cmd mcp`).

---

## What the MCP server provides

The Second Brain MCP server exposes three search tools over stdio:

| Tool | Purpose | Key params |
|---|---|---|
| `semantic_search` | Embedding-based similarity search over markdown notes | `query`, `top_k=5`, `path_prefix=""` |
| `keyword_search` | BM25 / full-text keyword search by title, heading, tags | `query`, `top_k=5`, `path_prefix=""` |
| `hybrid_search` | Combined semantic + keyword (recommended for RAG) | `query`, `top_k=5`, `path_prefix=""` |

All three return a `SearchResponse` with:
- `results[].file_path` — path to the source markdown file
- `results[].heading_path` — heading breadcrumb (e.g. `Project / Design / Architecture`)
- `results[].content` — the retrieved text chunk
- `results[].score` — relevance score (higher = more relevant)
- `results[].source` — `"semantic"`, `"keyword"`, or `"hybrid"`

---

## Wiring the MCP server

```python
from agent_framework import Agent, MCPStdioTool
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential
import os

second_brain = MCPStdioTool(
    name="second-brain",
    description="sb util (Second Brain) knowledge base — semantic, keyword, and hybrid search over markdown notes",
    command="C:\\Users\\Konstantin_Ivinsky\\AppData\\Local\\CodeMie\\npm-prefix\\sb.cmd",
    args=["mcp"],
)

agent = Agent(
    client=FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ.get("FOUNDRY_MODEL", "gpt-4o"),
        credential=AzureCliCredential(),
    ),
    name="MyAgent",
    instructions="Your instructions here. Always call semantic_search or hybrid_search before answering knowledge questions.",
    tools=[second_brain],
)
```

---

## Prompt guidance for the model

Tell the model explicitly to call search before answering, and to cite sources:

```
- ALWAYS call semantic_search, keyword_search, or hybrid_search before answering
  knowledge-base questions.
- Prefer hybrid_search for most questions; use keyword_search for exact titles or tags.
- Cite sources using file_path and heading_path from the results.
- If search returns no relevant results, say "the answer is not found in the knowledge base".
- Do not invent facts.
```

---

## Filtering by path

Use `path_prefix` to scope results to a subdirectory of the knowledge base:

```
semantic_search(query="...", top_k=5, path_prefix="01-projects/ai-upskilling")
keyword_search(query="MCP server", top_k=3, path_prefix="02-areas")
```

---

## MCP server startup

The server launches automatically as a subprocess when the agent first uses a tool.
No manual startup needed. Prerequisites:

1. `sb.cmd` must be installed at the path above (CodeMie local install)
2. The sb util (Second Brain) index must be built — run `sb index` once if this is a fresh setup
3. `az login` must be completed for FoundryChatClient authentication

---

## Alternative startup commands

If `sb.cmd` is unavailable, the MCP server can also be started as:

```python
# Using installed Python script (requires second-brain-mcp on PATH)
MCPStdioTool(name="second-brain", command="second-brain-mcp", args=[])

# Using the Python module directly (requires venv activated with the package)
MCPStdioTool(
    name="second-brain",
    command="python",
    args=["-m", "second_brain_search.mcp_server"],
)
```

---

## Example: RAG agent that answers from the knowledge base

```python
INSTRUCTIONS = """
You are a knowledge assistant. When the user asks a question:
1. Always call hybrid_search first with the user's question as the query.
2. If the results are sparse, also call keyword_search with key terms.
3. Answer based on the retrieved content. Cite file_path and heading_path.
4. If no relevant content is found, say "Not found in knowledge base."
5. Do not invent facts.
"""
```

---

## Example: Meeting assistant that retrieves on demand

```python
INSTRUCTIONS = """
You receive a meeting transcript and must answer the latest meaningful question.
- Identify the latest SPEAKER question (ignore MIC, greetings, chatter).
- Call semantic_search or hybrid_search to retrieve relevant knowledge.
- Answer concisely. Return: detected question, answer, sources.
- If no question found: "I cannot determine the latest question."
- If no answer found: "The answer is not found."
"""
```
