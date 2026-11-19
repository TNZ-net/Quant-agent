import json, os, urllib.request
from .. import config  # noqa: F401   
def host() -> str:
    h = os.getenv("OLLAMA_HOST", "").strip() or "127.0.0.1:11434"
    if "://" not in h:
        h = "http://" + h
    scheme, rest = h.split("://", 1)
    hostname, _, port = rest.partition(":")
    if hostname in ("", "0.0.0.0"):        
        hostname = "127.0.0.1"
    return f"{scheme}://{hostname}:{port.rstrip('/') or '11434'}"


def _call(path: str, payload: dict | None = None, timeout=300) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(host() + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def list_models() -> list[str]:
    return [m["name"] for m in _call("/api/tags", timeout=10).get("models", [])]


def pick_model() -> str:
    name = os.getenv("OLLAMA_MODEL")
    if name:
        return name
    chat_models = [m for m in list_models() if "embed" not in m.lower()]
    if not chat_models:
        raise RuntimeError("No chat model installed. Run `ollama pull qwen2.5:1.5b` or set OLLAMA_MODEL.")
    return chat_models[0]


def chat(prompt: str, system: str = "", model: str | None = None, timeout=300) -> str:
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
    out = _call("/api/chat", {"model": model or pick_model(), "messages": msgs, "stream": False,
                              "options": {"temperature": 0.1, "num_predict": 350}}, timeout)
    return out["message"]["content"].strip()