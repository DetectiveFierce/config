#!/usr/bin/python3
"""Explicit, one-time public model download; analysis remains offline."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


REVISION = "1110a243fdf4706b3f48f1d95db1a4f5529b4d41"
ROOT = Path.home() / ".local/share/storage-advisor"
ENV = ROOT / "model-venv"
MODEL = ROOT / "all-MiniLM-L6-v2"
FILES = ["config.json", "config_sentence_transformers.json", "modules.json",
         "sentence_bert_config.json", "tokenizer.json", "tokenizer_config.json",
         "special_tokens_map.json", "model.safetensors", "1_Pooling/config.json"]


def main() -> None:
    ROOT.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(ROOT, 0o700)
    if not (ENV / "bin/python").exists():
        subprocess.run([sys.executable, "-m", "venv", "--system-site-packages", str(ENV)], check=True)
    subprocess.run([str(ENV / "bin/python"), "-m", "pip", "install",
                    "--disable-pip-version-check", "sentence-transformers==5.1.1",
                    "transformers==4.57.6"], check=True)
    code = ("from huggingface_hub import snapshot_download; "
            "snapshot_download(repo_id='sentence-transformers/all-MiniLM-L6-v2', "
            f"revision='{REVISION}', local_dir={str(MODEL)!r}, allow_patterns={FILES!r})")
    subprocess.run([str(ENV / "bin/python"), "-c", code], check=True)
    (MODEL / "revision.txt").write_text(REVISION + "\n")
    print(f"Pinned local model ready at {MODEL}")


if __name__ == "__main__":
    main()
