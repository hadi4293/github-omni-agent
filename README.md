# GitHub Omni Agent

**ایجنت همه‌کاره و کاملاً رایگان گیت‌هاب**  
مدل: `gemini-3.5-flash-lite` · رابط وب مدرن + CLI

---

## دو روش اجرا

### ۱) رابط وب (پیشنهادی)

```bash
pip install -r requirements.txt
cp .env.example .env
# فایل .env را پر کن
python web_app.py
```

بعد برو به: **http://127.0.0.1:8000**

### ۲) خط فرمان (CLI)

```bash
python main.py
```

---

## نصب کامل (گام‌به‌گام)

**گام ۱**
```bash
git clone https://github.com/hadi4293/github-omni-agent.git
cd github-omni-agent
```

**گام ۲**
```bash
pip install -r requirements.txt
```

**گام ۳**
```bash
cp .env.example .env
```

**گام ۴** — فایل `.env` را باز کن و پر کن:

```env
GEMINI_API_KEY=کلید_گوگل
GITHUB_TOKEN=توکن_گیت‌هاب
```

- کلید گوگل: [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
- توکن گیت‌هاب (classic): [github.com/settings/tokens](https://github.com/settings/tokens)  
  دسترسی‌ها: `repo` + `workflow` + `read:org` + `gist`

**گام ۵** — اجرا:
```bash
python web_app.py
```

---

## ویژگی‌ها

| دسته | قابلیت‌ها |
|------|----------|
| ریپو | لیست، ساخت، حذف (با تأیید)، ساختار، ستاره |
| فایل | خواندن، ساخت/ویرایش + کامیت، حذف (با تأیید) |
| Issue | لیست، ساخت، کامنت، بستن، باز کردن، ویرایش |
| PR | لیست، ساخت، Merge (با تأیید)، بستن |
| برنچ/کامیت | لیست برنچ، ساخت برنچ، لیست کامیت |
| سایر | جستجوی کد، اطلاعات حساب، ساخت Gist |

عملیات خطرناک همیشه تأیید می‌خواهند.

---

## مدل

`gemini-3.5-flash-lite` — سریع، ارزان و مناسب ایجنت

---

ساخته شده برای استفاده شخصی و رایگان.
