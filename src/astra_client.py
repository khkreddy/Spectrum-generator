"""GPT-6 Astra client. Key from OpenAI API Key.txt. Never log the secret."""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-6-astra"
OUT = ROOT / "out" / "astra"
KEY_CANDIDATES = (
    ROOT / "OpenAI API Key.txt",
    Path("/home/harik/awm_build/OpenAI API Key.txt"),
    Path.home() / ".config/openai/api_key.txt",
)


def _keyfile() -> Path:
    for p in KEY_CANDIDATES:
        if p.is_file():
            return p
    raise SystemExit("No OpenAI key file found")


def _key() -> str:
    text = _keyfile().read_text(encoding="utf-8")
    m = re.search(r"sk-[A-Za-z0-9_\-]+", text)
    if not m:
        raise SystemExit("No OpenAI key in OpenAI API Key.txt")
    return m.group(0)


def client() -> OpenAI:
    return OpenAI(api_key=_key())


def image_part(path: Path) -> dict:
    raw = path.read_bytes()
    suffix = path.suffix.lower().lstrip(".")
    mime = {"gif": "image/gif", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(
        suffix, "application/octet-stream"
    )
    b64 = base64.b64encode(raw).decode("ascii")
    return {"type": "input_image", "image_url": f"data:{mime};base64,{b64}"}


def ask(
    prompt: str,
    *,
    images: list[Path] | None = None,
    effort: str = "high",
    name: str = "astra",
    model: str | None = None,
) -> str:
    """One-shot OpenAI Responses call. Persist raw text under out/astra/."""
    use = model or MODEL
    content: list[dict] = [{"type": "input_text", "text": prompt}]
    for p in images or []:
        if p.is_file():
            content.append(image_part(p))
    c = client()
    resp = c.responses.create(
        model=use,
        reasoning={"effort": effort},
        input=[{"role": "user", "content": content}],
    )
    text = resp.output_text or ""
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.md").write_text(text, encoding="utf-8")
    usage = getattr(resp, "usage", None)
    meta = {
        "requested_model": use,
        "response_model": getattr(resp, "model", None),
        "response_id": getattr(resp, "id", None),
        "effort": effort,
        "name": name,
        "n_chars": len(text),
        "usage": usage.model_dump() if usage is not None and hasattr(usage, "model_dump") else str(usage),
    }
    (OUT / f"{name}.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return text


def extract_json(text: str) -> dict | list:
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    blob = fence.group(1) if fence else text
    a, b = blob.find("{"), blob.rfind("}")
    if a >= 0 and b > a:
        return json.loads(blob[a : b + 1])
    a, b = blob.find("["), blob.rfind("]")
    if a >= 0 and b > a:
        return json.loads(blob[a : b + 1])
    raise ValueError("No JSON object in Astra output")
