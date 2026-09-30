#!/usr/bin/env python3
"""
GitHub Omni Agent - Web UI
رابط وب مدرن و زیبا
"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from agent import OmniAgent

load_dotenv()

app = FastAPI(title="GitHub Omni Agent", version="1.0")

_agent: Optional[OmniAgent] = None
_pending_confirm: Optional[dict] = None


def get_agent() -> OmniAgent:
    global _agent
    if _agent is None:
        gemini_key = os.getenv("GEMINI_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        if not gemini_key or not github_token:
            raise RuntimeError("GEMINI_API_KEY یا GITHUB_TOKEN تنظیم نشده")

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
async def index():
    return HTML_PAGE


@app.post("/api/chat")
async def chat(req: ChatRequest):
    global _pending_confirm
    try:
        agent = get_agent()
        _pending_confirm = None
        reply = agent.run(req.message.strip())

        if _pending_confirm and not _pending_confirm.get("approved"):
            return JSONResponse({
                "reply": reply or "",
                "needs_confirm": True,
                "confirm_description": _pending_confirm["description"],
            })

        return JSONResponse({"reply": reply or "", "needs_confirm": False})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/confirm")
async def confirm(req: ConfirmRequest):
    global _pending_confirm
    if not _pending_confirm:
        return JSONResponse({"reply": "هیچ عملیات معلقی وجود ندارد.", "needs_confirm": False})

    if req.approved:
        try:
            agent = get_agent()
            original_cb = agent.confirm_callback
            agent.confirm_callback = lambda d: True
            reply = agent.run("بله، تأیید می‌کنم. عملیات را انجام بده.")
            agent.confirm_callback = original_cb
            _pending_confirm = None
            return JSONResponse({"reply": reply or "", "needs_confirm": False})
        except Exception as e:
            return JSONResponse({"reply": f"خطا: {e}", "needs_confirm": False})
    else:
        _pending_confirm = None
        return JSONResponse({"reply": "عملیات لغو شد.", "needs_confirm": False})


@app.get("/api/health")
async def health():
    ok = bool(os.getenv("GEMINI_API_KEY") and os.getenv("GITHUB_TOKEN"))
    return {"status": "ok" if ok else "missing_env", "model": "gemini-3.5-flash-lite"}


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>GitHub Omni Agent</title>
  <link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Vazirmatn', system-ui, sans-serif;
      background: #0a0a0f;
      color: #e5e7eb;
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    /* Header */
    header {
      border-bottom: 1px solid #1f2937;
      background: rgba(17, 17, 27, 0.9);
      backdrop-filter: blur(12px);
      flex-shrink: 0;
      z-index: 20;
    }
    .header-inner {
      max-width: 48rem;
      margin: 0 auto;
      padding: 0.75rem 1rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .logo {
      width: 2.25rem; height: 2.25rem;
      border-radius: 0.75rem;
      background: linear-gradient(135deg, #38bdf8, #0284c7);
      display: flex; align-items: center; justify-content: center;
      color: white; font-weight: 700; font-size: 1.1rem;
      box-shadow: 0 4px 14px rgba(14, 165, 233, 0.25);
    }
    .status {
      font-size: 0.75rem;
      padding: 0.25rem 0.65rem;
      border-radius: 9999px;
      background: rgba(34, 197, 94, 0.1);
      color: #4ade80;
      border: 1px solid rgba(34, 197, 94, 0.2);
    }
    .status.busy {
      background: rgba(14, 165, 233, 0.1);
      color: #7dd3fc;
      border-color: rgba(14, 165, 233, 0.2);
    }
    .status.err {
      background: rgba(239, 68, 68, 0.1);
      color: #f87171;
      border-color: rgba(239, 68, 68, 0.2);
    }

    /* Main chat */
    main {
      flex: 1;
      min-height: 0;
      display: flex;
      flex-direction: column;
      max-width: 48rem;
      width: 100%;
      margin: 0 auto;
    }

    #chat-box {
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      padding: 1.5rem 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.85rem;
    }
    #chat-box::-webkit-scrollbar { width: 5px; }
    #chat-box::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }

    .msg {
      max-width: 85%;
      padding: 0.75rem 1rem;
      border-radius: 1rem;
      font-size: 0.9rem;
      line-height: 1.65;
      word-wrap: break-word;
      animation: fadeIn 0.25s ease;
    }
    .msg-user {
      align-self: flex-start;
      background: linear-gradient(135deg, #0ea5e9, #0284c7);
      color: #fff;
      border-bottom-right-radius: 0.25rem;
    }
    .msg-bot {
      align-self: flex-end;
      background: #1e1e2e;
      border: 1px solid #2a2a3c;
      color: #e5e7eb;
      border-bottom-left-radius: 0.25rem;
    }
    .msg-bot code {
      background: rgba(0,0,0,0.35);
      padding: 0.1rem 0.35rem;
      border-radius: 0.25rem;
      color: #7dd3fc;
      font-size: 0.85em;
    }
    .msg-bot strong { color: #fff; }

    .typing {
      align-self: flex-end;
      background: #1e1e2e;
      border: 1px solid #2a2a3c;
      padding: 0.75rem 1.2rem;
      border-radius: 1rem;
      width: fit-content;
    }
    .typing span {
      display: inline-block;
      width: 6px; height: 6px;
      margin: 0 2px;
      background: #7dd3fc;
      border-radius: 50%;
      animation: blink 1.4s infinite both;
    }
    .typing span:nth-child(2) { animation-delay: 0.2s; }
    .typing span:nth-child(3) { animation-delay: 0.4s; }

    @keyframes blink {
      0%, 80%, 100% { opacity: 0.2; }
      40% { opacity: 1; }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(6px); }
      to { opacity: 1; transform: none; }
    }

    /* Confirm */
    #confirm-banner {
      display: none;
      margin: 0 1rem 0.5rem;
      padding: 0.75rem 1rem;
      border-radius: 0.75rem;
      background: rgba(245, 158, 11, 0.1);
      border: 1px solid rgba(245, 158, 11, 0.3);
      font-size: 0.875rem;
    }
    #confirm-banner.show { display: block; }
    #confirm-text { color: #fcd34d; margin-bottom: 0.5rem; }
    .btn-confirm {
      padding: 0.35rem 1rem;
      border-radius: 0.5rem;
      font-size: 0.8rem;
      font-weight: 500;
      border: none;
      cursor: pointer;
      margin-left: 0.4rem;
    }
    .btn-yes { background: #f59e0b; color: #000; }
    .btn-yes:hover { background: #fbbf24; }
    .btn-no { background: #374151; color: #e5e7eb; }
    .btn-no:hover { background: #4b5563; }

    /* Input */
    .input-area {
      flex-shrink: 0;
      border-top: 1px solid #1f2937;
      background: rgba(17, 17, 27, 0.7);
      backdrop-filter: blur(12px);
      padding: 1rem;
    }
    .input-row {
      display: flex;
      gap: 0.5rem;
      align-items: flex-end;
    }
    #user-input {
      flex: 1;
      resize: none;
      background: #1e1e2e;
      border: 1px solid #374151;
      border-radius: 1rem;
      padding: 0.75rem 1rem;
      color: #e5e7eb;
      font-family: inherit;
      font-size: 0.9rem;
      max-height: 8rem;
      outline: none;
      transition: border-color 0.15s;
    }
    #user-input:focus {
      border-color: #0ea5e9;
      box-shadow: 0 0 0 2px rgba(14, 165, 233, 0.2);
    }
    #user-input::placeholder { color: #6b7280; }
    #send-btn {
      width: 2.75rem; height: 2.75rem;
      border-radius: 0.75rem;
      background: #0ea5e9;
      border: none;
      cursor: pointer;
      display: flex; align-items: center; justify-content: center;
      box-shadow: 0 4px 14px rgba(14, 165, 233, 0.3);
      transition: background 0.15s, transform 0.1s;
      flex-shrink: 0;
    }
    #send-btn:hover { background: #38bdf8; }
    #send-btn:active { transform: scale(0.95); }
    #send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    #send-btn svg { width: 1.25rem; height: 1.25rem; fill: white; }
  </style>
</head>
<body>

  <header>
    <div class="header-inner">
      <div style="display:flex;align-items:center;gap:0.75rem">
        <div class="logo">G</div>
        <div>
          <div style="font-weight:600;font-size:0.95rem">GitHub Omni Agent</div>
          <div style="font-size:0.7rem;color:#9ca3af">gemini-3.5-flash-lite · رایگان</div>
        </div>
      </div>
      <div id="status" class="status">آماده</div>
    </div>
  </header>

  <main>
    <div id="chat-box">
      <div class="msg msg-bot">
        سلام 👋 من <strong>GitHub Omni Agent</strong> هستم.<br><br>
        می‌تونی فارسی یا انگلیسی ازم بخوای کارهای گیت‌هاب رو انجام بدم.<br><br>
        مثلاً:<br>
        • لیست ریپوهای من رو نشون بده<br>
        • اطلاعات حساب من رو بگو<br>
        • یه issue جدید بساز
      </div>
    </div>

    <div id="confirm-banner">
      <p id="confirm-text"></p>
      <button class="btn-confirm btn-yes" onclick="sendConfirm(true)">تأیید و اجرا</button>
      <button class="btn-confirm btn-no" onclick="sendConfirm(false)">لغو</button>
    </div>

    <div class="input-area">
      <form id="chat-form" class="input-row" onsubmit="return false;">
        <textarea id="user-input" rows="1" placeholder="پیامت را بنویس..."></textarea>
        <button type="button" id="send-btn" onclick="submitChat()">
          <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </form>
    </div>
  </main>

<script>
(function () {
  const chatBox = document.getElementById('chat-box');
  const input = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  const statusEl = document.getElementById('status');
  const confirmBanner = document.getElementById('confirm-banner');
  const confirmText = document.getElementById('confirm-text');

  function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
  }

  function formatText(t) {
    if (!t) return '';
    let s = escapeHtml(String(t));
    s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/`([^`]+)`/g, '<code>$1</code>');
    s = s.replace(/\n/g, '<br>');
    return s;
  }

  function addMsg(text, isUser) {
    const div = document.createElement('div');
    div.className = 'msg ' + (isUser ? 'msg-user' : 'msg-bot');
    div.innerHTML = formatText(text);
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function showTyping() {
    const div = document.createElement('div');
    div.id = 'typing';
    div.className = 'typing';
    div.innerHTML = '<span></span><span></span><span></span>';
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function hideTyping() {
    const t = document.getElementById('typing');
    if (t) t.remove();
  }

  function setStatus(text, type) {
    statusEl.textContent = text;
    statusEl.className = 'status' + (type === 'busy' ? ' busy' : type === 'err' ? ' err' : '');
  }

  window.submitChat = async function () {
    const msg = input.value.trim();
    if (!msg) return;

    input.value = '';
    input.style.height = 'auto';
    addMsg(msg, true);

    sendBtn.disabled = true;
    setStatus('در حال فکر...', 'busy');
    showTyping();

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
      });

      const data = await res.json();
      hideTyping();

      if (!res.ok) {
        addMsg('خطا: ' + (data.detail || res.statusText || 'نامشخص'), false);
        setStatus('خطا', 'err');
        return;
      }

      addMsg(data.reply || '(پاسخ خالی)', false);

      if (data.needs_confirm) {
        confirmText.textContent = '⚠ ' + (data.confirm_description || 'عملیات خطرناک');
        confirmBanner.classList.add('show');
      } else {
        confirmBanner.classList.remove('show');
      }

      setStatus('آماده');
    } catch (err) {
      hideTyping();
      addMsg('خطا در ارتباط: ' + err.message, false);
      setStatus('خطا', 'err');
    } finally {
      sendBtn.disabled = false;
      input.focus();
    }
  };

  window.sendConfirm = async function (approved) {
    confirmBanner.classList.remove('show');
    showTyping();
    setStatus('در حال اجرا...', 'busy');

    try {
      const res = await fetch('/api/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved: approved })
      });
      const data = await res.json();
      hideTyping();
      addMsg(data.reply || '', false);
      setStatus('آماده');
    } catch (err) {
      hideTyping();
      addMsg('خطا: ' + err.message, false);
      setStatus('خطا', 'err');
    }
  };

  // Enter to send
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitChat();
    }
  });

  // Auto-resize
  input.addEventListener('input', function () {
    this.style.height = 'auto';
    this.style.height = Math.min(this.scrollHeight, 128) + 'px';
  });

  // Health check
  fetch('/api/health')
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (d.status !== 'ok') {
        setStatus('کلیدها تنظیم نشده', 'err');
      }
    })
    .catch(function () {});

  input.focus();
})();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    import uvicorn
    print("\n  🌐 GitHub Omni Agent Web UI")
    print("  → http://127.0.0.1:8000\n")
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
