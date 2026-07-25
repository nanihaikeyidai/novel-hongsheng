#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""novel-hongsheng environment check."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PYTHON = Path(r"D:\HermesWorkspace\MOSS-TTS\.venv\Scripts\python.exe")
MODEL_DIR = Path(r"D:\HermesWorkspace\models\MOSS-TTS-Local-Transformer-v1.5")
AUDIOBOOK = PROJECT_ROOT / "04-audiobook"
REF_DIR = AUDIOBOOK / "参考音色"
CHAPTER_JSON = AUDIOBOOK / "ch01_红绳伞" / "红绳_第01章_有声小说.json"


def check(label: str, path: Path) -> bool:
    ok = path.exists()
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {label}: {path}")
    return ok


def main() -> int:
    print("=== novel-hongsheng setup ===")
    print(f"Project: {PROJECT_ROOT}")

    ok = True
    ok &= check("git repo", PROJECT_ROOT / ".git")
    ok &= check("python venv", PYTHON)
    ok &= check("tts model", MODEL_DIR)
    ok &= check("ref voices", REF_DIR)
    ok &= check("chapter1 json", CHAPTER_JSON)

    if PYTHON.exists():
        ver = subprocess.check_output([str(PYTHON), "--version"], text=True).strip()
        print(f"Python: {ver}")
        cuda = subprocess.check_output(
            [str(PYTHON), "-c", "import torch; print(torch.cuda.is_available())"],
            text=True,
        ).strip()
        print(f"[{'OK' if cuda == 'True' else 'WARN'}] CUDA available: {cuda}")

    if REF_DIR.exists():
        count = len(list(REF_DIR.glob("*.wav")))
        print(f"Ref voice files: {count}")

    print()
    if ok:
        print("Ready. Run: 04-audiobook\\scripts\\generate_ch01.bat")
        return 0
    print("Some checks failed. See AGENTS.md")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
