"""
هسته ایجنت - Gemini Function Calling + GitHub Tools
"""

from __future__ import annotations

import json
from typing import Any

import google.generativeai as genai
from rich.console import Console

from tools.github_tools import GitHubTools

console = Console()

SYSTEM_PROMPT = """تو یک ایجنت هوشمند و همه‌کاره برای گیت‌هاب هستی.
نام تو: GitHub Omni Agent

قوانین مهم:
1. همیشه به زبان کاربر پاسخ بده (فارسی یا انگلیسی).
2. برای هر کاری که لازم داری از ابزارهای موجود استفاده کن.
3. عملیات خطرناک (حذف فایل، حذف ریپو، force push، پاک کردن branch و ...) را فقط بعد از تأیید صریح کاربر انجام بده.
4. اگر اطلاعات کافی نداری (مثل نام ریپو، شماره issue و ...) اول بپرس.
5. پاسخ‌هایت کوتاه، واضح و مفید باشد.
6. وقتی عملیاتی انجام دادی، نتیجه را خلاصه و تمیز گزارش کن.

ابزارهایی که داری:
- لیست ریپوها، گرفتن محتوای فایل، ساخت/ویرایش فایل، ساخت issue، کامنت گذاشتن، ساخت PR، جستجوی کد، لیست issueها و PRها و خیلی چیزهای دیگر.
"""


class OmniAgent:
    def __init__(self, gemini_api_key: str, github_token: str):
        genai.configure(api_key=gemini_api_key)
        self.gh = GitHubTools(github_token)

        # تعریف ابزارها برای Gemini
        self.tools = self._build_tools()

        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=SYSTEM_PROMPT,
            tools=self.tools,
        )

        self.chat = self.model.start_chat(enable_automatic_function_calling=False)

    def _build_tools(self):
        """تعریف Function Declarations برای Gemini"""
        return [
            genai.protos.Tool(
                function_declarations=[
                    genai.protos.FunctionDeclaration(
                        name="list_my_repos",
                        description="لیست ریپوهای کاربر لاگین‌شده را برمی‌گرداند",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "limit": genai.protos.Schema(
                                    type=genai.protos.Type.INTEGER,
                                    description="حداکثر تعداد ریپو (پیش‌فرض 30)",
                                )
                            },
                        ),
                    ),
                    genai.protos.FunctionDeclaration(
                        name="get_file_content",
                        description="محتوای یک فایل از ریپو را می‌خواند",
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
                        description="یک فایل را می‌سازد یا ویرایش می‌کند و کامیت می‌زند",
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
                        description="یک فایل را حذف می‌کند (عملیات خطرناک - نیاز به تأیید دارد)",
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
                        description="یک issue جدید می‌سازد",
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
                        description="روی یک issue یا PR کامنت می‌گذارد",
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
                        name="create_pull_request",
                        description="یک Pull Request می‌سازد",
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
                        name="get_repo_tree",
                        description="ساختار فایل‌ها و پوشه‌های یک ریپو را برمی‌گرداند",
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
                        name="ask_confirmation",
                        description="از کاربر برای عملیات خطرناک تأیید می‌گیرد. فقط وقتی استفاده کن که واقعاً نیاز به تأیید داری.",
                        parameters=genai.protos.Schema(
                            type=genai.protos.Type.OBJECT,
                            properties={
                                "action_description": genai.protos.Schema(
                                    type=genai.protos.Type.STRING,
                                    description="توضیح دقیق کاری که می‌خواهی انجام دهی",
                                ),
                            },
                            required=["action_description"],
                        ),
                    ),
                ]
            )
        ]

    def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        """اجرای واقعی ابزارها"""
        try:
            if name == "list_my_repos":
                return self.gh.list_my_repos(limit=args.get("limit", 30))

            if name == "get_file_content":
                return self.gh.get_file_content(
                    args["owner"], args["repo"], args["path"], args.get("ref")
                )

            if name == "create_or_update_file":
                return self.gh.create_or_update_file(
                    args["owner"],
                    args["repo"],
                    args["path"],
                    args["content"],
                    args["message"],
                    args.get("branch", "main"),
                )

            if name == "delete_file":
                # این عملیات خطرناکه → اول تأیید می‌گیریم
                confirm = self._ask_user_confirmation(
                    f"حذف فایل `{args['path']}` از ریپوی `{args['owner']}/{args['repo']}`"
                )
                if not confirm:
                    return "کاربر تأیید نکرد. عملیات لغو شد."
                return self.gh.delete_file(
                    args["owner"],
                    args["repo"],
                    args["path"],
                    args["message"],
                    args.get("branch", "main"),
                )

            if name == "list_issues":
                return self.gh.list_issues(
                    args["owner"], args["repo"], args.get("state", "open")
                )

            if name == "create_issue":
                return self.gh.create_issue(
                    args["owner"],
                    args["repo"],
                    args["title"],
                    args.get("body", ""),
                    args.get("labels"),
                )

            if name == "add_issue_comment":
                return self.gh.add_issue_comment(
                    args["owner"],
                    args["repo"],
                    args["issue_number"],
                    args["body"],
                )

            if name == "create_pull_request":
                return self.gh.create_pull_request(
                    args["owner"],
                    args["repo"],
                    args["title"],
                    args.get("body", ""),
                    args["head"],
                    args["base"],
                )

            if name == "search_code":
                return self.gh.search_code(args["query"])

            if name == "get_repo_tree":
                return self.gh.get_repo_tree(
                    args["owner"], args["repo"], args.get("path", "")
                )

            if name == "ask_confirmation":
                confirmed = self._ask_user_confirmation(args["action_description"])
                return "تأیید شد" if confirmed else "رد شد"

            return f"ابزار ناشناخته: {name}"

        except Exception as e:
            return f"خطا در اجرای {name}: {str(e)}"

    def _ask_user_confirmation(self, description: str) -> bool:
        console.print(
            f"\n[bold yellow]⚠ عملیات خطرناک:[/bold yellow] {description}"
        )
        answer = console.input("[bold]آیا مطمئنی؟ (yes/y یا no/n) › [/bold]").strip().lower()
        return answer in ("yes", "y", "بله", "آره")

    def run(self, user_message: str) -> str:
        """یک دور مکالمه با ایجنت"""
        response = self.chat.send_message(user_message)

        # حلقه function calling
        while True:
            # اگر function call وجود داشت
            function_calls = []
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    function_calls.append(part.function_call)

            if not function_calls:
                # پاسخ نهایی متنی
                text_parts = [
                    part.text
                    for part in response.candidates[0].content.parts
                    if part.text
                ]
                return "\n".join(text_parts) if text_parts else "پاسخی دریافت نشد."

            # اجرای همه function callها
            function_responses = []
            for fc in function_calls:
                name = fc.name
                args = dict(fc.args) if fc.args else {}
                console.print(f"[dim]→ در حال اجرای ابزار: {name}[/dim]")
                result = self._execute_tool(name, args)

                function_responses.append(
                    genai.protos.Part(
                        function_response=genai.protos.FunctionResponse(
                            name=name,
                            response={"result": result},
                        )
                    )
                )

            # ارسال نتایج به مدل
            response = self.chat.send_message(function_responses)
