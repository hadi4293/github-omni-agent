#!/usr/bin/env python3
"""Start web UI with Actions + Android + Memory patches forced on."""
from env_loader import load_project_env

load_project_env()

from memory_patch import apply_memory
from extra_tools_patch import apply_extra_tools
from android_patch import apply_android_tools

import web_app

# web_app may have partially patched OmniAgent; force full stack
web_app.OmniAgent = apply_memory(
    apply_android_tools(apply_extra_tools(web_app.OmniAgent))
)
web_app._agent = None  # تا با کلاس پچ‌شده دوباره ساخته شود

import uvicorn

print("GitHub Omni Agent")
print("  features: memory + actions/releases/codespaces + android scaffold")
print("  http://127.0.0.1:8000\n")
uvicorn.run(web_app.app, host="127.0.0.1", port=8000, reload=False)
