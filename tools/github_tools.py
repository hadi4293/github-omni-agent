"""
تمام ابزارهای گیت‌هاب برای ایجنت
"""

from __future__ import annotations

import base64
from typing import Optional

from github import Github, GithubException, InputGitTreeElement
from github.Repository import Repository


class GitHubTools:
    def __init__(self, token: str):
        self.g = Github(token)
        self.user = self.g.get_user()

    def list_my_repos(self, limit: int = 30) -> str:
        repos = list(self.user.get_repos(sort="updated"))[:limit]
        if not repos:
            return "هیچ ریپویی پیدا نشد."

        lines = ["### ریپوهای تو:\n"]
        for r in repos:
            visibility = "🔒 خصوصی" if r.private else "🌐 عمومی"
            lang = r.language or "—"
            lines.append(
                f"- **{r.full_name}** ({visibility}) | زبان: {lang} | "
                f"⭐ {r.stargazers_count} | آپدیت: {r.updated_at.strftime('%Y-%m-%d')}"
            )
        return "\n".join(lines)

    def get_file_content(
        self, owner: str, repo: str, path: str, ref: Optional[str] = None
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            kwargs = {"ref": ref} if ref else {}
            content = r.get_contents(path, **kwargs)

            if isinstance(content, list):
                return f"`{path}` یک پوشه است، نه فایل. از get_repo_tree استفاده کن."

            if content.encoding == "base64":
                text = base64.b64decode(content.content).decode("utf-8", errors="replace")
            else:
                text = content.content or ""

            # محدود کردن طول برای جلوگیری از پاسخ خیلی بلند
            if len(text) > 15000:
                text = text[:15000] + "\n\n... [محتوا خیلی طولانی بود و کوتاه شد]"

            return f"### فایل: `{path}`\n```\n{text}\n```"

        except GithubException as e:
            return f"خطا در خواندن فایل: {e.data.get('message', str(e))}"

    def create_or_update_file(
        self,
        owner: str,
        repo: str,
        path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")

            try:
                existing = r.get_contents(path, ref=branch)
                # آپدیت
                result = r.update_file(
                    path=path,
                    message=message,
                    content=content,
                    sha=existing.sha,
                    branch=branch,
                )
                action = "آپدیت شد"
            except GithubException:
                # ساخت جدید
                result = r.create_file(
                    path=path,
                    message=message,
                    content=content,
                    branch=branch,
                )
                action = "ساخته شد"

            commit_sha = result["commit"].sha[:7]
            return f"✅ فایل `{path}` با موفقیت {action}.\nکامیت: `{commit_sha}`\nپیام: {message}"

        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def delete_file(
        self,
        owner: str,
        repo: str,
        path: str,
        message: str,
        branch: str = "main",
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            contents = r.get_contents(path, ref=branch)

            if isinstance(contents, list):
                return "نمی‌توان پوشه را مستقیماً حذف کرد. فقط فایل پشتیبانی می‌شود."

            r.delete_file(
                path=path,
                message=message,
                sha=contents.sha,
                branch=branch,
            )
            return f"✅ فایل `{path}` با موفقیت حذف شد."

        except GithubException as e:
            return f"خطا در حذف فایل: {e.data.get('message', str(e))}"

    def list_issues(self, owner: str, repo: str, state: str = "open") -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            issues = list(r.get_issues(state=state))[:20]

            if not issues:
                return f"هیچ issue با وضعیت `{state}` پیدا نشد."

            lines = [f"### Issueهای `{owner}/{repo}` (state={state}):\n"]
            for i in issues:
                labels = ", ".join(l.name for l in i.labels) or "—"
                lines.append(
                    f"- **#{i.number}** {i.title}\n"
                    f"  وضعیت: {i.state} | لیبل‌ها: {labels} | "
                    f"نویسنده: @{i.user.login}"
                )
            return "\n".join(lines)

        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[list[str]] = None,
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            issue = r.create_issue(title=title, body=body, labels=labels or [])
            return (
                f"✅ Issue ساخته شد:\n"
                f"- شماره: **#{issue.number}**\n"
                f"- عنوان: {issue.title}\n"
                f"- لینک: {issue.html_url}"
            )
        except GithubException as e:
            return f"خطا در ساخت issue: {e.data.get('message', str(e))}"

    def add_issue_comment(
        self, owner: str, repo: str, issue_number: int, body: str
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            issue = r.get_issue(issue_number)
            comment = issue.create_comment(body)
            return f"✅ کامنت گذاشته شد روی #{issue_number}\nلینک: {comment.html_url}"
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str,
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            pr = r.create_pull(title=title, body=body, head=head, base=base)
            return (
                f"✅ Pull Request ساخته شد:\n"
                f"- شماره: **#{pr.number}**\n"
                f"- عنوان: {pr.title}\n"
                f"- از `{head}` به `{base}`\n"
                f"- لینک: {pr.html_url}"
            )
        except GithubException as e:
            return f"خطا در ساخت PR: {e.data.get('message', str(e))}"

    def search_code(self, query: str) -> str:
        try:
            results = self.g.search_code(query)
            items = list(results)[:10]

            if not items:
                return "هیچ نتیجه‌ای پیدا نشد."

            lines = [f"### نتایج جستجو برای `{query}`:\n"]
            for item in items:
                lines.append(
                    f"- **{item.repository.full_name}** → `{item.path}`\n"
                    f"  [مشاهده]({item.html_url})"
                )
            return "\n".join(lines)

        except GithubException as e:
            return f"خطا در جستجو: {e.data.get('message', str(e))}"

    def get_repo_tree(
        self, owner: str, repo: str, path: str = ""
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")

            if path:
                contents = r.get_contents(path)
            else:
                contents = r.get_contents("")

            if not isinstance(contents, list):
                contents = [contents]

            lines = [f"### ساختار `{owner}/{repo}/{path or ''}`:\n"]
            for item in contents:
                icon = "📁" if item.type == "dir" else "📄"
                size = f" ({item.size} bytes)" if item.type == "file" else ""
                lines.append(f"{icon} `{item.path}`{size}")

            return "\n".join(lines)

        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"
