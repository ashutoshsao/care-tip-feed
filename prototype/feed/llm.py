"""Thin OpenRouter client: structured outputs + token/cost tracking."""

import json
import os
import time
from copy import deepcopy
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

URL = "https://openrouter.ai/api/v1/chat/completions"

# $ per million tokens (in, out), pulled from OpenRouter 2026-10-12.
PRICES = {
    "anthropic/claude-haiku-5.5": (0.10, 0.50),
    "anthropic/claude-sonnet-5.5": (2.00, 10.00),
    "anthropic/claude-opus-5.5": (4.00, 20.00),
    "deepseek/deepseek-v4.1-flash": (0.30, 1.20),
    "google/gemini-3.8-flash": (0.75, 3.75),
    "google/gemini-3.1-pro-preview": (2.00, 12.00),
    "openai/gpt-6-luna": (0.10, 0.50),
    "openai/gpt-6.1-sol": (2.00, 10.00),
    "anthropic/claude-sonnet-5.5": (2.00, 10.00),
    "qwen/qwen3.8-flash": (0.15, 0.47),
    "z-ai/glm-5.3-flash": (0.15, 0.50),
    "mistralai/mistral-small-2603": (0.15, 0.60),
}

USAGE: dict[str, dict] = {}


def strict_schema(schema: dict) -> dict:
    """Inline $refs and make every object strict (all props required, no extras)."""
    schema = deepcopy(schema)
    defs = schema.pop("$defs", {})

    def walk(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return walk(deepcopy(defs[node["$ref"].split("/")[-1]]))
            node = {k: walk(v) for k, v in node.items()
                    if k != "default" and not (k == "title" and isinstance(v, str))}
            if node.get("type") == "object" and "properties" in node:
                node["required"] = list(node["properties"].keys())
                node["additionalProperties"] = False
            return node
        if isinstance(node, list):
            return [walk(x) for x in node]
        return node

    return walk(schema)


def chat_json(model: str, system: str, user: str, schema: dict, name: str = "output",
              temperature: float = 0.0, max_tokens: int = 8000, retries: int = 3) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "response_format": {"type": "json_schema",
                            "json_schema": {"name": name, "strict": True, "schema": schema}},
        "provider": {"require_parameters": True},
        "max_tokens": max_tokens,
    }
    if not model.startswith(("anthropic/", "openai/")):   # Claude 5.x / GPT-6 endpoints reject temperature
        body["temperature"] = temperature
    headers = {"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}"}
    last = None
    for attempt in range(retries):
        try:
            r = httpx.post(URL, json=body, headers=headers, timeout=180)
            if r.status_code != 200:
                raise httpx.HTTPError(f"{r.status_code}: {r.text[:300]}")
            data = r.json()
            content = data["choices"][0]["message"]["content"]
            _track(model, data.get("usage", {}))
            return json.loads(content)
        except (httpx.HTTPError, KeyError, json.JSONDecodeError) as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{model} failed after {retries} tries: {last}")


def _track(model: str, usage: dict):
    u = USAGE.setdefault(model, {"calls": 0, "in": 0, "out": 0})
    u["calls"] += 1
    u["in"] += usage.get("prompt_tokens", 0)
    u["out"] += usage.get("completion_tokens", 0)


def cost(model: str) -> float:
    u = USAGE.get(model, {"in": 0, "out": 0})
    p_in, p_out = PRICES.get(model, (0, 0))
    return (u["in"] * p_in + u["out"] * p_out) / 1e6
