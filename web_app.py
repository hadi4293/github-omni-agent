#!/usr/bin/env python3
"""GitHub Omni Agent - Web UI"""

import os
import traceback
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from env_loader import load_project_env, env_status

_ENV_PATH, _ENV_LOGS = load_project_env()
for line in _ENV_LOGS:
    print("[env]", line)

from agent import OmniAgent
from memory_patch import apply_memory
from extra_tools_patch import apply_extra_tools

OmniAgent = apply_extra_tools(OmniAgent)
OmniAgent = apply_memory(OmniAgent)

app = FastAPI(title="GitHub Omni Agent")

_agent: Optional[OmniAgent] = None
_pending_confirm: Optional[dict] = None
_agent_error: Optional[str] = None


def get_agent() -> OmniAgent:
    global _agent, _agent_error
    if _agent is not None:
        return _agent

    global _ENV_PATH, _ENV_LOGS
    _ENV_PATH, _ENV_LOGS = load_project_env()
    st = env_status()
    print("[env] status:", st)

    if not st["ok"]:
        missing = []
        if not st["has_gemini"]:
            missing.append("GEMINI_API_KEY")
        if not st["has_github"]:
            missing.append("GITHUB_TOKEN")
        msg = (
            "کلیدهای زیر پیدا نشد: " + ", ".join(missing) + "\n\n"
            + f"مسیر .env لودشده: {_ENV_PATH or 'هیچ'}\n"
            + "فایل .env باید این دو خط را داشته باشد:\n"
            + "GEMINI_API_KEY=...\nGITHUB_TOKEN=...\n"
        )
        _agent_error = msg
        raise RuntimeError(msg)

    def web_confirm(description: str) -> bool:
        global _pending_confirm
        _pending_confirm = {"description": description, "approved": False}
        return False

    try:
        _agent = OmniAgent(
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            github_token=os.getenv("GITHUB_TOKEN", "").strip(),
            confirm_callback=web_confirm,
        )
        _agent_error = None
        return _agent
    except Exception as e:
        _agent_error = f"{type(e).__name__}: {e}"
        raise


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
        reply = agent.run(text) or ""
        if _pending_confirm and not _pending_confirm.get("approved"):
            return JSONResponse({
                "ok": True,
                "reply": reply,
                "needs_confirm": True,
                "confirm_description": _pending_confirm.get("description", ""),
            })
        return JSONResponse({"ok": True, "reply": reply, "needs_confirm": False})
    except Exception as e:
        print("[api/chat ERROR]", traceback.format_exc())
        return JSONResponse(
            {"ok": False, "reply": f"{type(e).__name__}: {e}", "needs_confirm": False},
            status_code=200,
        )


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
        print("[api/confirm ERROR]", traceback.format_exc())
        return JSONResponse(
            {"ok": False, "reply": f"{type(e).__name__}: {e}", "needs_confirm": False},
            status_code=200,
        )


@app.get("/api/health")
async def api_health():
    st = env_status()
    model = None
    err = _agent_error
    if st["ok"]:
        try:
            a = get_agent()
            model = a.model_name
            err = None
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
    else:
        err = f"env missing. loaded_from={_ENV_PATH}"
    return {"ok": st["ok"] and err is None, "model": model, "error": err}


