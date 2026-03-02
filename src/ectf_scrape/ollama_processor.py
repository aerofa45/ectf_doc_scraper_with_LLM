from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests

# Uses local Ollama server (free) at http://localhost:11434
# Install: https://ollama.com
# Pull model: ollama pull llama3.1:8b (or any other)
DEFAULT_MODEL = "llama3.1:8b"


SYSTEM_INSTRUCTIONS = """You are a technical documentation mining assistant.
You will be given a markdown page from eCTF documentation.

Return STRICT JSON with keys:
- page_category: one of ["tools","api","bootloader","hardware","protocol","remote_scenario","flags","other"]
- short_summary: <= 6 bullet points as strings
- inferred_commands: list of CLI commands or command templates (strings)
- key_terms: list of important keywords (strings)
- notes: list of short notes (strings), including any constraints/limits/timeouts

Rules:
- Only output JSON (no markdown, no commentary).
- If uncertain, be conservative and put items in notes.
"""


def ollama_available(timeout_s: float = 2.0) -> bool:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=timeout_s)
        return r.status_code == 200
    except Exception:
        return False


def process_with_ollama(markdown: str, model: str = DEFAULT_MODEL, timeout_s: float = 120.0) -> Dict[str, Any]:
    # Keep prompts bounded so you don’t choke the local model
    md = markdown[:12000]

    payload = {
        "model": model,
        "prompt": (
            f"{SYSTEM_INSTRUCTIONS}\n\n"
            "PAGE MARKDOWN:\n"
            "----------------\n"
            f"{md}\n"
        ),
        "stream": False,
        "format": "json",
        "options": {"temperature": 0},
    }

    r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=timeout_s)
    r.raise_for_status()

    data = r.json()
    # Ollama returns {"response": "...json..."} when format=json
    text = (data.get("response") or "").strip()

    try:
        return json.loads(text)
    except Exception:
        # Fallback: preserve raw output so nothing is lost
        return {"page_category": "other", "short_summary": [], "inferred_commands": [], "key_terms": [], "notes": ["Failed to parse JSON."], "raw_output": text}