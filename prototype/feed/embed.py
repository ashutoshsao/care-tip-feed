"""Local embeddings via Ollama, cached to disk (tips are embedded once — D12)."""

import hashlib
import json
from pathlib import Path

import httpx
import numpy as np

OLLAMA = "http://localhost:11434/api/embed"
CACHE = Path(__file__).resolve().parents[1] / "data" / "embed_cache"


def embed(texts: list[str], model: str) -> np.ndarray:
    CACHE.mkdir(parents=True, exist_ok=True)
    out, missing = [None] * len(texts), []
    for i, t in enumerate(texts):
        f = CACHE / f"{model.replace(':', '_')}_{hashlib.sha1(t.encode()).hexdigest()}.json"
        if f.exists():
            out[i] = json.loads(f.read_text())
        else:
            missing.append(i)
    for start in range(0, len(missing), 32):
        batch = missing[start:start + 32]
        r = httpx.post(OLLAMA, json={"model": model, "input": [texts[i] for i in batch]}, timeout=300)
        r.raise_for_status()
        for i, vec in zip(batch, r.json()["embeddings"]):
            out[i] = vec
            f = CACHE / f"{model.replace(':', '_')}_{hashlib.sha1(texts[i].encode()).hexdigest()}.json"
            f.write_text(json.dumps(vec))
    return np.array(out, dtype=np.float32)   # Ollama returns L2-normalized vectors


def cosine(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return a @ b.T
