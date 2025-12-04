1. از یک ایمیج پایتون کوچک و پایدار استفاده کنید
​FROM python:3.11-slim-bullseye
​2. متغیرهای محیطی برای تنظیمات
​ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
ENV PORT 8080
​3. ایجاد و تغییر دایرکتوری کاری
​WORKDIR $APP_HOME
​4. کپی کردن فایل‌های نیازمندی‌ها
​COPY requirements.txt .
​5. نصب نیازمندی‌ها
​RUN pip install --no-cache-dir -r requirements.txt
​6. کپی کردن کل کد سورس
​فرض بر این است که bot_app.py، utils.py، keyboards.py و astrology_core.py اینجا هستند.
​COPY . .
​7. افشای پورت 8080
​EXPOSE 8080
​8. دستور نهایی اجرا (CMD) - اینجاست که خطای پورت حل می‌شود
​ما به طور صریح از 0.0.0.0:8080 استفاده می‌کنیم
​CMD ["uvicorn", "bot_app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
