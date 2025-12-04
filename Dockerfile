1. تعیین ایمیج پایه
​پیشنهاد: استفاده از نسخه معتبر پایتون
​FROM python:3.11-slim-bullseye
​2. تنظیم دایرکتوری کاری
​WORKDIR /app
​3. کپی کردن فایل requirements و نصب پیش‌نیازها
​این دو خط باید دقیقاً به همین ترتیب باشند تا از کش داکر به درستی استفاده شود
​COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
​4. کپی کردن کد برنامه
​COPY . .
​5. دستور اجرا (CMD)
​ما قبلاً این را برای پورت 8080 اصلاح کردیم
​CMD ["uvicorn", "bot_app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
