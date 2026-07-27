# Copyright (c) Microsoft. All rights reserved.

"""Meeting assistant agent — answers the latest question using Second Brain MCP retrieval."""

import os
import sys
from pathlib import Path

from agent_framework import Agent, MCPStreamableHTTPTool, SkillsProvider, ToolApprovalMiddleware
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv

_SKILLS_ROOT = str(Path(__file__).resolve().parent.parent)
if _SKILLS_ROOT not in sys.path:
    sys.path.insert(0, _SKILLS_ROOT)

from subprocess_script_runner import subprocess_script_runner  # pyrefly: ignore[missing-import]  # noqa: E402

load_dotenv()

_skills_dir = Path(__file__).parent / "skills"
_skill_md = (_skills_dir / "second-brain" / "SKILL.md").read_text(encoding="utf-8")

INSTRUCTIONS = f"""
You are an AI Assistant with access to the `sb` Second Brain MCP tool.

For every user request, call exactly one `sb` search tool first.
If you do not call `sb`, do not answer.
Use only the tool result to answer the user.

Rules:
- Always start with one keyword_search or semantic_search call. No exceptions.
- Optionally follow with one get_document call if the snippet is insufficient.
- Maximum two sb tool calls per request. Never retry with different parameters.
- Never answer from memory.
- If the result is insufficient, say so — do not skip the search call.

{_skill_md}
"""

_SB_SEARCH_TOOLS = {"sb/keyword_search", "sb/semantic_search"}


class SbToolRequiredMiddleware:
    """
    Runtime enforcement: reject any response not preceded by an sb search call.

    Prompt alone cannot force tool usage — this middleware tracks tool calls per
    turn and raises RuntimeError if the turn ends without at least one sb search
    invocation, providing a hard policy layer independent of the LLM prompt.

    Allowed per-turn pattern: one search call + optional get_document call.
    """

    def __init__(self) -> None:
        self._search_called: bool = False

    def on_turn_start(self) -> None:
        self._search_called = False

    def on_tool_call(self, tool_name: str, **kwargs) -> bool:
        if tool_name in _SB_SEARCH_TOOLS:
            self._search_called = True
        return True

    def on_before_response(self, response: str) -> str:
        if not self._search_called:
            raise RuntimeError(
                "Response blocked: no sb search tool was called this turn. "
                "Policy requires sb/keyword_search or sb/semantic_search before answering."
            )
        return response


second_brain = MCPStreamableHTTPTool(
    name="sb",
    description="sb util (Second Brain) knowledge base — semantic and keyword search over markdown notes",
    url="http://localhost:3001/mcp",
)

skills_provider = SkillsProvider.from_paths(
    skill_paths=str(_skills_dir),
    script_runner=subprocess_script_runner,
)

agent = Agent(
    name="67 Assistant",
    client=FoundryChatClient(
        project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
        model=os.environ.get("FOUNDRY_MODEL", "gpt-5-mini"),
        credential=AzureCliCredential(),
    ),
    instructions=INSTRUCTIONS,
    tools=[second_brain],
    context_providers=[skills_provider],
    middleware=[
        SbToolRequiredMiddleware(),
        ToolApprovalMiddleware(auto_approval_rules=[SkillsProvider.all_tools_auto_approval_rule]),
    ],
)


def main() -> None:
    """Launch the 67 Meeting Assistant in DevUI."""
    import logging

    from agent_framework.devui import serve

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger(__name__)

    skill_names = sorted(p.name for p in _skills_dir.iterdir() if (p / "SKILL.md").exists())
    logger.info("Skills loaded: %s", ", ".join(skill_names) if skill_names else "(none)")

    logger.info("Starting 67 Meeting Assistant")
    logger.info("Available at: http://localhost:8091")
    logger.info("Note: Make sure 'az login' has been run for authentication")
    logger.info("Note: ensure the Second Brain MCP server is running at http://localhost:3001/mcp")

    serve(entities=[agent], port=8091, auto_open=True)


if __name__ == "__main__":
    main()
