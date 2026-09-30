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

# یک نمونه ایجنت برای هر session ساده (در production بهتره per-user باشه)
_agent: Optional[OmniAgent] = None
_pending_confirm: Optional[dict] = None  # برای تأیید عملیات خطرناک


def get_agent() -> OmniAgent:
    global _agent
    if _agent is None:
        gemini_key = os.getenv("GEMINI_API_KEY")
        github_token = os.getenv("GITHUB_TOKEN")
        if not gemini_key or not github_token:
            raise RuntimeError("GEMINI_API_KEY یا GITHUB_TOKEN تنظیم نشده")

        def web_confirm(description: str) -> bool:
            # در وب، تأیید را از طریق API جداگانه می‌گیریم
            # اینجا False برمی‌گردونیم تا ایجنت پیام «نیاز به تأیید» بده
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

        # اگر عملیات خطرناک درخواست شده بود
        if _pending_confirm and not _pending_confirm.get("approved"):
            return JSONResponse({
                "reply": reply,
                "needs_confirm": True,
                "confirm_description": _pending_confirm["description"],
            })

        return JSONResponse({"reply": reply, "needs_confirm": False})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/confirm")
async def confirm(req: ConfirmRequest):
    global _pending_confirm, _agent
    if not _pending_confirm:
        return JSONResponse({"reply": "هیچ عملیات معلقی وجود ندارد.", "needs_confirm": False})

    if req.approved:
        # کاربر تأیید کرد → دوباره پیام قبلی را با تأیید بفرست
        # برای سادگی، به کاربر می‌گیم که دوباره دستور را بزند یا مستقیم اجرا کنیم
        # اینجا یک راه ساده: تأیید را ذخیره می‌کنیم و از کاربر می‌خواهیم دوباره بگوید
        _pending_confirm["approved"] = True
        # چون callback قبلاً False برگردونده، ساده‌ترین راه این است که
        # یک پیام سیستمی بفرستیم
        try:
            agent = get_agent()
            # override موقت
            original_cb = agent.confirm_callback
            agent.confirm_callback = lambda d: True
            reply = agent.run("بله، تأیید می‌کنم. عملیات را انجام بده.")
            agent.confirm_callback = original_cb
            _pending_confirm = None
            return JSONResponse({"reply": reply, "needs_confirm": False})
        except Exception as e:
            return JSONResponse({"reply": f"خطا: {e}", "needs_confirm": False})
    else:
        _pending_confirm = None
        return JSONResponse({"reply": "عملیات لغو شد.", "needs_confirm": False})


@app.get("/api/health")
async def health():
    ok = bool(os.getenv("GEMINI_API_KEY") and os.getenv("GITHUB_TOKEN"))
    return {"status": "ok" if ok else "missing_env", "model": "gemini-3.5-flash-lite"}


HTML_PAGE = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>GitHub Omni Agent</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      theme: {
        extend: {
          colors: {
            brand: { 50:'#f0f9ff',100:'#e0f2fe',200:'#bae6fd',300:'#7dd3fc',400:'#38bdf8',500:'#0ea5e9',600:'#0284c7',700:'#0369a1',800:'#075985',900:'#0c4a6e' },
            dark: { 800:'#1e1e2e',900:'#11111b',950:'#0a0a0f' }
          },
          fontFamily: { sans: ['Vazirmatn','Inter','system-ui','sans-serif'] }
        }
      }
    }
  </script>
  <link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    body { font-family: 'Vazirmatn', system-ui, sans-serif; }
    .msg-user { background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%); }
    .msg-bot  { background: #1e1e2e; border: 1px solid #2a2a3c; }
    .scrollbar::-webkit-scrollbar { width: 6px; }
    .scrollbar::-webkit-scrollbar-track { background: transparent; }
    .scrollbar::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
    #chat-box { scroll-behavior: smooth; }
    .typing span { animation: blink 1.4s infinite both; }
    .typing span:nth-child(2) { animation-delay: 0.2s; }
    .typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink { 0%,80%,100%{opacity:0} 40%{opacity:1} }
    .fade-in { animation: fadeIn 0.3s ease; }
    @keyframes fadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:none} }
  </style>
