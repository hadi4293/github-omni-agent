"""
لودر مقاوم .env
چند مسیر را امتحان می‌کند تا فایل پیدا شود.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple

from dotenv import load_dotenv


def _candidates() -> List[Path]:
    here = Path(__file__).resolve().parent
    cwd = Path.cwd().resolve()
    paths = [
        here / ".env",
        cwd / ".env",
        here.parent / ".env",
        cwd.parent / ".env",
    ]
    # یکتا نگه دار
    seen = set()
    out: List[Path] = []
    for p in paths:
        key = str(p)
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def load_project_env() -> Tuple[Optional[Path], List[str]]:
    """
    Returns (loaded_path or None, log_lines)
    """
    logs: List[str] = []
    loaded: Optional[Path] = None

    for path in _candidates():
        exists = path.exists()
        logs.append(f"check: {path}  exists={exists}")
        if exists:
            ok = load_dotenv(dotenv_path=path, override=True)
            logs.append(f"load_dotenv({path}) -> {ok}")
            loaded = path
            break

    if loaded is None:
        logs.append("هیچ فایل .env پیدا نشد.")

    return loaded, logs


def env_status() -> dict:
    gemini = (os.getenv("GEMINI_API_KEY") or "").strip()
    github = (os.getenv("GITHUB_TOKEN") or "").strip()

    def mask(v: str) -> str:
        if not v:
            return "(خالی)"
        if len(v) <= 8:
            return "***"
        return v[:4] + "..." + v[-4:]

    return {
        "GEMINI_API_KEY": mask(gemini),
        "GITHUB_TOKEN": mask(github),
        "has_gemini": bool(gemini),
        "has_github": bool(github),
        "ok": bool(gemini and github),
    }
