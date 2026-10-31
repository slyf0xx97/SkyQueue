"""One cached model call that returns a validated Pydantic object (F3.3, F5.6).

Cache key: model + prompt hash. The API key is never part of the key, never logged and never written.
creds = {"provider": "anthropic" | "openrouter", "key": str, "workspace": str | None}; None reads .env.
"""
import hashlib
import json
import os

from dotenv import load_dotenv
from pydantic import BaseModel

from src.config import ROOT

CACHE_DIR = ROOT / "cache"
USAGE: list[dict] = []   # token use per call, read by the logger
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_json(model: str, system: str, user: str, schema: type[BaseModel], purpose: str = "",
              creds: dict | None = None) -> BaseModel:
    provider = (creds or {}).get("provider", "anthropic")
    key = hashlib.sha256(f"{provider}\n{model}\n{system}\n{user}".encode()).hexdigest()[:24]
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        hit = json.loads(path.read_text())
        USAGE.append({**hit["usage"], "purpose": purpose, "cached": True})
        return schema.model_validate(hit["reply"])

    if provider == "openrouter":
        reply, usage = _openrouter(model, system, user, schema, creds)
    else:
        reply, usage = _anthropic(model, system, user, schema, creds)
    usage["model"] = model
    CACHE_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps({"usage": usage, "reply": reply.model_dump(mode="json"), "purpose": purpose}, indent=1))
    USAGE.append({**usage, "purpose": purpose, "cached": False})
    return reply


def _anthropic(model, system, user, schema, creds):
    import anthropic

    if creds and creds.get("key"):
        api_key, workspace = creds["key"], creds.get("workspace")
    else:
        load_dotenv(ROOT / ".env")
        api_key, workspace = os.environ["ANTHROPIC_API_KEY"], os.environ.get("ANTHROPIC_WORKSPACE_ID")
    client = anthropic.Anthropic(api_key=api_key,
                                 default_headers={"anthropic-workspace-id": workspace} if workspace else None)
    resp = client.messages.parse(
        model=model, max_tokens=16000, system=system,
        messages=[{"role": "user", "content": user}], output_format=schema,
        # server-side fallback on a safety refusal, routed by refusal category
        extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"}, extra_body={"fallbacks": "default"},
    )
    if resp.stop_reason == "refusal":
        raise RuntimeError("model declined the request")
    if resp.parsed_output is None:
        raise ValueError(f"reply did not match the schema (stop_reason={resp.stop_reason})")
    return resp.parsed_output, {"input_tokens": resp.usage.input_tokens, "output_tokens": resp.usage.output_tokens}


def _openrouter(model, system, user, schema, creds):
    import httpx

    body = {"model": model, "response_format": {"type": "json_object"}, "messages": [
        {"role": "system", "content": f"{system}\n\nReply with one JSON object matching this JSON schema:\n"
                                      f"{json.dumps(schema.model_json_schema())}"},
        {"role": "user", "content": user}]}
    r = httpx.post(OPENROUTER_URL, json=body, timeout=120,
                   headers={"Authorization": f"Bearer {creds['key']}", "X-Title": "SkyQueue"})
    r.raise_for_status()
    data = r.json()
    text = data["choices"][0]["message"]["content"]
    start, end = text.find("{"), text.rfind("}")
    reply = schema.model_validate_json(text[start:end + 1])
    u = data.get("usage") or {}
    return reply, {"input_tokens": u.get("prompt_tokens", 0), "output_tokens": u.get("completion_tokens", 0)}
