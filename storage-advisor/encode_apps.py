#!/usr/bin/python3
"""CPU-only model subprocess; reads short app descriptions from stdin."""
import json
import sys
from pathlib import Path

from sentence_transformers import SentenceTransformer


model_path = Path.home() / ".local/share/storage-advisor/all-MiniLM-L6-v2"
if (model_path / "revision.txt").read_text().strip() != "1110a243fdf4706b3f48f1d95db1a4f5529b4d41":
    raise SystemExit("Unexpected local model revision")
descriptions = json.load(sys.stdin)
model = SentenceTransformer(str(model_path), device="cpu", local_files_only=True)
vectors = model.encode([text[:1000] for text in descriptions.values()], batch_size=16,
                       normalize_embeddings=True, show_progress_bar=False)
json.dump({key: vec.tolist() for key, vec in zip(descriptions, vectors)}, sys.stdout)
