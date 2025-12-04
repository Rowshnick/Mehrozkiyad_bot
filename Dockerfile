# ----------------------------------------------------------------------
# Dockerfile - نسخه نهایی و عملی
# ----------------------------------------------------------------------

# 1. تصویر پایه پایتون (سبک)
FROM python:3.11-slim-bullseye

# 2. نصب فقط بسته های سیستمی ضروری (مانند Locale)
# نصب 'locales' برای پشتیبانی از UTF-8 و زبان فارسی ضروری است.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    locales \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen && \
    locale-gen en_US.UTF-8 && \
    rm -rf /var/lib/apt/lists/*

# 3. تنظیم متغیرهای محیطی
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
# این متغیرها برای پایتون ضروری هستند
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# مسیر کاری برنامه
ENV APP_HOME /usr/src/app
WORKDIR $APP_HOME

# 4. کپی و نصب وابستگی‌ها
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. کپی کردن سورس کد برنامه
COPY . .

# 6. دستور اجرای نهایی (Exec Form با شل)
# برای تضمین تفسیر متغیر $PORT توسط شل، از "sh -c" استفاده می کنیم.
# این روش قوی ترین راه برای حل مشکل عدم تفسیر متغیر محیطی است.
# ${PORT:-8080} به این معناست: از متغیر محیطی $PORT استفاده کن، در غیر این صورت از 8080 استفاده کن.
CMD ["/bin/sh", "-c", "uvicorn bot_app:app --host 0.0.0.0 --port ${PORT:-8080}"]
