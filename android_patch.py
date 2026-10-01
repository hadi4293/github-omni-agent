"""
ثبت ابزار ساخت اپ اندروید از صفر تا APK/Release
"""

from __future__ import annotations

from typing import Any

import google.generativeai as genai

from tools.android_builder import scaffold_android_in_repo

ANDROID_DECLARATIONS = [
    genai.protos.FunctionDeclaration(
        name="scaffold_android_app",
        description=(
            "ساخت کامل اسکلت یک اپ اندروید Kotlin از صفر داخل ریپو: "
            "Gradle، Manifest، MainActivity، UI ساده، و GitHub Actions برای بیلد APK و Release. "
            "برای درخواست‌هایی مثل ساخت اپ اندروید / تبدیل به APK / انتشار ریلز از این ابزار استفاده کن."
        ),
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                "app_name": genai.protos.Schema(
                    type=genai.protos.Type.STRING,
                    description="نام نمایشی اپ، مثلاً MyShop",
                ),
                "package_name": genai.protos.Schema(
                    type=genai.protos.Type.STRING,
                    description="مثل com.example.myshop",
                ),
                "branch": genai.protos.Schema(type=genai.protos.Type.STRING),
            },
            required=["owner", "repo", "app_name", "package_name"],
        ),
    ),
]


def apply_android_tools(agent_cls):
    if getattr(agent_cls, "_android_patched", False):
        return agent_cls

    _orig_build = agent_cls._build_tools
    _orig_exec = agent_cls._execute_tool

    def _build_tools(self):
        tools = _orig_build(self)
        try:
            existing = list(tools[0].function_declarations)
            existing.extend(ANDROID_DECLARATIONS)
            tools = [genai.protos.Tool(function_declarations=existing)]
        except Exception as e:
            print("[android_patch] declarations:", e)
        return tools

    def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        if name == "scaffold_android_app":
            try:
                return scaffold_android_in_repo(
                    self.gh,
                    args["owner"],
                    args["repo"],
                    args["app_name"],
                    args["package_name"],
                    args.get("branch", "main"),
                )
            except Exception as e:
                return f"خطا در scaffold_android_app: {type(e).__name__}: {e}"
        return _orig_exec(self, name, args)

    agent_cls._build_tools = _build_tools
    agent_cls._execute_tool = _execute_tool
    agent_cls._android_patched = True
    return agent_cls
