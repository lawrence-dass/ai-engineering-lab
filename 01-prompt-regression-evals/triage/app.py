"""The feature under test: one model call that turns a support message into a Triage record.

This is the code a product would ship. The eval suite calls it and nothing else,
so what gets measured is what would run in production.
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path

import anthropic
from pydantic import ValidationError

from triage.schema import TRIAGE_JSON_SCHEMA, Triage

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Short names used on the command line, mapped to API model IDs.
MODELS = {
    "haiku": "claude-haiku-5-5",
    "opus": "claude-opus-5-5",
}

# Classification is a simple task, so both models run at low effort.
# Sampling parameters such as temperature are not accepted by these models,
# which means runs are not deterministic. The eval repeats each case to see the spread.
EFFORT = "low"
MAX_TOKENS = 8000


@dataclass
class TriageResult:
    output: Triage | None  # None when the reply could not be used
    raw_text: str
    status: str  # "ok", "truncated", "refusal" or "invalid"
    stop_reason: str | None
    served_model: str
    input_tokens: int
    output_tokens: int
    latency_s: float


def load_prompt(version: str) -> str:
    return (PROMPTS_DIR / f"{version}.md").read_text()


def build_user_message(ticket: str) -> str:
    return f"<ticket>\n{ticket}\n</ticket>"


async def triage_ticket(
    client: anthropic.AsyncAnthropic, *, model: str, system_prompt: str, ticket: str
) -> TriageResult:
    started = time.perf_counter()
    response = await client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=[{"role": "user", "content": build_user_message(ticket)}],
        output_config={
            "effort": EFFORT,
            "format": {"type": "json_schema", "schema": TRIAGE_JSON_SCHEMA},
        },
    )
    latency = time.perf_counter() - started

    raw_text = next((block.text for block in response.content if block.type == "text"), "")
    output: Triage | None = None

    if response.stop_reason == "refusal":
        status = "refusal"
    elif response.stop_reason == "max_tokens":
        status = "truncated"
    else:
        try:
            output = Triage.model_validate(json.loads(raw_text))
            status = "ok"
        except (json.JSONDecodeError, ValidationError):
            status = "invalid"

    return TriageResult(
        output=output,
        raw_text=raw_text,
        status=status,
        stop_reason=response.stop_reason,
        served_model=response.model,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        latency_s=round(latency, 3),
    )
