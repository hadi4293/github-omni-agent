"""
ابزارهای اضافی: Actions / Releases / Codespaces
"""

from __future__ import annotations

from typing import Optional

from github import GithubException


def attach_extra_methods(cls):
    """متدها را روی کلاس GitHubTools می‌چسباند."""

    # ─── Actions ───
    def list_workflow_runs(self, owner: str, repo: str, limit: int = 10) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            runs = list(r.get_workflow_runs())[:limit]
            if not runs:
                return f"هیچ workflow run در `{owner}/{repo}` پیدا نشد."
            lines = [f"### آخرین workflow runهای `{owner}/{repo}`:\n"]
            for run in runs:
                lines.append(
                    f"- **#{run.id}** {run.name or run.display_title or 'workflow'}\n"
                    f"  وضعیت: {run.status}/{run.conclusion or '—'} | برنچ: {run.head_branch}\n"
                    f"  لینک: {run.html_url}"
                )
            return "\n".join(lines)
        except GithubException as e:
            return f"خطا در لیست Actions: {e.data.get('message', str(e))}"

    def list_workflows(self, owner: str, repo: str) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            wfs = list(r.get_workflows())
            if not wfs:
                return f"هیچ workflow در `{owner}/{repo}` پیدا نشد."
            lines = [f"### Workflowهای `{owner}/{repo}`:\n"]
            for w in wfs:
                lines.append(
                    f"- **{w.name}** (id={w.id}) | state={w.state}\n"
                    f"  path: `{w.path}` | {w.html_url}"
                )
            return "\n".join(lines)
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def trigger_workflow(
        self,
        owner: str,
        repo: str,
        workflow_id: str,
        ref: str = "main",
    ) -> str:
        """workflow_id می‌تواند نام فایل مثل ci.yml یا id عددی باشد."""
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            try:
                wf = r.get_workflow(workflow_id)
            except Exception:
                # اگر id عددی بود
                wf = r.get_workflow(int(workflow_id))
            ok = wf.create_dispatch(ref=ref)
            if ok is False:
                return (
                    f"درخواست dispatch فرستاده شد ولی API مقدار False داد. "
                    f"مطمئن شو workflow `workflow_dispatch` دارد."
                )
            return (
                f"✅ Workflow `{wf.name}` روی برنچ `{ref}` تریگر شد.\n"
                f"چند لحظه بعد با list_workflow_runs وضعیت را چک کن."
            )
        except GithubException as e:
            return f"خطا در تریگر workflow: {e.data.get('message', str(e))}"

    def get_workflow_run(self, owner: str, repo: str, run_id: int) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            run = r.get_workflow_run(run_id)
            return (
                f"### Workflow Run #{run.id}\n"
                f"- نام: {run.name}\n"
                f"- وضعیت: {run.status} / {run.conclusion or '—'}\n"
                f"- برنچ: {run.head_branch}\n"
                f"- رویداد: {run.event}\n"
                f"- لینک: {run.html_url}"
            )
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def cancel_workflow_run(self, owner: str, repo: str, run_id: int) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            run = r.get_workflow_run(run_id)
            run.cancel()
            return f"✅ درخواست لغو run #{run_id} ارسال شد."
        except GithubException as e:
            return f"خطا در لغو: {e.data.get('message', str(e))}"

    def rerun_workflow_run(self, owner: str, repo: str, run_id: int) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            run = r.get_workflow_run(run_id)
            run.rerun()
            return f"✅ Run #{run_id} دوباره اجرا شد."
        except GithubException as e:
            return f"خطا در rerun: {e.data.get('message', str(e))}"

    # ─── Releases ───
    def list_releases(self, owner: str, repo: str, limit: int = 10) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            releases = list(r.get_releases())[:limit]
            if not releases:
                return f"هیچ Release در `{owner}/{repo}` نیست."
            lines = [f"### Releaseهای `{owner}/{repo}`:\n"]
            for rel in releases:
                tag = rel.tag_name
                draft = " (draft)" if rel.draft else ""
                pre = " (prerelease)" if rel.prerelease else ""
                lines.append(
                    f"- **{rel.title or tag}** `{tag}`{draft}{pre}\n"
                    f"  {rel.html_url}"
                )
            return "\n".join(lines)
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def get_latest_release(self, owner: str, repo: str) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            rel = r.get_latest_release()
            body = (rel.body or "")[:1500]
            return (
                f"### آخرین Release `{owner}/{repo}`\n"
                f"- عنوان: {rel.title}\n"
                f"- تگ: `{rel.tag_name}`\n"
                f"- نویسنده: @{rel.author.login if rel.author else '?'}\n"
                f"- لینک: {rel.html_url}\n"
                f"- توضیحات:\n{body}"
            )
        except GithubException as e:
            return f"خطا: {e.data.get('message', str(e))}"

    def create_release(
        self,
        owner: str,
        repo: str,
        tag_name: str,
        name: str = "",
        body: str = "",
        draft: bool = False,
        prerelease: bool = False,
        target_commitish: str = "main",
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            rel = r.create_git_release(
                tag=tag_name,
                name=name or tag_name,
                message=body or "",
                draft=draft,
                prerelease=prerelease,
                target_commitish=target_commitish,
            )
            return (
                f"✅ Release ساخته شد:\n"
                f"- تگ: `{rel.tag_name}`\n"
                f"- عنوان: {rel.title}\n"
                f"- لینک: {rel.html_url}"
            )
        except GithubException as e:
            return f"خطا در ساخت Release: {e.data.get('message', str(e))}"

    def delete_release(self, owner: str, repo: str, release_id: int) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            rel = r.get_release(release_id)
            rel.delete_release()
            return f"✅ Release id={release_id} حذف شد."
        except GithubException as e:
            return f"خطا در حذف Release: {e.data.get('message', str(e))}"

    # ─── Codespaces ───
    def list_codespaces(self, limit: int = 15) -> str:
        try:
            # PyGithub: user.get_codespaces() در نسخه‌های جدید
            if not hasattr(self.user, "get_codespaces"):
                return (
                    "نسخه PyGithub شما Codespaces را پشتیبانی نمی‌کند. "
                    "`pip install -U PyGithub` را اجرا کن."
                )
            spaces = list(self.user.get_codespaces())[:limit]
            if not spaces:
                return "هیچ Codespace فعالی نداری."
            lines = ["### Codespaceهای تو:\n"]
            for cs in spaces:
                repo_name = getattr(getattr(cs, "repository", None), "full_name", "?")
                lines.append(
                    f"- **{cs.name}** | state={cs.state}\n"
                    f"  ریپو: {repo_name} | ماشین: {getattr(cs, 'machine_display_name', getattr(cs, 'machine', '—'))}\n"
                    f"  url: {getattr(cs, 'web_url', getattr(cs, 'url', '—'))}"
                )
            return "\n".join(lines)
        except GithubException as e:
            return f"خطا در لیست Codespaces: {e.data.get('message', str(e))}"
        except Exception as e:
            return f"خطا در Codespaces: {type(e).__name__}: {e}"

    def create_codespace(
        self,
        owner: str,
        repo: str,
        ref: str = "main",
        machine: str = "basicLinux32gb",
    ) -> str:
        try:
            r = self.g.get_repo(f"{owner}/{repo}")
            if not hasattr(r, "create_codespace"):
                # fallback از طریق API سطح پایین
                if not hasattr(self.user, "create_codespace"):
                    return (
                        "ساخت Codespace در این نسخه PyGithub در دسترس نیست. "
                        "`pip install -U PyGithub` را امتحان کن."
                    )
            # PyGithub 2.x
            try:
                cs = r.create_codespace(ref=ref, machine=machine)
            except TypeError:
                cs = r.create_codespace()
            return (
                f"✅ Codespace ساخته شد:\n"
                f"- نام: {getattr(cs, 'name', '—')}\n"
                f"- state: {getattr(cs, 'state', '—')}\n"
                f"- لینک: {getattr(cs, 'web_url', getattr(cs, 'url', '—'))}"
            )
        except GithubException as e:
            return f"خطا در ساخت Codespace: {e.data.get('message', str(e))}"
        except Exception as e:
            return f"خطا: {type(e).__name__}: {e}"

    def delete_codespace(self, codespace_name: str) -> str:
        try:
            if not hasattr(self.user, "get_codespace"):
                return "حذف Codespace در این نسخه PyGithub پشتیبانی نمی‌شود."
            cs = self.user.get_codespace(codespace_name)
            cs.delete()
            return f"✅ Codespace `{codespace_name}` حذف شد."
        except GithubException as e:
            return f"خطا در حذف Codespace: {e.data.get('message', str(e))}"
        except Exception as e:
            return f"خطا: {type(e).__name__}: {e}"

    cls.list_workflow_runs = list_workflow_runs
    cls.list_workflows = list_workflows
    cls.trigger_workflow = trigger_workflow
    cls.get_workflow_run = get_workflow_run
    cls.cancel_workflow_run = cancel_workflow_run
    cls.rerun_workflow_run = rerun_workflow_run
    cls.list_releases = list_releases
    cls.get_latest_release = get_latest_release
    cls.create_release = create_release
    cls.delete_release = delete_release
    cls.list_codespaces = list_codespaces
    cls.create_codespace = create_codespace
    cls.delete_codespace = delete_codespace
    return cls
