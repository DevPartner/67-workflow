# Copyright (c) Microsoft. All rights reserved.

"""Transcript Q&A Workflow — fetches live transcript, detects questions, answers via Second Brain."""

import os
from dataclasses import dataclass, field

import httpx
from agent_framework import (
    Agent,
    Case,
    Default,
    Executor,
    MCPStreamableHTTPTool,
    Message,
    WorkflowBuilder,
    WorkflowContext,
    handler,
)
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing_extensions import Never

load_dotenv()

# ── Request / data models ─────────────────────────────────────────────────────


class TranscriptRequest(BaseModel):
    """Trigger the transcript fetch workflow."""

    port: int = int(os.environ.get("TRANSCRIPT_PORT", "3000"))
    base_url: str = os.environ.get("TRANSCRIPT_BASE_URL", "http://localhost")


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


# ── Prompt ────────────────────────────────────────────────────────────────────

_QUESTION_DETECT_PROMPT = (
    "You are an assistant that detects questions in meeting transcripts.\n"
    "Analyze the transcript below.\n"
    "If it contains a question, reply with exactly: QUESTION: <question text>\n"
    "If no question is present, reply with exactly: NO_QUESTION\n\n"
    "Transcript:\n{transcript}"
)

# ── Executors ─────────────────────────────────────────────────────────────────


class TranscriptReceiver(Executor):
    """Step 1: Fetches the live transcript from the Rust REST server."""

    @handler
    async def handle_request(self, request: TranscriptRequest, ctx: WorkflowContext[TranscriptData]) -> None:
        url = f"{request.base_url.rstrip('/')}:{request.port}/transcript"
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
        chat_response = await client.get_response([Message("user", [prompt])])
        response_text = chat_response.text.strip()

        if response_text.startswith("QUESTION:"):
            question = response_text[len("QUESTION:"):].strip()
            result = QuestionDetectionResult(transcript_data=data, has_question=True, question_text=question)
        else:
            result = QuestionDetectionResult(transcript_data=data, has_question=False)

        await ctx.send_message(result)


class AnswerGenerator(Executor):
    """Step 3a: Answers the detected question using Second Brain MCP retrieval."""

    @handler
    async def handle_question(
        self, result: QuestionDetectionResult, ctx: WorkflowContext[Never, str]
    ) -> None:
        second_brain = MCPStreamableHTTPTool(
            name="sb",
            description="Second Brain knowledge base — semantic and keyword search over markdown notes",
            url="http://localhost:3001/mcp",
        )
        answer_agent = Agent(
            name="transcript-answer-agent",
            client=FoundryChatClient(
                project_endpoint=os.environ.get("FOUNDRY_PROJECT_ENDPOINT"),
                model=os.environ.get("FOUNDRY_MODEL", "gpt-4o"),
                credential=AzureCliCredential(),
            ),
            instructions=(
                "You have access to the Second Brain (sb) tool.\n"
                "For every request, call sb (keyword_search or semantic_search) first, then answer.\n"
                "Use only the tool result to answer. Never answer from memory."
            ),
            tools=[second_brain],
        )
        agent_response = await answer_agent.run(result.question_text)
        await ctx.yield_output(agent_response.text)


class SilentTerminator(Executor):
    """Step 3b: No question detected — terminate gracefully."""

    @handler
    async def handle_no_question(
        self, result: QuestionDetectionResult, ctx: WorkflowContext[Never, str]
    ) -> None:
        await ctx.yield_output("No question detected in transcript.")


# ── Workflow wiring ───────────────────────────────────────────────────────────

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


# ── Entry point ───────────────────────────────────────────────────────────────


def main() -> None:
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
