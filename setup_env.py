#!/usr/bin/env python3
"""
ساخت فایل .env یک‌بار برای همیشه.
اجرا:
    python setup_env.py
"""

from pathlib import Path
from env_loader import PACKAGE_ENV, HOME_ENV, load_project_env, env_status


def main():
    print("=== تنظیم کلیدهای GitHub Omni Agent ===\n")
    print(f"1) کنار پروژه: {PACKAGE_ENV}")
    print(f"2) مسیر ثابت خانه (پیشنهادی): {HOME_ENV}")
    choice = input("کدام؟ [1/2] پیش‌فرض 2: ").strip() or "2"
    target = PACKAGE_ENV if choice == "1" else HOME_ENV

    gemini = input("GEMINI_API_KEY: ").strip()
    github = input("GITHUB_TOKEN: ").strip()

    if not gemini or not github:
        print("هر دو کلید لازم است.")
        return

    # بدون کوتیشن و فاصله
    content = f"GEMINI_API_KEY={gemini}\nGITHUB_TOKEN={github}\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    print(f"\n✅ نوشته شد: {target}")

    load_project_env(force=True)
    print("status:", env_status())
    print("\nحالا اجرا کن: python run_web.py")


if __name__ == "__main__":
    main()
