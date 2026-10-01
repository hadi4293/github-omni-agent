#!/usr/bin/env python3
"""
اجرای وب با پچ‌های کامل + لود قطعی .env
همیشه از این فایل اجرا کن:
    python run_web.py
"""

import sys
from pathlib import Path

# تضمین: پوشه پروژه در sys.path باشد حتی اگر از جای دیگر صدا زده شود
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env_loader import load_project_env, ensure_env_or_explain, env_status, PACKAGE_ENV, HOME_ENV

path, logs = load_project_env(force=True)
print("[env] --------")
for line in logs:
    print("[env]", line)
st = env_status()
print("[env] status:", st)
print("[env] --------")

ok, msg = ensure_env_or_explain()
if not ok:
    print("\n" + msg + "\n")
    print("بعد از ساخت .env دوباره اجرا کن: python run_web.py")
    sys.exit(1)

from memory_patch import apply_memory
from extra_tools_patch import apply_extra_tools
from android_patch import apply_android_tools

import web_app

web_app.OmniAgent = apply_memory(
    apply_android_tools(apply_extra_tools(web_app.OmniAgent))
)
web_app._agent = None

import uvicorn

print("GitHub Omni Agent")
print(f"  .env: {path}")
print("  features: memory + actions + android")
print("  http://127.0.0.1:8000\n")
uvicorn.run(web_app.app, host="127.0.0.1", port=8000, reload=False)