</head>
<body class="bg-dark-950 text-gray-100 min-h-screen flex flex-col">

  <!-- Header -->
  <header class="border-b border-gray-800 bg-dark-900/80 backdrop-blur sticky top-0 z-20">
    <div class="max-w-3xl mx-auto px-4 py-3 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-brand-500/20">G</div>
        <div>
          <h1 class="font-semibold text-base leading-tight">GitHub Omni Agent</h1>
          <p class="text-xs text-gray-400">gemini-3.5-flash-lite · رایگان</p>
        </div>
      </div>
      <div id="status" class="text-xs px-2.5 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">آماده</div>
    </div>
  </header>

  <!-- Chat Area -->
  <main class="flex-1 overflow-hidden flex flex-col max-w-3xl w-full mx-auto">
    <div id="chat-box" class="flex-1 overflow-y-auto scrollbar px-4 py-6 space-y-4">
      <!-- Welcome -->
      <div class="fade-in msg-bot rounded-2xl rounded-tr-sm px-4 py-3 max-w-[85%] text-sm leading-relaxed">
        سلام 👋 من <strong>GitHub Omni Agent</strong> هستم.<br>
        می‌تونی فارسی یا انگلیسی ازم بخوای کارهای گیت‌هاب رو انجام بدم.<br><br>
        مثلاً:<br>
        • لیست ریپوهای من رو نشون بده<br>
        • اطلاعات حساب من رو بگو<br>
        • یه issue جدید بساز
      </div>
    </div>

    <!-- Confirm Banner -->
    <div id="confirm-banner" class="hidden mx-4 mb-2 p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-sm">
      <p id="confirm-text" class="text-amber-200 mb-2"></p>
      <div class="flex gap-2">
        <button onclick="sendConfirm(true)" class="px-4 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-black font-medium text-sm transition">تأیید و اجرا</button>
        <button onclick="sendConfirm(false)" class="px-4 py-1.5 rounded-lg bg-gray-700 hover:bg-gray-600 text-sm transition">لغو</button>
      </div>
    </div>

    <!-- Input -->
    <div class="border-t border-gray-800 bg-dark-900/60 backdrop-blur p-4">
      <form id="chat-form" class="flex gap-2 items-end">
        <textarea id="user-input" rows="1" placeholder="پیامت را بنویس..." 
          class="flex-1 resize-none bg-dark-800 border border-gray-700 rounded-2xl px-4 py-3 text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/50 transition max-h-32"
          onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();submitChat()}"></textarea>
        <button type="submit" id="send-btn"
          class="w-11 h-11 rounded-xl bg-brand-500 hover:bg-brand-400 active:scale-95 transition flex items-center justify-center shadow-lg shadow-brand-500/25 disabled:opacity-50">
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </form>
    </div>
  </main>

<script>
const chatBox = document.getElementById('chat-box');
const form = document.getElementById('chat-form');
const input = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const statusEl = document.getElementById('status');
const confirmBanner = document.getElementById('confirm-banner');
const confirmText = document.getElementById('confirm-text');

function addMsg(text, isUser) {
  const div = document.createElement('div');
  div.className = `fade-in ${isUser ? 'msg-user text-white ml-auto' : 'msg-bot'} rounded-2xl ${isUser ? 'rounded-tl-sm' : 'rounded-tr-sm'} px-4 py-3 max-w-[85%] text-sm leading-relaxed whitespace-pre-wrap`;
  div.innerHTML = formatMarkdown(text);
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function formatMarkdown(t) {
  return t
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code class="bg-black/30 px-1 rounded text-brand-300">$1</code>')
    .replace(/\n/g, '<br>');
}

function showTyping() {
  const div = document.createElement('div');
  div.id = 'typing';
  div.className = 'msg-bot rounded-2xl rounded-tr-sm px-4 py-3 w-fit typing';
  div.innerHTML = '<span>•</span><span>•</span><span>•</span>';
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function hideTyping() {
  const t = document.getElementById('typing');
  if (t) t.remove();
}

form.addEventListener('submit', e => { e.preventDefault(); submitChat(); });

async function submitChat() {
  const msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  input.style.height = 'auto';
  addMsg(msg, true);
  sendBtn.disabled = true;
  statusEl.textContent = 'در حال فکر...';
  statusEl.className = 'text-xs px-2.5 py-1 rounded-full bg-brand-500/10 text-brand-300 border border-brand-500/20';
  showTyping();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: msg})
    });
    const data = await res.json();
    hideTyping();
    if (!res.ok) throw new Error(data.detail || 'خطا');
    addMsg(data.reply, false);
    if (data.needs_confirm) {
      confirmText.textContent = '⚠ ' + data.confirm_description;
      confirmBanner.classList.remove('hidden');
    } else {
      confirmBanner.classList.add('hidden');
    }
  } catch (err) {
    hideTyping();
    addMsg('خطا: ' + err.message, false);
  } finally {
    sendBtn.disabled = false;
    statusEl.textContent = 'آماده';
    statusEl.className = 'text-xs px-2.5 py-1 rounded-full bg-green-500/10 text-green-400 border border-green-500/20';
    input.focus();
  }
}

async function sendConfirm(approved) {
  confirmBanner.classList.add('hidden');
  showTyping();
  statusEl.textContent = 'در حال اجرا...';
  try {
    const res = await fetch('/api/confirm', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({approved})
    });
    const data = await res.json();
    hideTyping();
    addMsg(data.reply, false);
  } catch (err) {
    hideTyping();
    addMsg('خطا: ' + err.message, false);
  }
  statusEl.textContent = 'آماده';
}

// auto-resize textarea
input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = Math.min(input.scrollHeight, 128) + 'px';
});

// health check
fetch('/api/health').then(r => r.json()).then(d => {
  if (d.status !== 'ok') {
    statusEl.textContent = 'کلیدها تنظیم نشده';
    statusEl.className = 'text-xs px-2.5 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/20';
  }
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    import uvicorn
    print("\n  🌐 GitHub Omni Agent Web UI")
    print("  → http://127.0.0.1:8000\n")
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
