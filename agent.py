"""
هسته ایجنت - Gemini Function Calling + تمام ابزارهای گیت‌هاب
نسخه نهایی و کامل
"""

from __future__ import annotations

from typing import Any

import google.generativeai as genai
from rich.console import Console

from tools.github_tools import GitHubTools

console = Console()

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


class OmniAgent:
    def __init__(self, gemini_api_key: str, github_token: str):
        genai.configure(api_key=gemini_api_key)
        self.gh = GitHubTools(github_token)

        self.tools = self._build_tools()

        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT,
            tools=self.tools,
        )

        self.chat = self.model.start_chat(enable_automatic_function_calling=False)

    def _build_tools(self):
        return [
            genai.protos.Tool(
                function_declarations=[
                    # ── Repo ──
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
                                "private": genai.protos.Schema(
                                    type=genai.protos.Type.BOOLEAN,
                                    description="خصوصی باشد؟ پیش‌فرض true",
                                ),
                                "auto_init": genai.protos.Schema(
                                    type=genai.protos.Type.BOOLEAN,
                                    description="با README ساخته شود؟ پیش‌فرض true",
                                ),
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
                                "path": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="مسیر پوشه (اختیاری)",
                                ),
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
                    # ── File ──
                    genai.protos.FunctionDeclaration(
                        name="get_file_content",
                        description="خواندن محتوای یک فایل",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "path": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "ref": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="برنچ یا تگ (اختیاری)",
                                ),
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
                                "message": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="پیام کامیت",
                                ),
                                "branch": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="برنچ (پیش‌فرض main)",
                                ),
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
                    # ── Issue ──
                    genai.protos.FunctionDeclaration(
                        name="list_issues",
                        description="لیست issueهای یک ریپو",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "state": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="open | closed | all",
                                ),
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
                    # ── Pull Request ──
                    genai.protos.FunctionDeclaration(
                        name="list_pull_requests",
                        description="لیست Pull Requestهای یک ریپو",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "owner": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "repo": genai.protos.Schema(type=genai.protos.Type.STRING),
                                "state": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="open | closed | all",
                                ),
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
                                "head": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="برنچ مبدأ",
                                ),
                                "base": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="برنچ مقصد (معمولاً main)",
                                ),
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
                    # ── Branch & Commit ──
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
                                "from_branch": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="برنچ مبدأ (پیش‌فرض main)",
                                ),
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
                                "limit": genai.protos.Schema(
                                    type=genai.protos.Type.INTEGER,
                                    description="تعداد کامیت (پیش‌فرض ۱۰)",
                                ),
                            },
                            required=["owner", "repo"],
                        ),
                    ),
                    # ── Search & User ──
                    genai.protos.FunctionDeclaration(
                        name="search_code",
                        description="جستجوی کد در گیت‌هاب",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "query": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="کوئری جستجو (مثلاً repo:owner/repo language:python)",
                                ),
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
                                "public": genai.protos.Schema(
                                    type=genai.protos.Type.BOOLEAN,
                                    description="عمومی باشد؟ پیش‌فرض false",
                                ),
                            },
                            required=["filename", "content"],
                        ),
                    ),
                ]
            )
        ]

    def _ask_user_confirmation(self, description: str) -> bool:
        console.print(f"\n[bold yellow]⚠ عملیات خطرناک:[/bold yellow] {description}")
        answer = (
            console.input("[bold]آیا مطمئنی؟ (yes / y / بله) یا (no / n / خیر) › [/bold]")
            .strip()
            .lower()
        )
        return answer in ("yes", "y", "بله", "آره", "باشه")

    def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        try:
            # ── عملیات خطرناک که نیاز به تأیید دارند ──
            if name == "delete_file":
                ok = self._ask_user_confirmation(
                    f"حذف فایل `{args['path']}` از `{args['owner']}/{args['repo']}`"
                )
                if not ok:
                    return "کاربر تأیید نکرد. عملیات لغو شد."
                return self.gh.delete_file(
                    args["owner"],
                    args["repo"],
                    args["path"],
                    args["message"],
                    args.get("branch", "main"),
                )

            if name == "delete_repo":
                ok = self._ask_user_confirmation(
                    f"حذف کامل و دائمی ریپوی `{args['owner']}/{args['repo']}`"
                )
                if not ok:
                    return "کاربر تأیید نکرد. عملیات لغو شد."
                return self.gh.delete_repo(args["owner"], args["repo"])

            if name == "merge_pull_request":
                ok = self._ask_user_confirmation(
                    f"Merge کردن PR #{args['pr_number']} در `{args['owner']}/{args['repo']}`"
                )
                if not ok:
                    return "کاربر تأیید نکرد. عملیات لغو شد."
                return self.gh.merge_pull_request(
                    args["owner"],
                    args["repo"],
                    args["pr_number"],
                    args.get("commit_message", ""),
                )

            # ── بقیه ابزارها ──
            mapping = {
                "list_my_repos": lambda: self.gh.list_my_repos(args.get("limit", 30)),
                "create_repo": lambda: self.gh.create_repo(
                    args["name"],
                    args.get("description", ""),
                    args.get("private", True),
                    args.get("auto_init", True),
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
                    args["owner"],
                    args["repo"],
                    args["path"],
                    args["content"],
                    args["message"],
                    args.get("branch", "main"),
                ),
                "list_issues": lambda: self.gh.list_issues(
                    args["owner"], args["repo"], args.get("state", "open")
                ),
                "create_issue": lambda: self.gh.create_issue(
                    args["owner"],
                    args["repo"],
                    args["title"],
                    args.get("body", ""),
                    args.get("labels"),
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
                    args["owner"],
                    args["repo"],
                    args["issue_number"],
                    args.get("title"),
                    args.get("body"),
                ),
                "list_pull_requests": lambda: self.gh.list_pull_requests(
                    args["owner"], args["repo"], args.get("state", "open")
                ),
                "create_pull_request": lambda: self.gh.create_pull_request(
                    args["owner"],
                    args["repo"],
                    args["title"],
                    args.get("body", ""),
                    args["head"],
                    args["base"],
                ),
                "close_pull_request": lambda: self.gh.close_pull_request(
                    args["owner"], args["repo"], args["pr_number"]
                ),
                "list_branches": lambda: self.gh.list_branches(args["owner"], args["repo"]),
                "create_branch": lambda: self.gh.create_branch(
                    args["owner"],
                    args["repo"],
                    args["branch_name"],
                    args.get("from_branch", "main"),
                ),
                "list_commits": lambda: self.gh.list_commits(
                    args["owner"], args["repo"], args.get("limit", 10)
                ),
                "search_code": lambda: self.gh.search_code(args["query"]),
                "get_me": lambda: self.gh.get_me(),
                "create_gist": lambda: self.gh.create_gist(
                    args["filename"],
                    args["content"],
                    args.get("description", ""),
                    args.get("public", False),
                ),
            }

            if name in mapping:
                return mapping[name]()

            return f"ابزار ناشناخته: {name}"

        except Exception as e:
            return f"خطا در اجرای {name}: {str(e)}"

    def run(self, user_message: str) -> str:
        response = self.chat.send_message(user_message)

        while True:
            function_calls = []
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_calls.append(part.function_call)

            if not function_calls:
                text_parts = [
                    part.text
                    for part in response.candidates[0].content.parts
                    if part.text
                ]
                return "\n".join(text_parts) if text_parts else "پاسخی دریافت نشد."

            function_responses = []
            for fc in function_calls:
                name = fc.name
                args = dict(fc.args) if fc.args else {}
                console.print(f"[dim]→ اجرای ابزار: {name}[/dim]")
                result = self._execute_tool(name, args)

                function_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=name,
                            response={"result": result},
                        )
                    )
                )

            response = self.chat.send_message(function_responses)
