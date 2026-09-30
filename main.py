#!/usr/bin/env python3
"""
GitHub Omni Agent - CLI Entry Point
ایجنت همه‌کاره و رایگان گیت‌هاب با Gemini
"""

import os
import sys
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from agent import OmniAgent

load_dotenv()
console = Console()


def check_env() -> None:
    missing = []
    if not os.getenv("GEMINI_API_KEY"):
        missing.append("GEMINI_API_KEY")
    if not os.getenv("GITHUB_TOKEN"):
        missing.append("GITHUB_TOKEN")

    if missing:
        console.print(
            Panel(
                "[red]متغیرهای محیطی زیر تنظیم نشده‌اند:[/red]\n"
                + "\n".join(f"  • {m}" for m in missing)
                + "\n\nفایل [bold].env[/bold] را از روی [bold].env.example[/bold] بساز و مقادیر را پر کن.\n"
                "راهنما در README.md نوشته شده است.",
                title="خطای پیکربندی",
                border_style="red",
            )
        )
        sys.exit(1)


def main() -> None:
    check_env()

    console.print(
        Panel(
            "[bold cyan]GitHub Omni Agent[/bold cyan]\n"
            "ایجنت همه‌کاره و کاملاً رایگان گیت‌هاب\n\n"
            "دستورات را به [bold]فارسی[/bold] یا [bold]انگلیسی[/bold] بنویس.\n"
            "برای خروج بنویس: [bold]exit[/bold] یا [bold]خروج[/bold]",
            border_style="cyan",
            title="خوش آمدید",
        )
    )

    agent = OmniAgent(
        gemini_api_key=os.getenv("GEMINI_API_KEY"),
        github_token=os.getenv("GITHUB_TOKEN"),
    )

    while True:
        try:
            user_input = console.input("\n[bold green]تو › [/bold green]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]خداحافظ![/yellow]")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "خروج", "q", "bye"):
            console.print("[yellow]خداحافظ! موفق باشی.[/yellow]")
            break

        with console.status("[bold cyan]در حال فکر کردن و اجرا...[/bold cyan]", spinner="dots"):
            try:
                response = agent.run(user_input)
            except Exception as e:
                console.print(f"[red]خطای غیرمنتظره:[/red] {e}")
                continue

        console.print(Panel(Markdown(str(response)), title="ایجنت", border_style="blue"))


if __name__ == "__main__":
    main()
