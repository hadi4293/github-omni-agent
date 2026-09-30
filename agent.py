"""
هسته ایجنت - Gemini Function Calling + تمام ابزارهای گیت‌هاب
مدل: gemini-3.5-flash-lite
"""

from __future__ import annotations

from typing import Any, Optional, Callable

import google.generativeai as genai
from google.generativeai.types import generation_types

from tools.github_tools import GitHubTools

SYSTEM_PROMPT = """تو یک ایجنت هوشمند و همه‌کاره برای گیت‌هاب هستی.
نام تو: GitHub Omni Agent

قوانین مهم و اجباری:
1. همیشه به زبان کاربر پاسخ بده (فارسی یا انگلیسی).
2. برای هر کاری که لازم داری از ابزارهای موجود استفاده کن. حدس نزن.
3. عملیات خطرناک را فقط بعد از تأیید صریح کاربر انجام بده:
   - حذف فایل
   - حذف ریپوزیتوری
   - Merge کردن Pull Request
4. اگر اطلاعات کافی نداری (نام ریپو، شماره issue، نام برنچ و ...) اول بپرس.
5. پاسخ‌هایت کوتاه، واضح، مرتب و مفید باشد.
6. وقتی عملیاتی انجام دادی، نتیجه را خلاصه و تمیز گزارش کن.
7. هرگز توکن یا کلید API را در پاسخ‌ها نشان نده.
"""

# مدل‌های جایگزین اگر مدل اصلی در دسترس نبود
MODEL_CANDIDATES = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


