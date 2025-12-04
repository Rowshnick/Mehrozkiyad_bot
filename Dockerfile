1. استفاده از یک ایمیج پایه پایتون کوچک و پایدار
​FROM python:3.11-slim-bullseye
​2. تعریف متغیرهای محیطی
​PYTHONUNBUFFERED برای نمایش فوری لاگ‌ها ضروری است
​ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
​3. ایجاد و تنظیم دایرکتوری کاری
​WORKDIR $APP_HOME
​4. کپی کردن فایل نیازمندی‌ها
​COPY requirements.txt .
​5. نصب نیازمندی‌ها
​RUN pip install --no-cache-dir -r requirements.txt
​6. کپی کردن کل سورس کد برنامه (bot_app.py، utils.py، و غیره)
​COPY . .
​7. افشای پورت 8080
​EXPOSE 8080
​8. دستور نهایی اجرای برنامه (CMD)
​اصلاح حیاتی: پورت را به طور صریح 8080 تعیین می‌کنیم تا خطای '$PORT is not a valid integer' حل شود.
​ما فرض می‌کنیم فایل اصلی برنامه شما bot_app.py نام دارد و شیء FastAPI در آن app است.
​CMD ["uvicorn", "bot_app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]


