"""
حافظه مکالمه ایجنت
- در RAM نگه می‌دارد
- روی دیسک هم ذخیره می‌کند تا با ری‌استارت از بین نرود
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class ConversationMemory:
    def __init__(self, path: Optional[Path] = None, max_turns: int = 30):
        self.path = path or (Path(__file__).resolve().parent / "data" / "memory.json")
        self.max_turns = max_turns
        self.turns: List[Dict[str, str]] = []  # {role: user|assistant, content: str}
        self.facts: List[str] = []  # نکات پایدار که کاربر گفته
        self._load()

    def _load(self) -> None:
        try:
            if self.path.exists():
                data = json.loads(self.path.read_text(encoding="utf-8"))
                self.turns = list(data.get("turns") or [])[-self.max_turns :]
                self.facts = list(data.get("facts") or [])[:50]
        except Exception as e:
            print(f"[memory] load failed: {e}")
            self.turns = []
            self.facts = []

    def save(self) -> None:
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"turns": self.turns[-self.max_turns :], "facts": self.facts[:50]}
            self.path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            print(f"[memory] save failed: {e}")

    def add(self, role: str, content: str) -> None:
        content = (content or "").strip()
        if not content:
            return
        self.turns.append({"role": role, "content": content})
        if len(self.turns) > self.max_turns:
            self.turns = self.turns[-self.max_turns :]
        self.save()

    def add_fact(self, fact: str) -> None:
        fact = (fact or "").strip()
        if fact and fact not in self.facts:
            self.facts.append(fact)
            self.facts = self.facts[:50]
            self.save()

    def clear(self) -> None:
        self.turns = []
        self.facts = []
        self.save()

    def context_block(self, last_n: int = 12) -> str:
        """متن خلاصه برای تزریق به پرامپت / مدل جدید"""
        parts: List[str] = []
        if self.facts:
            parts.append("نکات به‌یادمانده درباره کاربر/پروژه:")
            for f in self.facts[-10:]:
                parts.append(f"- {f}")
            parts.append("")

        recent = self.turns[-last_n:]
        if recent:
            parts.append("خلاصه مکالمات اخیر:")
            for t in recent:
                who = "کاربر" if t.get("role") == "user" else "ایجنت"
                text = (t.get("content") or "").replace("\n", " ")
                if len(text) > 400:
                    text = text[:400] + "…"
                parts.append(f"{who}: {text}")

        return "\n".join(parts).strip()

    def as_gemini_history(self, last_n: int = 10) -> List[Any]:
        """تاریخچه به فرمت start_chat(history=...)"""
        history = []
        for t in self.turns[-last_n:]:
            role = "user" if t.get("role") == "user" else "model"
            history.append({"role": role, "parts": [t.get("content") or ""]})
        return history
