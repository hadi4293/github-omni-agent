#!/usr/bin/env python3
"""GitHub Omni Agent - Web UI (simple & reliable)"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from agent import OmniAgent

load_dotenv()

app = FastAPI(title="GitHub Omni Agent")

_agent: Optional[OmniAgent] = None
_pending_confirm: Optional[dict] = None


def get_agent() -> OmniAgent:
    global _agent
    if _agent is None:
        gemini_key = os.getenv("GEMINI_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        if not gemini_key or not github_token:
            raise RuntimeError("GEMINI_API_KEY or GITHUB_TOKEN missing in .env")

        def web_confirm(description: str) -> bool:
            global _pending_confirm
            _pending_confirm = {"description": description, "approved": False}
            return False

        _agent = OmniAgent(
            gemini_api_key=gemini_key,
            github_token=github_token,
            confirm_callback=web_confirm,
        )
    return _agent


class ChatRequest(BaseModel):
    message: str


class ConfirmRequest(BaseModel):
    approved: bool


@app.get("/", response_class=HTMLResponse)
async def home():
    return PAGE


@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    global _pending_confirm
    try:
        agent = get_agent()
        _pending_confirm = None
        text = (req.message or "").strip()
        if not text:
            return JSONResponse({"ok": True, "reply": "پیام خالی بود.", "needs_confirm": False})

        reply = agent.run(text)
        reply = reply if reply is not None else ""

        if _pending_confirm and not _pending_confirm.get("approved"):
            return JSONResponse({
                "ok": True,
                "reply": reply,
                "needs_confirm": True,
                "confirm_description": _pending_confirm.get("description", ""),
            })

        return JSONResponse({"ok": True, "reply": reply, "needs_confirm": False})
    except Exception as e:
        return JSONResponse({"ok": False, "reply": f"خطا: {e}", "needs_confirm": False}, status_code=500)


@app.post("/api/confirm")
async def api_confirm(req: ConfirmRequest):
    global _pending_confirm
    if not _pending_confirm:
        return JSONResponse({"ok": True, "reply": "عملیات معلقی نیست.", "needs_confirm": False})

    if not req.approved:
        _pending_confirm = None
        return JSONResponse({"ok": True, "reply": "عملیات لغو شد.", "needs_confirm": False})

    try:
        agent = get_agent()
        original = agent.confirm_callback
        agent.confirm_callback = lambda d: True
        reply = agent.run("بله تأیید می‌کنم، انجام بده.")
        agent.confirm_callback = original
        _pending_confirm = None
        return JSONResponse({"ok": True, "reply": reply or "", "needs_confirm": False})
    except Exception as e:
        return JSONResponse({"ok": False, "reply": f"خطا: {e}", "needs_confirm": False})


@app.get("/api/health")
async def api_health():
    has_keys = bool(os.getenv("GEMINI_API_KEY") and os.getenv("GITHUB_TOKEN"))
    return {"ok": has_keys, "model": "gemini-3.5-flash-lite"}


PAGE = r'''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GitHub Omni Agent</title>
<style>
  html, body { height: 100%; margin: 0; }
  body {
    font-family: Tahoma, "Segoe UI", Arial, sans-serif;
    background: #0f1117;
    color: #e8eaed;
    display: flex;
    flex-direction: column;
  }

  #top {
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  #top h1 { margin: 0; font-size: 16px; font-weight: 600; }
  #top small { color: #8b949e; font-size: 12px; }
  #badge {
    font-size: 11px;
    padding: 3px 10px;
    border-radius: 20px;
    background: #23863633;
    color: #3fb950;
    border: 1px solid #23863666;
  }

  #messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .bubble {
    max-width: 80%;
    padding: 10px 14px;
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
  }
  .me {
    align-self: flex-start;
    background: #1f6feb;
    color: #fff;
  }
  .bot {
    align-self: flex-end;
    background: #21262d;
    border: 1px solid #30363d;
    color: #e8eaed;
  }
  .err {
    align-self: flex-end;
    background: #3d1214;
    border: 1px solid #f8514966;
    color: #ffa198;
  }

  #confirm {
    display: none;
    margin: 0 16px 8px;
    padding: 10px 14px;
    background: #3d2e00;
    border: 1px solid #d2992266;
    border-radius: 10px;
    font-size: 13px;
    color: #e3b341;
  }
  #confirm.show { display: block; }
  #confirm button {
    margin-top: 8px;
    margin-left: 6px;
    padding: 5px 14px;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
  }
  #btn-yes { background: #d29922; color: #000; }
  #btn-no  { background: #30363d; color: #e8eaed; }

  #bottom {
    border-top: 1px solid #30363d;
    background: #161b22;
    padding: 12px 16px;
    display: flex;
    gap: 8px;
  }
  #inp {
    flex: 1;
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 10px 12px;
    color: #e8eaed;
    font-size: 14px;
    font-family: inherit;
    outline: none;
    resize: none;
    min-height: 42px;
    max-height: 120px;
  }
  #inp:focus { border-color: #1f6feb; }
  #btn {
    width: 42px;
    height: 42px;
    border: none;
    border-radius: 10px;
    background: #1f6feb;
    color: #fff;
    font-size: 18px;
    cursor: pointer;
    flex-shrink: 0;
  }
  #btn:disabled { opacity: 0.4; cursor: wait; }
  #btn:hover:not(:disabled) { background: #388bfd; }
</style>
</head>
<body>

<div id="top">
  <div>
    <h1>GitHub Omni Agent</h1>
    <small>gemini-3.5-flash-lite</small>
  </div>
  <span id="badge">آماده</span>
</div>

<div id="messages">
  <div class="bubble bot">سلام! من ایجنت گیت‌هاب هستم.
دستورات را فارسی یا انگلیسی بنویس.

مثال:
• لیست ریپوهای من رو نشون بده
• اطلاعات حساب من رو بگو</div>
</div>

<div id="confirm">
  <div id="confirm-msg"></div>
  <button id="btn-yes" type="button">تأیید</button>
  <button id="btn-no" type="button">لغو</button>
</div>

<div id="bottom">
  <textarea id="inp" rows="1" placeholder="پیام خود را بنویس..."></textarea>
  <button id="btn" type="button">➤</button>
</div>

<script>
const messages = document.getElementById("messages");
const inp = document.getElementById("inp");
const btn = document.getElementById("btn");
const badge = document.getElementById("badge");
const confirmBox = document.getElementById("confirm");
const confirmMsg = document.getElementById("confirm-msg");
const btnYes = document.getElementById("btn-yes");
const btnNo = document.getElementById("btn-no");

function addBubble(text, cls) {
  const el = document.createElement("div");
  el.className = "bubble " + cls;
  el.textContent = text;   // امن و بدون HTML injection
  messages.appendChild(el);
  messages.scrollTop = messages.scrollHeight;
  return el;
}

function setBusy(on) {
  btn.disabled = on;
  badge.textContent = on ? "در حال کار..." : "آماده";
  badge.style.color = on ? "#58a6ff" : "#3fb950";
  badge.style.background = on ? "#1f6feb33" : "#23863633";
  badge.style.borderColor = on ? "#1f6feb66" : "#23863666";
}

async function send() {
  const text = inp.value.trim();
  if (!text) return;

  inp.value = "";
  addBubble(text, "me");
  setBusy(true);

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text })
    });

    let data;
    try {
      data = await res.json();
    } catch (_) {
      addBubble("پاسخ سرور قابل خواندن نبود (status " + res.status + ")", "err");
      setBusy(false);
      return;
    }

    const reply = (data && data.reply != null) ? String(data.reply) : "(پاسخ خالی)";
    addBubble(reply, data && data.ok === false ? "err" : "bot");

    if (data && data.needs_confirm) {
      confirmMsg.textContent = "⚠ " + (data.confirm_description || "عملیات خطرناک");
      confirmBox.classList.add("show");
    } else {
      confirmBox.classList.remove("show");
    }
  } catch (e) {
    addBubble("خطای شبکه: " + e.message, "err");
  }

  setBusy(false);
  inp.focus();
}

async function doConfirm(approved) {
  confirmBox.classList.remove("show");
  setBusy(true);
  try {
    const res = await fetch("/api/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved: approved })
    });
    const data = await res.json();
    addBubble(String(data.reply || ""), "bot");
  } catch (e) {
    addBubble("خطا: " + e.message, "err");
  }
  setBusy(false);
}

btn.addEventListener("click", send);
btnYes.addEventListener("click", function () { doConfirm(true); });
btnNo.addEventListener("click", function () { doConfirm(false); });

inp.addEventListener("keydown", function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

// health
fetch("/api/health").then(function (r) { return r.json(); }).then(function (d) {
  if (!d.ok) {
    badge.textContent = "کلیدها ناقص";
    badge.style.color = "#f85149";
    badge.style.background = "#f8514933";
  }
}).catch(function () {});

inp.focus();
</script>
</body>
</html>
'''


if __name__ == "__main__":
    import uvicorn
    print("\n  GitHub Omni Agent")
    print("  http://127.0.0.1:8000\n")
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
