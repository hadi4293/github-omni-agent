# GitHub Omni Agent

**ایجنت همه‌کاره و رایگان گیت‌هاب** با قدرت Gemini (Google AI Studio)

## ویژگی‌ها
- دسترسی کامل به گیت‌هاب (خوندن، نوشتن، issue، PR، کامیت، جستجو و ...)
- فقط برای عملیات خطرناک (حذف فایل، حذف ریپو، force push و ...) ازت اجازه می‌گیره
- کاملاً رایگان (Gemini Free Tier + GitHub Token خودت)
- رابط خط فرمان ساده و فارسی/انگلیسی

## نصب سریع

```bash
git clone https://github.com/hadi4293/github-omni-agent.git
cd github-omni-agent
pip install -r requirements.txt
cp .env.example .env
```

سپس فایل `.env` رو باز کن و این دو تا رو پر کن:

```env
GEMINI_API_KEY=your_google_ai_studio_key
GITHUB_TOKEN=your_github_personal_access_token
```

### چطور کلیدها رو بگیریم؟

1. **Gemini API Key (رایگان):**
   - برو به [aistudio.google.com](https://aistudio.google.com)
   - Get API Key بزن و کپی کن

2. **GitHub Token:**
   - برو به GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - New token (classic) بساز
   - دسترسی‌های پیشنهادی: `repo`, `workflow`, `read:org`, `gist`
   - توکن رو کپی کن

## اجرا

```bash
python main.py
```

بعدش فقط فارسی یا انگلیسی بنویس، مثلاً:

- «لیست ریپوهای من رو نشون بده»
- «توی ریپوی X فایل README رو بخون»
- «یه issue جدید توی ریپوی Y بساز با عنوان ...»
- «این کد رو توی فایل Z کامیت کن»
- «PR بساز از branch feature به main»

## امنیت

عملیات‌های خطرناک (حذف فایل، حذف ریپو، force push و ...) همیشه ازت تأیید می‌گیرن قبل از اجرا.

## ساختار پروژه

```
main.py              # نقطه ورود CLI
agent.py             # هسته ایجنت + Gemini Function Calling
tools/
  github_tools.py    # تمام ابزارهای گیت‌هاب
requirements.txt
.env.example
```

ساخته شده با ❤️ برای استفاده شخصی و رایگان.
