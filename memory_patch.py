"""اعمال حافظه مکالمه روی OmniAgent بدون بازنویسی کل agent.py"""

from __future__ import annotations

from memory import ConversationMemory


def apply_memory(agent_cls):
    if getattr(agent_cls, "_memory_patched", False):
        return agent_cls

    _orig_init = agent_cls.__init__
    _orig_run = agent_cls.run
    _orig_pick = agent_cls._pick_model

    def __init__(self, *a, **k):
        _orig_init(self, *a, **k)
        if not hasattr(self, "memory"):
            self.memory = ConversationMemory()
        try:
            # چت را با تاریخچه بازسازی کن
            history = self.memory.as_gemini_history(last_n=10)
            if self.model is not None:
                self.chat = self.model.start_chat(
                    history=history,
                    enable_automatic_function_calling=False,
                )
        except Exception as e:
            print("[memory] init history:", e)

    def _pick_model(self, reset_chat: bool = False):
        name = _orig_pick(self, reset_chat=True)
        try:
            if not hasattr(self, "memory"):
                self.memory = ConversationMemory()
            history = self.memory.as_gemini_history(last_n=10)
            self.chat = self.model.start_chat(
                history=history,
                enable_automatic_function_calling=False,
            )
            print(f"[memory] restored {len(history)} turns on model {name}")
        except Exception as e:
            print("[memory] pick history:", e)
        return name

    def run(self, user_message: str) -> str:
        if not hasattr(self, "memory"):
            self.memory = ConversationMemory()

        raw = (user_message or "").strip()
        low = raw.lower()

        if low in ("پاک کردن حافظه", "حافظه را پاک کن", "clear memory", "/clear"):
            self.memory.clear()
            try:
                self._pick_model(reset_chat=True)
            except Exception:
                pass
            return "حافظه مکالمه پاک شد."

        ctx = self.memory.context_block(last_n=8)
        if ctx:
            payload = "### حافظه\n" + ctx + "\n\n### پیام جدید کاربر\n" + raw
        else:
            payload = raw

        self.memory.add("user", raw)
        reply = _orig_run(self, payload)
        if reply:
            self.memory.add("assistant", reply)
        return reply

    agent_cls.__init__ = __init__
    agent_cls._pick_model = _pick_model
    agent_cls.run = run
    agent_cls._memory_patched = True
    return agent_cls
