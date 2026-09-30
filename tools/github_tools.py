"""
تمام ابزارهای گیت‌هاب برای GitHub Omni Agent
نسخه نهایی و کامل
"""

from __future__ import annotations

import base64
from typing import Optional

from github import Github, GithubException


class GitHubTools:
    def __init__(self, token: str):
        self.g = Github(token)
        self.user = self.g.get_user()

    # ───────────────────────────── Repo ─────────────────────────────

    def list_my_repos(self, limit: int = 30) -> str:
        repos = list(self.user.get_repos(sort="updated"))[:limit]
        if not repos:
            return "هیچ ریپویی پیدا نشد."

        lines = ["### ریپوهای تو:\n"]
        for r in repos:
            vis = "🔒 خصوصی" if r.private else "🌐 عمومی"
            lang = r.language or "—"
            lines.append(
                f"- **{r.full_name}** ({vis}) | زبان: {lang} | "
                f"⭐ {r.stargazers_count} | آپدیت: {r.updated_at.strftime('%Y-%m-%d')}"
            )
        return "\n".join(lines)

    def create_repo(
        self,
        name: str,
        description: str = "",
        private: bool = True,
        auto_init: bool = True,
    ) -> str:
        try:
            repo = self.user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=auto_init,
            )
            return (
                f"✅ ریپو ساخته شد:\n"
                f"- نام: **{repo.full_name}**\n"
                f"- لینک: {repo.html_url}\n"
                f"- وضعیت: {'خصوصی' if private else 'عمومی'}"
            )
        except GithubException as e:
            return f"خطا در ساخت ریپو: {e.data.get('message', str(e))}"

    def delete_repo(self, owner: str, repo: str) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            r.delete()
            return f"✅ ریپوی `{owner}/{repo}` با موفقیت حذف شد."
        except GithubException as e:
            return f"خطا در حذف ریپو: {e.data.get('message', str(e))}"

    def get_repo_tree(self, owner: str, repo: str, path: str = "") -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            contents = r.get_contents(path or "")
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

    def star_repo(self, owner: str, repo: str) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            self.user.add_to_starred(r)
            return f"✅ به `{owner}/{repo}` ستاره داده شد."
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def unstar_repo(self, owner: str, repo: str) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            self.user.remove_from_starred(r)
            return f"✅ ستاره از `{owner}/{repo}` برداشته شد."
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    # ───────────────────────────── File ─────────────────────────────

    def get_file_content(
        self, owner: str, repo: str, path: str, ref: Optional[str] = None
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            kwargs = {"ref": ref} if ref else {}
            content = r.get_contents(path, **kwargs)

            if isinstance(content, list):
                return f"`{path}` یک پوشه است. از get_repo_tree استفاده کن."

            if content.encoding == "base64":
                text = base64.b64decode(content.content).decode("utf-8", errors="replace")
            else:
                text = content.content or ""

            if len(text) > 18000:
                text = text[:18000] + "\n\n... [محتوا خیلی طولانی بود و کوتاه شد]"

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
                result = r.update_file(
                    path=path,
                    message=message,
                    content=content,
                    sha=existing.sha,
                    branch=branch,
                )
                action = "آپدیت شد"
            except GithubException:
                result = r.create_file(
                    path=path,
                    message=message,
                    content=content,
                    branch=branch,
                )
                action = "ساخته شد"

            sha = result["commit"].sha[:7]
            return f"✅ فایل `{path}` با موفقیت {action}.\nکامیت: `{sha}`\nپیام: {message}"
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

    # ───────────────────────────── Issue ─────────────────────────────

    def list_issues(self, owner: str, repo: str, state: str = "open") -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            issues = list(r.get_issues(state=state))[:25]
            if not issues:
                return f"هیچ issue با وضعیت `{state}` پیدا نشد."

            lines = [f"### Issueهای `{owner}/{repo}` (state={state}):\n"]
            for i in issues:
                if i.pull_request:
                    continue  # فقط issue واقعی
                labels = ", ".join(l.name for l in i.labels) or "—"
                lines.append(
                    f"- **#{i.number}** {i.title}\n"
                    f"  وضعیت: {i.state} | لیبل‌ها: {labels} | نویسنده: @{i.user.login}"
                )
            return "\n".join(lines) if len(lines) > 1 else "هیچ issue واقعی پیدا نشد."
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str = "",
        labels: Optional[list] = None,
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            issue = r.create_issue(title=title, body=body or "", labels=labels or [])
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

    def close_issue(self, owner: str, repo: str, issue_number: int) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            issue = r.get_issue(issue_number)
            issue.edit(state="closed")
            return f"✅ Issue #{issue_number} بسته شد."
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def reopen_issue(self, owner: str, repo: str, issue_number: int) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            issue = r.get_issue(issue_number)
            issue.edit(state="open")
            return f"✅ Issue #{issue_number} دوباره باز شد."
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def update_issue(
        self,
        owner: str,
        repo: str,
        issue_number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            issue = r.get_issue(issue_number)
            kwargs = {}
            if title is not None:
                kwargs["title"] = title
            if body is not None:
                kwargs["body"] = body
            if not kwargs:
                return "هیچ تغییری مشخص نشده."
            issue.edit(**kwargs)
            return f"✅ Issue #{issue_number} آپدیت شد."
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    # ───────────────────────────── Pull Request ─────────────────────────────

    def list_pull_requests(self, owner: str, repo: str, state: str = "open") -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            prs = list(r.get_pulls(state=state))[:20]
            if not prs:
                return f"هیچ Pull Request با وضعیت `{state}` پیدا نشد."

            lines = [f"### PRهای `{owner}/{repo}` (state={state}):\n"]
            for pr in prs:
                lines.append(
                    f"- **#{pr.number}** {pr.title}\n"
                    f"  از `{pr.head.ref}` → `{pr.base.ref}` | نویسنده: @{pr.user.login}"
                )
            return "\n".join(lines)
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
            pr = r.create_pull(title=title, body=body or "", head=head, base=base)
            return (
                f"✅ Pull Request ساخته شد:\n"
                f"- شماره: **#{pr.number}**\n"
                f"- عنوان: {pr.title}\n"
                f"- از `{head}` به `{base}`\n"
                f"- لینک: {pr.html_url}"
            )
        except GithubException as e:
            return f"خطا در ساخت PR: {e.data.get('message', str(e))}"

    def merge_pull_request(
        self, owner: str, repo: str, pr_number: int, commit_message: str = ""
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            pr = r.get_pull(pr_number)
            if pr.is_merged():
                return f"PR #{pr_number} قبلاً merge شده است."
            result = pr.merge(commit_message=commit_message or f"Merge PR #{pr_number}")
            if result.merged:
                return f"✅ PR #{pr_number} با موفقیت merge شد."
            return f"نتوانست merge شود: {result.message}"
        except GithubException as e:
            return f"خطا در merge: {e.data.get('message', str(e))}"

    def close_pull_request(self, owner: str, repo: str, pr_number: int) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            pr = r.get_pull(pr_number)
            pr.edit(state="closed")
            return f"✅ PR #{pr_number} بسته شد."
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    # ───────────────────────────── Branch & Commit ─────────────────────────────

    def list_branches(self, owner: str, repo: str) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            branches = list(r.get_branches())[:30]
            if not branches:
                return "هیچ برنچی پیدا نشد."
            lines = [f"### برنچ‌های `{owner}/{repo}`:\n"]
            for b in branches:
                lines.append(f"- `{b.name}` (آخرین کامیت: {b.commit.sha[:7]})")
            return "\n".join(lines)
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def create_branch(
        self, owner: str, repo: str, branch_name: str, from_branch: str = "main"
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            source = r.get_branch(from_branch)
            r.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source.commit.sha)
            return f"✅ برنچ `{branch_name}` از روی `{from_branch}` ساخته شد."
        except GithubException as e:
            return f"خطا در ساخت برنچ: {e.data.get('message', str(e))}"

    def list_commits(self, owner: str, repo: str, limit: int = 10) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            commits = list(r.get_commits())[:limit]
            if not commits:
                return "هیچ کامیتی پیدا نشد."
            lines = [f"### آخرین کامیت‌های `{owner}/{repo}`:\n"]
            for c in commits:
                msg = (c.commit.message or "").split("\n")[0][:80]
                author = c.commit.author.name if c.commit.author else "?"
                lines.append(f"- `{c.sha[:7]}` {msg} — {author}")
            return "\n".join(lines)
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    # ───────────────────────────── Search & User ─────────────────────────────

    def search_code(self, query: str) -> str:
        try:
            results = self.g.search_code(query)
            items = list(results)[:12]
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

    def get_me(self) -> str:
        try:
            u = self.user
            return (
                f"### اطلاعات حساب شما:\n"
                f"- نام کاربری: **{u.login}**\n"
                f"- نام: {u.name or '—'}\n"
                f"- بیو: {u.bio or '—'}\n"
                f"- ریپوهای عمومی: {u.public_repos}\n"
                f"- دنبال‌کنندگان: {u.followers}\n"
                f"- لینک: {u.html_url}"
            )
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def create_gist(
        self, filename: str, content: str, description: str = "", public: bool = False
    ) -> str:
        try:
            gist = self.g.get_user().create_gist(
                public=public,
                files={filename: {"content": content}},
                description=description or "",
            )
            return f"✅ Gist ساخته شد:\n- لینک: {gist.html_url}"
        except GithubException as e:
            return f"خطا در ساخت Gist: {e.data.get('message', str(e))}"
