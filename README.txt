پکیج آماده v4 - توضیحات
فایل‌ها:
- bot_app.py : اصلی، آماده برای اجرا در Render (Webhook mode)
- utils/astro.py : توابع نمونه برای هوروسکوپ، نماد، سنگ، گیاه، چارت، لینک‌ها
- utils/healing.py : توابع نمونه برای پیشنهادات حوزه‌ای
- requirements.txt : پکیج‌های لازم
- render.yaml : نمونه تنظیمات Render (pythonVersion: 3.12.6)

نکات راه‌اندازی:
1) در Render متغیرهای محیطی زیر را ست کنید:
   - BOT_TOKEN = توکن ربات تلگرام
   - WEBHOOK_URL = https://<your-service>.onrender.com
2) Deploy کنید.
3) لاگ‌ها را بررسی کنید؛ run_webhook در زمان اجرا webhook را ثبت می‌کند.
4) اگر توابع واقعی خود را دارید، جایگزین محتویات فایل‌های utils/* کنید.
