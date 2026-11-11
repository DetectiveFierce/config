"""Bounded, local similarity retrieval. Similarity is never deletion proof."""
from __future__ import annotations

import hashlib
import math
import os
import re
import json
import subprocess
import warnings
from collections import defaultdict
from pathlib import Path

from .common import HOME, run


def exact_digest(path: Path) -> str:
    digest = hashlib.blake2b(digest_size=32)
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOATIME", 0))
    try:
        while block := os.read(fd, 1024 * 1024):
            digest.update(block)
    finally:
        os.close(fd)
    return digest.hexdigest()


def _shingles(text: str) -> set[int]:
    words = re.findall(r"[\w]+", text.casefold())
    return {int.from_bytes(hashlib.blake2b(" ".join(words[i:i+5]).encode(),
                                         digest_size=8).digest(), "big")
            for i in range(max(0, len(words)-4))}


def minhash(text: str, count: int = 32) -> tuple[int, ...]:
    values = sorted(_shingles(text))[:1024]
    if not values:
        return ()
    prime = 18446744073709551557
    return tuple(min(((i * 11400714819323198485 + 0x9e3779b97f4a7c15) * x +
                      (i + 1) * 6364136223846793005) % prime for x in values)
                 for i in range(1, count + 1))


def signature_similarity(a: tuple[int, ...], b: tuple[int, ...]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x == y for x, y in zip(a, b)) / len(a)


def pdf_text(path: Path) -> str:
    result = run(["pdftotext", "-f", "1", "-l", "5", "-layout", str(path), "-"], 8)
    return result.stdout[:80_000] if result.returncode == 0 else ""


def image_hash(path: Path) -> tuple[int, int, int] | None:
    try:
        import numpy as np
        from PIL import Image
        from scipy.fft import dctn
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                width, height = image.size
                if width * height > 25_000_000:
                    return None
                grey = image.convert("L").resize((32, 32))
                coeff = dctn(np.asarray(grey, dtype=float), norm="ortho")[:8, :8]
                pixels = coeff.flatten()[1:]
                median = float(np.median(pixels))
                bits = sum((1 << i) for i, value in enumerate(pixels) if value > median)
                return bits, width, height
    except (OSError, ValueError, ImportError, Warning):
        return None


def hamming(a: int, b: int) -> int:
    return (a ^ b).bit_count()


def app_embeddings(descriptions: dict[str, str]) -> dict[str, list[float]]:
    """Encode brief app descriptions only. Never transmit text or read file contents."""
    root = HOME / ".local/share/storage-advisor"
    interpreter = root / "model-venv/bin/python"
    model = root / "all-MiniLM-L6-v2"
    helper = Path(__file__).resolve().parent.parent / "encode_apps.py"
    if not (interpreter.is_file() and (model / "revision.txt").is_file()):
        return {}
    try:
        result = subprocess.run([str(interpreter), str(helper)], input=json.dumps(descriptions),
                                capture_output=True, text=True, timeout=120, check=False,
                                env={**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
        return json.loads(result.stdout) if result.returncode == 0 else {}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return {}


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x*x for x in a)) *
                                               math.sqrt(sum(y*y for y in b)) + 1e-12)
