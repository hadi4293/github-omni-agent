"""
لودر قطعی .env — دیگر وابسته به cwd نیست.

ترتیب جستجو:
1) کنار همین پکیج (پوشه پروژه)
2) مسیر ثابت در خانه کاربر: ~/.github-omni-agent.env
3) cwd و والد cwd
4) متغیرهای محیطی از قبل set شده در سیستم
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Tuple

from dotenv import load_dotenv

PACKAGE_DIR = Path(__file__).resolve().parent
HOME_ENV = Path.home() / ".github-omni-agent.env"
PACKAGE_ENV = PACKAGE_DIR / ".env"

_LOADED_PATH: Optional[Path] = None
_LOGS: List[str] = []


def _candidates() -> List[Path]:
    cwd = Path.cwd().resolve()
    paths = [
        PACKAGE_ENV,
        HOME_ENV,
        cwd / ".env",
        cwd.parent / ".env",
        PACKAGE_DIR.parent / ".env",
    ]
    seen = set()
    out: List[Path] = []
    for p in paths:
        key = str(p.resolve()) if p.exists() else str(p)
        try:
            key = str(p.resolve())
        except Exception:
            key = str(p)
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def _parse_env_file(path: Path) -> dict:
    """خواندن دستی .env برای اطمینان (علاوه بر dotenv)."""
    data = {}
    try:
        text = path.read_text(encoding="utf-8-sig")  # utf-8-sig = بدون BOM مشکل
    except Exception:
        return data
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        # حذف کوتیشن اطراف
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'\""):
            val = val[1:-1]
        if key:
            data[key] = val
    return data


def load_project_env(force: bool = False) -> Tuple[Optional[Path], List[str]]:
    global _LOADED_PATH, _LOGS
    if _LOADED_PATH is not None and not force:
        return _LOADED_PATH, list(_LOGS)

    logs: List[str] = []
    loaded: Optional[Path] = None

    logs.append(f"PACKAGE_DIR={PACKAGE_DIR}")
    logs.append(f"cwd={Path.cwd().resolve()}")

    for path in _candidates():
        exists = path.is_file()
        logs.append(f"check {path} exists={exists}")
        if not exists:
            continue

        # 1) python-dotenv
        load_dotenv(dotenv_path=path, override=True)
        # 2) پارس دستی و force به os.environ
        parsed = _parse_env_file(path)
        for k, v in parsed.items():
            if v:
                os.environ[k] = v
        logs.append(f"loaded keys from {path}: {sorted(parsed.keys())}")
        loaded = path
        break

    if loaded is None:
        logs.append("NO .env FILE FOUND in any candidate path")

    _LOADED_PATH = loaded
    _LOGS = logs
    return loaded, logs


def ensure_env_or_explain() -> Tuple[bool, str]:
    """True اگر هر دو کلید حاضر باشند."""
    load_project_env(force=True)
    gemini = (os.getenv("GEMINI_API_KEY") or "").strip()
    github = (os.getenv("GITHUB_TOKEN") or "").strip()

    if gemini and github:
        return True, f"OK env from {_LOADED_PATH}"

    missing = []
    if not gemini:
        missing.append("GEMINI_API_KEY")
    if not github:
        missing.append("GITHUB_TOKEN")

    lines = [
        "کلیدها پیدا نشد: " + ", ".join(missing),
        "",
        "یکی از این دو کار را انجام بده:",
        "",
        f"A) فایل بساز: {PACKAGE_ENV}",
        "   با این محتوا (بدون فاصله و بدون کوتیشن):",
        "   GEMINI_API_KEY=کلید_گوگل",
        "   GITHUB_TOKEN=توکن_گیت‌هاب",
        "",
        f"B) یا فایل ثابت در خانه: {HOME_ENV}",
        "   همان دو خط را آنجا بگذار — دیگر مهم نیست از کجا python را اجرا کنی.",
        "",
        "مسیرهایی که گشته شد:",
    ]
    for log in _LOGS:
        lines.append("  " + log)
    return False, "\n".join(lines)


def env_status() -> dict:
    load_project_env()
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
        "loaded_from": str(_LOADED_PATH) if _LOADED_PATH else None,
        "package_env": str(PACKAGE_ENV),
        "home_env": str(HOME_ENV),
    }


def write_env_template(target: Optional[Path] = None) -> Path:
    path = target or PACKAGE_ENV
    if not path.exists():
        path.write_text(
            "GEMINI_API_KEY=\nGITHUB_TOKEN=\n",
            encoding="utf-8",
        )
    return path
