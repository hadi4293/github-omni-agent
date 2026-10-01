#!/usr/bin/env python3
"""Entry that applies all patches then starts the web UI."""
from env_loader import load_project_env

load_project_env()

import agent as agent_mod
from memory_patch import apply_memory
from extra_tools_patch import apply_extra_tools
from android_patch import apply_android_tools

agent_mod.OmniAgent = apply_memory(
    apply_android_tools(apply_extra_tools(agent_mod.OmniAgent))
)

import uvicorn

print("GitHub Omni Agent (android + actions + memory)")
print("http://127.0.0.1:8000")
uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
