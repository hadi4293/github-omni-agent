"""
ثبت ابزارهای Actions / Releases / Codespaces در ایجنت
"""

from __future__ import annotations

from typing import Any

import google.generativeai as genai

from tools.extra_tools import attach_extra_methods
from tools.github_tools import GitHubTools


# متدها را یک‌بار به کلاس بچسبان
attach_extra_methods(GitHubTools)

EXTRA_DECLARATIONS = [
    genai.protos.FunctionDeclaration(
        name="list_workflows",
        description="لیست workflowهای GitHub Actions یک ریپو",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
            },
            required=["owner", "repo"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="list_workflow_runs",
        description="لیست آخرین اجراهای GitHub Actions",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                "limit": genai.protos.Schema(type=genai.protos.Type.INTEGER),
            },
            required=["owner", "repo"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="trigger_workflow",
        description="اجرای دستی یک workflow (باید workflow_dispatch داشته باشد)",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                "workflow_id": genai.protos.Schema(
                    type=genai.protos.Type.STRING,
                    description="نام فایل مثل ci.yml یا id عددی",
                ),
                "ref": genai.protos.Schema(type=genai.protos.Type.STRING),
            },
            required=["owner", "repo", "workflow_id"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="get_workflow_run",
        description="جزئیات یک workflow run",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                "run_id": genai.protos.Schema(type=genai.protos.Type.INTEGER),
            },
            required=["owner", "repo", "run_id"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="cancel_workflow_run",
        description="لغو یک workflow run در حال اجرا",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                "run_id": genai.protos.Schema(type=genai.protos.Type.INTEGER),
            },
            required=["owner", "repo", "run_id"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="rerun_workflow_run",
        description="اجرای مجدد یک workflow run",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                "run_id": genai.protos.Schema(type=genai.protos.Type.INTEGER),
            },
            required=["owner", "repo", "run_id"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="list_releases",
        description="لیست Releaseهای یک ریپو",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                "limit": genai.protos.Schema(type=genai.protos.Type.INTEGER),
            },
            required=["owner", "repo"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="get_latest_release",
        description="آخرین Release یک ریپو",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
            },
            required=["owner", "repo"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="create_release",
        description="ساخت Release جدید با تگ",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                "tag_name": genai.protos.Schema(type=genai.protos.Type.STRING),
                "name": genai.protos.Schema(type=genai.protos.Type.STRING),
                "body": genai.protos.Schema(type=genai.protos.Type.STRING),
                "draft": genai.protos.Schema(type=genai.protos.Type.BOOLEAN),
                "prerelease": genai.protos.Schema(type=genai.protos.Type.BOOLEAN),
                "target_commitish": genai.protos.Schema(type=genai.protos.Type.STRING),
            },
            required=["owner", "repo", "tag_name"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="delete_release",
        description="حذف یک Release (خطرناک - نیاز به تأیید)",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                "release_id": genai.protos.Schema(type=genai.protos.Type.INTEGER),
            },
            required=["owner", "repo", "release_id"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="list_codespaces",
        description="لیست Codespaceهای کاربر",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "limit": genai.protos.Schema(type=genai.protos.Type.INTEGER),
            },
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="create_codespace",
        description="ساخت Codespace برای یک ریپو",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                "ref": genai.protos.Schema(type=genai.protos.Type.STRING),
                "machine": genai.protos.Schema(type=genai.protos.Type.STRING),
            },
            required=["owner", "repo"],
        ),
    ),
    genai.protos.FunctionDeclaration(
        name="delete_codespace",
        description="حذف یک Codespace (خطرناک - نیاز به تأیید)",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "codespace_name": genai.protos.Schema(type=genai.protos.Type.STRING),
            },
            required=["codespace_name"],
        ),
    ),
]


def apply_extra_tools(agent_cls):
    if getattr(agent_cls, "_extra_tools_patched", False):
        return agent_cls

    _orig_build = agent_cls._build_tools
    _orig_exec = agent_cls._execute_tool

    def _build_tools(self):
        tools = _orig_build(self)
        # tools[0] is Tool with function_declarations list-like
        try:
            existing = list(tools[0].function_declarations)
            existing.extend(EXTRA_DECLARATIONS)
            tools = [genai.protos.Tool(function_declarations=existing)]
        except Exception as e:
            print("[extra_tools] merge declarations failed:", e)
        return tools

    def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        # تأیید برای عملیات خطرناک جدید
        if name == "delete_release":
            ok = self._ask_confirmation(
                f"حذف Release id={args.get('release_id')} از {args.get('owner')}/{args.get('repo')}"
            )
            if not ok:
                return "کاربر تأیید نکرد. عملیات لغو شد."
            return self.gh.delete_release(args["owner"], args["repo"], int(args["release_id"]))

        if name == "delete_codespace":
            ok = self._ask_confirmation(f"حذف Codespace `{args.get('codespace_name')}`")
            if not ok:
                return "کاربر تأیید نکرد. عملیات لغو شد."
            return self.gh.delete_codespace(args["codespace_name"])

        extra_map = {
            "list_workflows": lambda: self.gh.list_workflows(args["owner"], args["repo"]),
            "list_workflow_runs": lambda: self.gh.list_workflow_runs(
                args["owner"], args["repo"], args.get("limit", 10)
            ),
            "trigger_workflow": lambda: self.gh.trigger_workflow(
                args["owner"], args["repo"], args["workflow_id"], args.get("ref", "main")
            ),
            "get_workflow_run": lambda: self.gh.get_workflow_run(
                args["owner"], args["repo"], int(args["run_id"])
            ),
            "cancel_workflow_run": lambda: self.gh.cancel_workflow_run(
                args["owner"], args["repo"], int(args["run_id"])
            ),
            "rerun_workflow_run": lambda: self.gh.rerun_workflow_run(
                args["owner"], args["repo"], int(args["run_id"])
            ),
            "list_releases": lambda: self.gh.list_releases(
                args["owner"], args["repo"], args.get("limit", 10)
            ),
            "get_latest_release": lambda: self.gh.get_latest_release(
                args["owner"], args["repo"]
            ),
            "create_release": lambda: self.gh.create_release(
                args["owner"],
                args["repo"],
                args["tag_name"],
                args.get("name", ""),
                args.get("body", ""),
                args.get("draft", False),
                args.get("prerelease", False),
                args.get("target_commitish", "main"),
            ),
            "list_codespaces": lambda: self.gh.list_codespaces(args.get("limit", 15)),
            "create_codespace": lambda: self.gh.create_codespace(
                args["owner"],
                args["repo"],
                args.get("ref", "main"),
                args.get("machine", "basicLinux32gb"),
            ),
        }

        if name in extra_map:
            try:
                return extra_map[name]()
            except Exception as e:
                return f"خطا در {name}: {type(e).__name__}: {e}"

        return _orig_exec(self, name, args)

    agent_cls._build_tools = _build_tools
    agent_cls._execute_tool = _execute_tool
    agent_cls._extra_tools_patched = True
    return agent_cls