class OmniAgent:
    def __init__(
        self,
        gemini_api_key: str,
        github_token: str,
        confirm_callback: Optional[Callable[[str], bool]] = None,
    ):
        genai.configure(api_key=gemini_api_key)
        self.gh = GitHubTools(github_token)
        self.confirm_callback = confirm_callback
        self.tools = self._build_tools()
        self.model_name = None
        self.model = None
        self.chat = None
        self._init_model()

    def _init_model(self):
        last_err = None
        for name in MODEL_CANDIDATES:
            try:
                model = genai.GenerativeModel(
                    model_name=name,
                    system_instruction=SYSTEM_PROMPT,
                    tools=self.tools,
                )
                # تست خیلی سبک — فقط ساخت مدل کافی است
                self.model = model
                self.model_name = name
                self.chat = self.model.start_chat(enable_automatic_function_calling=False)
                print(f"[agent] using model: {name}")
                return
            except Exception as e:
                last_err = e
                print(f"[agent] model {name} failed: {e}")
        raise RuntimeError(f"هیچ مدل Gemini در دسترس نبود. آخرین خطا: {last_err}")

    def _build_tools(self):
        return [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name="list_my_repos",
                        description="لیست ریپوهای کاربر لاگین‌شده",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "limit": genai.protos.Schema(
                                    type=genai.protos.Type.INTEGER,
                                    description="حداکثر تعداد (پیش‌فرض ۳۰)",
                                )
                            },
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="create_repo",
                        description="ساخت ریپوزیتوری جدید",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "name": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "description": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "private": genai.protos.Schema(type=genai.protos.Type.BOOLEAN),
                                "auto_init": genai.protos.Schema(type=genai.protos.Type.BOOLEAN),
                            },
                            required=["name"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="delete_repo",
                        description="حذف کامل یک ریپوزیتوری (خطرناک - نیاز به تأیید)",
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
                        name="get_repo_tree",
                        description="ساختار فایل‌ها و پوشه‌های یک ریپو",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "path": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["owner", "repo"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="star_repo",
                        description="ستاره دادن به یک ریپو",
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
                        name="unstar_repo",
                        description="برداشتن ستاره از یک ریپو",
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
                        name="get_file_content",
                        description="خواندن محتوای یک فایل",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "path": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "ref": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["owner", "repo", "path"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="create_or_update_file",
                        description="ساخت یا ویرایش فایل و کامیت کردن",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "path": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "content": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "message": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "branch": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["owner", "repo", "path", "content", "message"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="delete_file",
                        description="حذف فایل (خطرناک - نیاز به تأیید)",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "path": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "message": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "branch": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["owner", "repo", "path", "message"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="list_issues",
                        description="لیست issueهای یک ریپو",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "state": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["owner", "repo"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="create_issue",
                        description="ساخت issue جدید",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "title": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "body": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "labels": genai.protos.Schema(
                                    type=genai.protos.Type.ARRAY,
                                    items=genai.protos.Schema(type=genai.protos.Type.STRING),
                                ),
                            },
                            required=["owner", "repo", "title"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="add_issue_comment",
                        description="کامنت گذاشتن روی issue یا PR",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "issue_number": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                                "body": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["owner", "repo", "issue_number", "body"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="close_issue",
                        description="بستن یک issue",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "issue_number": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                            },
                            required=["owner", "repo", "issue_number"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="reopen_issue",
                        description="باز کردن مجدد یک issue",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "issue_number": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                            },
                            required=["owner", "repo", "issue_number"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="update_issue",
                        description="ویرایش عنوان یا بدنه یک issue",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "issue_number": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                                "title": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "body": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["owner", "repo", "issue_number"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="list_pull_requests",
                        description="لیست Pull Requestهای یک ریپو",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "state": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["owner", "repo"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="create_pull_request",
                        description="ساخت Pull Request",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "title": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "body": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "head": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "base": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["owner", "repo", "title", "head", "base"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="merge_pull_request",
                        description="Merge کردن یک Pull Request (خطرناک - نیاز به تأیید)",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "pr_number": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                                "commit_message": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["owner", "repo", "pr_number"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="close_pull_request",
                        description="بستن یک Pull Request بدون merge",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "pr_number": genai.protos.Schema(type=genai.protos.Type.INTEGER),
                            },
                            required=["owner", "repo", "pr_number"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="list_branches",
                        description="لیست برنچ‌های یک ریپو",
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
                        name="create_branch",
                        description="ساخت برنچ جدید",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "branch_name": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "from_branch": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["owner", "repo", "branch_name"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="list_commits",
                        description="لیست آخرین کامیت‌های یک ریپو",
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
                        name="search_code",
                        description="جستجوی کد در گیت‌هاب",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "query": genai.protos.Schema(type=genai.protos.Type.STRING),
                            },
                            required=["query"],
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_me",
                        description="اطلاعات حساب کاربری لاگین‌شده",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={},
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="create_gist",
                        description="ساخت یک Gist",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "filename": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "content": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "description": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "public": genai.protos.Schema(type=genai.protos.Type.BOOLEAN),
                            },
                            required=["filename", "content"],
                        ),
                    ),
                ]
            )
        ]

    def _ask_confirmation(self, description: str) -> bool:
        if self.confirm_callback:
            return self.confirm_callback(description)
        try:
            from rich.console import Console
            c = Console()
            c.print(f"\n[bold yellow]⚠ عملیات خطرناک:[/bold yellow] {description}")
            answer = c.input("[bold]آیا مطمئنی؟ (yes/y/بله) › [/bold]").strip().lower()
            return answer in ("yes", "y", "بله", "آره", "باشه")
        except Exception:
            return False

    def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        try:
            if name == "delete_file":
                ok = self._ask_confirmation(
                    f"حذف فایل `{args.get('path')}` از `{args.get('owner')}/{args.get('repo')}`"
                )
                if not ok:
                    return "کاربر تأیید نکرد. عملیات لغو شد."
                return self.gh.delete_file(
                    args["owner"], args["repo"], args["path"],
                    args["message"], args.get("branch", "main"),
                )

            if name == "delete_repo":
                ok = self._ask_confirmation(
                    f"حذف کامل و دائمی ریپوی `{args.get('owner')}/{args.get('repo')}`"
                )
                if not ok:
                    return "کاربر تأیید نکرد. عملیات لغو شد."
                return self.gh.delete_repo(args["owner"], args["repo"])

            if name == "merge_pull_request":
                ok = self._ask_confirmation(
                    f"Merge کردن PR #{args.get('pr_number')} در `{args.get('owner')}/{args.get('repo')}`"
                )
                if not ok:
                    return "کاربر تأیید نکرد. عملیات لغو شد."
                return self.gh.merge_pull_request(
                    args["owner"], args["repo"], args["pr_number"],
                    args.get("commit_message", ""),
                )

            mapping = {
                "list_my_repos": lambda: self.gh.list_my_repos(args.get("limit", 30)),
                "create_repo": lambda: self.gh.create_repo(
                    args["name"], args.get("description", ""),
                    args.get("private", True), args.get("auto_init", True),
                ),
                "get_repo_tree": lambda: self.gh.get_repo_tree(
                    args["owner"], args["repo"], args.get("path", "")
                ),
                "star_repo": lambda: self.gh.star_repo(args["owner"], args["repo"]),
                "unstar_repo": lambda: self.gh.unstar_repo(args["owner"], args["repo"]),
                "get_file_content": lambda: self.gh.get_file_content(
                    args["owner"], args["repo"], args["path"], args.get("ref")
                ),
                "create_or_update_file": lambda: self.gh.create_or_update_file(
                    args["owner"], args["repo"], args["path"],
                    args["content"], args["message"], args.get("branch", "main"),
                ),
                "list_issues": lambda: self.gh.list_issues(
                    args["owner"], args["repo"], args.get("state", "open")
                ),
                "create_issue": lambda: self.gh.create_issue(
                    args["owner"], args["repo"], args["title"],
                    args.get("body", ""), args.get("labels"),
                ),
                "add_issue_comment": lambda: self.gh.add_issue_comment(
                    args["owner"], args["repo"], args["issue_number"], args["body"]
                ),
                "close_issue": lambda: self.gh.close_issue(
                    args["owner"], args["repo"], args["issue_number"]
                ),
                "reopen_issue": lambda: self.gh.reopen_issue(
                    args["owner"], args["repo"], args["issue_number"]
                ),
                "update_issue": lambda: self.gh.update_issue(
                    args["owner"], args["repo"], args["issue_number"],
                    args.get("title"), args.get("body"),
                ),
                "list_pull_requests": lambda: self.gh.list_pull_requests(
                    args["owner"], args["repo"], args.get("state", "open")
                ),
                "create_pull_request": lambda: self.gh.create_pull_request(
                    args["owner"], args["repo"], args["title"],
                    args.get("body", ""), args["head"], args["base"],
                ),
                "close_pull_request": lambda: self.gh.close_pull_request(
                    args["owner"], args["repo"], args["pr_number"]
                ),
                "list_branches": lambda: self.gh.list_branches(args["owner"], args["repo"]),
                "create_branch": lambda: self.gh.create_branch(
                    args["owner"], args["repo"], args["branch_name"],
                    args.get("from_branch", "main"),
                ),
                "list_commits": lambda: self.gh.list_commits(
                    args["owner"], args["repo"], args.get("limit", 10)
                ),
                "search_code": lambda: self.gh.search_code(args["query"]),
                "get_me": lambda: self.gh.get_me(),
                "create_gist": lambda: self.gh.create_gist(
                    args["filename"], args["content"],
                    args.get("description", ""), args.get("public", False),
                ),
            }

            if name in mapping:
                return mapping[name]()
            return f"ابزار ناشناخته: {name}"

        except Exception as e:
            return f"خطا در اجرای {name}: {type(e).__name__}: {e}"

    def _extract_parts(self, response):
        """استخراج امن function_call و text از پاسخ Gemini"""
        function_calls = []
        texts = []

        try:
            cands = getattr(response, "candidates", None) or []
            if not cands:
                # گاهی prompt feedback دارد
                feedback = getattr(response, "prompt_feedback", None)
                if feedback:
                    return [], [f"پاسخ مدل خالی بود. feedback: {feedback}"]
                return [], ["پاسخ مدل خالی بود (candidates خالی)."]

            content = getattr(cands[0], "content", None)
            if not content:
                finish = getattr(cands[0], "finish_reason", None)
                return [], [f"محتوای پاسخ خالی بود. finish_reason={finish}"]

            parts = getattr(content, "parts", None) or []
            for part in parts:
                fc = getattr(part, "function_call", None)
                if fc and getattr(fc, "name", None):
                    function_calls.append(fc)
                t = getattr(part, "text", None)
                if t:
                    texts.append(t)
        except Exception as e:
            return [], [f"خطا در خواندن پاسخ مدل: {e}"]

        return function_calls, texts

    def run(self, user_message: str) -> str:
        try:
            response = self.chat.send_message(user_message)
        except Exception as e:
            return f"خطا در ارتباط با Gemini ({self.model_name}): {type(e).__name__}: {e}"

        # حداکثر چند دور function calling
        for _ in range(8):
            function_calls, texts = self._extract_parts(response)

            if not function_calls:
                return "\n".join(texts) if texts else "پاسخی از مدل دریافت نشد."

            function_responses = []
            for fc in function_calls:
                name = fc.name
                try:
                    args = dict(fc.args) if fc.args else {}
                except Exception:
                    args = {}
                print(f"[agent] tool: {name} args={args}")
                result = self._execute_tool(name, args)
                function_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=name,
                            response={"result": result},
                        )
                    )
                )

            try:
                response = self.chat.send_message(function_responses)
            except Exception as e:
                return f"خطا بعد از اجرای ابزار: {type(e).__name__}: {e}"

        return "تعداد دورهای ابزار بیش از حد شد. لطفاً دوباره تلاش کن."
