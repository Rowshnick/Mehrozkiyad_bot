# استفاده از یک Image رسمی پایتون 3.13 (مناسب برای Render)
FROM python:3.13-slim

# تنظیم متغیرهای محیطی برای اجرای بهتر پایتون
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# ایجاد پوشه کار و رفتن به آن
ENV APP_HOME /usr/src/app
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# 1. نصب وابستگی‌های سیستمی حیاتی برای کامپایل پکیج‌های باینری
# build-essential شامل GCC و سایر ابزارهای مورد نیاز برای pyswisseph است.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. کپی و نصب وابستگی‌های پایتون
# این مرحله pyswisseph را با استفاده از ابزارهای سیستمی تازه نصب شده، کامپایل می‌کند.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. کپی کردن بقیه کدهای پروژه (bot_app.py و غیره)
COPY . .

# 4. دستور اجرا برای Render/Gunicorn
# این دستور برنامه شما را پس از Deploy آغاز می‌کند.
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "bot_app:app"]
