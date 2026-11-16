"""The feature under test: one model call that turns a support message into a Triage record.

This is the code a product would ship. The eval suite calls it and nothing else,
so what gets measured is what would run in production.

The same feature is implemented for two providers, Anthropic and OpenAI. Both get
the same system prompt, the same ticket, the same output contract and the same
effort setting, and both return the same TriageResult, so the grader and report
never need to know which vendor answered.
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path

import anthropic
import openai
from pydantic import ValidationError

from triage.schema import TRIAGE_JSON_SCHEMA, TRIAGE_JSON_SCHEMA_OPENAI, Triage

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

# Short names used on the command line, mapped to API model IDs.
# One cheap model and one strong model (a step below the flagship) from each vendor.
MODELS = {
    "haiku": "claude-haiku-5-5",
    "opus": "claude-opus-5-5",
    "luna": "gpt-6-luna",
    "sol": "gpt-6.1-sol",
}
PROVIDERS = {"haiku": "anthropic", "opus": "anthropic", "luna": "openai", "sol": "openai"}
PROVIDER_BY_MODEL_ID = {MODELS[name]: PROVIDERS[name] for name in MODELS}

# Classification is a simple task, so every model runs at low effort, the lowest
# level all four accept. All four reason before answering, and the reasoning is
# billed as output. No sampling parameters such as temperature are sent, so runs
# are not deterministic. The eval repeats each case to see the spread.
EFFORT = "low"
MAX_TOKENS = 8000


@dataclass
class TriageResult:
    output: Triage | None  # None when the reply could not be used
    raw_text: str
    status: str  # "ok", "truncated", "refusal" or "invalid"
    stop_reason: str | None
    served_model: str
    input_tokens: int  # input billed at the full rate, excluding cache reads and writes
    output_tokens: int  # includes reasoning tokens
    latency_s: float
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int | None = None  # thinking/reasoning tokens, a part of output_tokens


def load_prompt(version: str) -> str:
    return (PROMPTS_DIR / f"{version}.md").read_text()


def build_user_message(ticket: str) -> str:
    return f"<ticket>\n{ticket}\n</ticket>"


def parse_reply(raw_text: str) -> tuple[Triage | None, str]:
    try:
        return Triage.model_validate(json.loads(raw_text)), "ok"
    except (json.JSONDecodeError, ValidationError):
        return None, "invalid"


async def triage_ticket(clients: dict, *, model: str, system_prompt: str, ticket: str) -> TriageResult:
    """Triages one ticket with the named model, using that model's provider."""
    provider = PROVIDER_BY_MODEL_ID[model]
    call = triage_anthropic if provider == "anthropic" else triage_openai
    return await call(clients[provider], model=model, system_prompt=system_prompt, ticket=ticket)


async def triage_anthropic(
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
        output, status = parse_reply(raw_text)

    usage = response.usage
    return TriageResult(
        output=output,
        raw_text=raw_text,
        status=status,
        stop_reason=response.stop_reason,
        served_model=response.model,
        input_tokens=usage.input_tokens,  # Anthropic already excludes cached tokens here
        output_tokens=usage.output_tokens,
        latency_s=round(latency, 3),
        cache_read_tokens=usage.cache_read_input_tokens or 0,
        cache_write_tokens=usage.cache_creation_input_tokens or 0,
        reasoning_tokens=usage.output_tokens_details.thinking_tokens if usage.output_tokens_details else None,
    )


async def triage_openai(client: openai.AsyncOpenAI, *, model: str, system_prompt: str, ticket: str) -> TriageResult:
    started = time.perf_counter()
    response = await client.responses.create(
        model=model,
        instructions=system_prompt,
        input=build_user_message(ticket),
        max_output_tokens=MAX_TOKENS,
        reasoning={"effort": EFFORT},
        text={"format": {"type": "json_schema", "name": "triage", "schema": TRIAGE_JSON_SCHEMA_OPENAI, "strict": True}},
        store=False,  # test traffic, nothing to keep on OpenAI's side
    )
    latency = time.perf_counter() - started

    refused = any(
        part.type == "refusal"
        for item in response.output
        if item.type == "message"
        for part in item.content
    )
    raw_text = response.output_text
    output: Triage | None = None
    incomplete = response.incomplete_details.reason if response.incomplete_details else None

    if refused or incomplete == "content_filter":
        status, stop_reason = "refusal", "refusal"
    elif response.status == "incomplete":
        status, stop_reason = "truncated", f"incomplete:{incomplete}"
    else:
        output, status = parse_reply(raw_text)
        stop_reason = response.status

    usage = response.usage
    details = usage.input_tokens_details
    cache_read = details.cached_tokens or 0
    cache_write = getattr(details, "cache_write_tokens", 0) or 0
    return TriageResult(
        output=output,
        raw_text=raw_text,
        status=status,
        stop_reason=stop_reason,
        served_model=response.model,
        input_tokens=usage.input_tokens - cache_read - cache_write,  # OpenAI's count includes cached tokens
        output_tokens=usage.output_tokens,
        latency_s=round(latency, 3),
        cache_read_tokens=cache_read,
        cache_write_tokens=cache_write,
        reasoning_tokens=usage.output_tokens_details.reasoning_tokens,
    )