PAGE = r'''<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GitHub Omni Agent</title>
<link href="https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:#07070c; --surface:#12121a; --surface2:#1a1a24;
    --border:rgba(255,255,255,0.07); --text:#ececf1; --muted:#8b8b9e;
    --accent2:#a29bfe;
    --user:linear-gradient(135deg,#6c5ce7 0%,#4834d4 100%);
    --success:#00d2a0; --warning:#f0b429; --danger:#ff6b6b; --radius:16px;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%;font-family:'Vazirmatn',Tahoma,sans-serif;background:var(--bg);color:var(--text);overflow:hidden}
  body::before{content:'';position:fixed;top:-40%;left:-20%;width:70%;height:70%;background:radial-gradient(circle,rgba(108,92,231,0.12) 0%,transparent 70%);pointer-events:none;z-index:0}
  body::after{content:'';position:fixed;bottom:-30%;right:-15%;width:55%;height:55%;background:radial-gradient(circle,rgba(0,210,160,0.06) 0%,transparent 70%);pointer-events:none;z-index:0}
  #app{position:relative;z-index:1;height:100%;display:flex;flex-direction:column;max-width:820px;margin:0 auto}
  header{flex-shrink:0;display:flex;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid var(--border);background:rgba(18,18,26,0.75);backdrop-filter:blur(20px)}
  .brand{display:flex;align-items:center;gap:12px}
  .logo{width:40px;height:40px;border-radius:12px;background:var(--user);display:grid;place-items:center;font-weight:700;font-size:18px;color:#fff;box-shadow:0 4px 20px rgba(108,92,231,0.4)}
  .brand-text h1{font-size:15px;font-weight:600}
  .brand-text p{font-size:11px;color:var(--muted);margin-top:1px}
  #badge{font-size:11px;font-weight:500;padding:5px 12px;border-radius:20px;background:rgba(0,210,160,0.1);color:var(--success);border:1px solid rgba(0,210,160,0.25);display:flex;align-items:center;gap:6px}
  #badge .dot{width:6px;height:6px;border-radius:50%;background:currentColor;animation:pulse 2s infinite}
  #badge.busy{background:rgba(108,92,231,0.12);color:var(--accent2);border-color:rgba(108,92,231,0.3)}
  #badge.err{background:rgba(255,107,107,0.1);color:var(--danger);border-color:rgba(255,107,107,0.3)}
  @keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
  #messages{flex:1;overflow-y:auto;padding:24px 20px;display:flex;flex-direction:column;gap:14px}
  #messages::-webkit-scrollbar{width:4px}
  #messages::-webkit-scrollbar-thumb{background:rgba(255,255,255,0.1);border-radius:4px}
  .row{display:flex;gap:10px;animation:slideUp 0.35s cubic-bezier(0.16,1,0.3,1)}
  .row.bot,.row.err{flex-direction:row-reverse}
  .avatar{width:32px;height:32px;border-radius:10px;flex-shrink:0;display:grid;place-items:center;font-size:13px;font-weight:700;margin-top:2px}
  .row.me .avatar{background:var(--user);color:#fff}
  .row.bot .avatar,.row.err .avatar{background:var(--surface2);border:1px solid var(--border);color:var(--accent2)}
  .bubble{max-width:75%;padding:12px 16px;border-radius:var(--radius);font-size:14px;line-height:1.7;white-space:pre-wrap;word-break:break-word}
  .row.me .bubble{background:var(--user);color:#fff;border-bottom-right-radius:4px;box-shadow:0 4px 18px rgba(108,92,231,0.25)}
  .row.bot .bubble{background:var(--surface);border:1px solid var(--border);color:var(--text);border-bottom-left-radius:4px}
  .row.err .bubble{background:rgba(255,107,107,0.08);border:1px solid rgba(255,107,107,0.25);color:#ffa8a8;border-bottom-left-radius:4px}
  .typing-row{display:flex;flex-direction:row-reverse;gap:10px}
  .typing-bubble{background:var(--surface);border:1px solid var(--border);border-radius:var(--radius);border-bottom-left-radius:4px;padding:14px 18px;display:flex;gap:5px;align-items:center}
  .typing-bubble span{width:7px;height:7px;border-radius:50%;background:var(--accent2);animation:bounce 1.4s infinite ease-in-out both}
  .typing-bubble span:nth-child(2){animation-delay:0.16s}
  .typing-bubble span:nth-child(3){animation-delay:0.32s}
  @keyframes bounce{0%,80%,100%{transform:scale(0.6);opacity:0.4}40%{transform:scale(1);opacity:1}}
  @keyframes slideUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
  #confirm{display:none;margin:0 20px 10px;padding:14px 16px;background:rgba(240,180,41,0.08);border:1px solid rgba(240,180,41,0.3);border-radius:14px}
  #confirm.show{display:block}
  #confirm-msg{font-size:13px;color:var(--warning);margin-bottom:10px}
  .confirm-btns{display:flex;gap:8px}
  .confirm-btns button{padding:7px 18px;border:none;border-radius:10px;font-family:inherit;font-size:13px;font-weight:500;cursor:pointer}
  #btn-yes{background:var(--warning);color:#1a1200}
  #btn-no{background:var(--surface2);color:var(--text);border:1px solid var(--border)}
  #bottom{flex-shrink:0;padding:12px 20px 18px;border-top:1px solid var(--border);background:rgba(18,18,26,0.75);backdrop-filter:blur(20px)}
  .suggestions{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
  .chip{font-size:12px;padding:6px 14px;border-radius:20px;background:var(--surface);border:1px solid var(--border);color:var(--muted);cursor:pointer;font-family:inherit}
  .chip:hover{border-color:rgba(108,92,231,0.4);color:var(--accent2);background:rgba(108,92,231,0.08)}
  .input-wrap{display:flex;align-items:flex-end;gap:10px;background:var(--surface);border:1px solid var(--border);border-radius:18px;padding:6px 6px 6px 16px}
  .input-wrap:focus-within{border-color:rgba(108,92,231,0.5);box-shadow:0 0 0 3px rgba(108,92,231,0.12)}
  #inp{flex:1;background:transparent;border:none;outline:none;color:var(--text);font-family:inherit;font-size:14px;line-height:1.5;resize:none;max-height:120px;padding:8px 0}
  #inp::placeholder{color:var(--muted)}
  #btn{width:42px;height:42px;border:none;border-radius:14px;background:var(--user);color:#fff;cursor:pointer;display:grid;place-items:center;flex-shrink:0;box-shadow:0 4px 16px rgba(108,92,231,0.35)}
  #btn:disabled{opacity:0.4;cursor:not-allowed;box-shadow:none}
  #btn svg{width:18px;height:18px;fill:currentColor}
</style>
</head>
<body>
<div id="app">
  <header>
    <div class="brand">
      <div class="logo">G</div>
      <div class="brand-text">
        <h1>GitHub Omni Agent</h1>
        <p id="model-label">gemini · رایگان</p>
      </div>
    </div>
    <div id="badge"><span class="dot"></span> آماده</div>
  </header>
  <div id="messages">
    <div class="row bot">
      <div class="avatar">AI</div>
      <div class="bubble">سلام 👋 من GitHub Omni Agent هستم.

ریپو، فایل، Issue، PR، Actions، Release و Codespace را پشتیبانی می‌کنم.
حافظه فعال است. برای پاک کردن بنویس: پاک کردن حافظه</div>
    </div>
  </div>
  <div id="confirm">
    <div id="confirm-msg"></div>
    <div class="confirm-btns">
      <button id="btn-yes" type="button">تأیید و اجرا</button>
      <button id="btn-no" type="button">لغو</button>
    </div>
  </div>
  <div id="bottom">
    <div class="suggestions" id="suggestions">
      <button class="chip" type="button" data-q="لیست ریپوهای من رو نشون بده">📦 ریپوها</button>
      <button class="chip" type="button" data-q="workflowهای ریپوی github-omni-agent رو لیست کن">⚙️ Actions</button>
      <button class="chip" type="button" data-q="آخرین releaseهای github-omni-agent">🏷️ Releases</button>
      <button class="chip" type="button" data-q="codespaceهای من رو نشون بده">💻 Codespaces</button>
    </div>
    <div class="input-wrap">
      <textarea id="inp" rows="1" placeholder="پیام خود را بنویس..."></textarea>
      <button id="btn" type="button"><svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg></button>
    </div>
  </div>
</div>
<script>
(function(){
  var messages=document.getElementById("messages");
  var inp=document.getElementById("inp");
  var btn=document.getElementById("btn");
  var badge=document.getElementById("badge");
  var confirmBox=document.getElementById("confirm");
  var confirmMsg=document.getElementById("confirm-msg");
  var suggestions=document.getElementById("suggestions");
  function addMsg(text,kind){
    var row=document.createElement("div"); row.className="row "+kind;
    var av=document.createElement("div"); av.className="avatar"; av.textContent=kind==="me"?"تو":"AI";
    var bub=document.createElement("div"); bub.className="bubble"; bub.textContent=text;
    row.appendChild(av); row.appendChild(bub); messages.appendChild(row);
    messages.scrollTop=messages.scrollHeight;
  }
  function showTyping(){
    var row=document.createElement("div"); row.className="typing-row"; row.id="typing";
    row.innerHTML='<div class="avatar" style="background:#1a1a24;border:1px solid rgba(255,255,255,0.07);color:#a29bfe;width:32px;height:32px;border-radius:10px;display:grid;place-items:center;font-size:13px;font-weight:700">AI</div><div class="typing-bubble"><span></span><span></span><span></span></div>';
    messages.appendChild(row); messages.scrollTop=messages.scrollHeight;
  }
  function hideTyping(){ var t=document.getElementById("typing"); if(t)t.remove(); }
  function setBusy(on){
    btn.disabled=on;
    if(on){ badge.className="busy"; badge.innerHTML='<span class="dot"></span> در حال کار...'; }
    else { badge.className=""; badge.innerHTML='<span class="dot"></span> آماده'; }
  }
  function setErr(){ badge.className="err"; badge.innerHTML='<span class="dot"></span> خطا'; }
  async function send(text){
    text=(text||inp.value).trim(); if(!text)return;
    inp.value=""; inp.style.height="auto"; if(suggestions)suggestions.style.display="none";
    addMsg(text,"me"); setBusy(true); showTyping();
    try{
      var res=await fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text})});
      var data=await res.json(); hideTyping();
      var reply=(data&&data.reply!=null)?String(data.reply):"(پاسخ خالی)";
      addMsg(reply, data&&data.ok===false?"err":"bot");
      if(data&&data.needs_confirm){ confirmMsg.textContent="⚠ "+(data.confirm_description||"عملیات خطرناک"); confirmBox.classList.add("show"); }
      else confirmBox.classList.remove("show");
      if(data&&data.ok===false) setErr(); else setBusy(false);
    }catch(e){ hideTyping(); addMsg("خطای شبکه: "+e.message,"err"); setErr(); btn.disabled=false; }
    inp.focus();
  }
  async function doConfirm(approved){
    confirmBox.classList.remove("show"); setBusy(true); showTyping();
    try{
      var res=await fetch("/api/confirm",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({approved:approved})});
      var data=await res.json(); hideTyping();
      addMsg(String(data.reply||""), data.ok===false?"err":"bot"); setBusy(false);
    }catch(e){ hideTyping(); addMsg("خطا: "+e.message,"err"); setErr(); btn.disabled=false; }
  }
  btn.addEventListener("click",function(){send();});
  document.getElementById("btn-yes").addEventListener("click",function(){doConfirm(true);});
  document.getElementById("btn-no").addEventListener("click",function(){doConfirm(false);});
  inp.addEventListener("keydown",function(e){ if(e.key==="Enter"&&!e.shiftKey){e.preventDefault();send();} });
  inp.addEventListener("input",function(){ this.style.height="auto"; this.style.height=Math.min(this.scrollHeight,120)+"px"; });
  var chips=document.querySelectorAll(".chip");
  for(var i=0;i<chips.length;i++){ chips[i].addEventListener("click",function(){ send(this.getAttribute("data-q")); }); }
  fetch("/api/health").then(function(r){return r.json();}).then(function(d){
    if(d.model) document.getElementById("model-label").textContent=d.model+" · رایگان";
    if(!d.ok){ badge.className="err"; badge.innerHTML='<span class="dot"></span> مشکل .env'; if(d.error) addMsg("مشکل: "+d.error,"err"); }
  }).catch(function(){});
  inp.focus();
})();
</script>
</body>
</html>
'''


if __name__ == "__main__":
    import uvicorn
    print("\n  GitHub Omni Agent")
    print(f"  env loaded from: {_ENV_PATH}")
    print("  http://127.0.0.1:8000\n")
    uvicorn.run("web_app:app", host="127.0.0.1", port=8000, reload=False)
