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
# ابتدا requirements.txt را کپی کرده و وابستگی‌ها را نصب می‌کند تا از Docker Layer Caching بهینه استفاده شود.
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 5. کپی کردن سورس کد برنامه
# کپی کردن تمام فایل‌های سورس (bot_app.py، utils.py، keyboards.py و...)
COPY . .

# 6. دستور اجرای نهایی و صریح (python -m uvicorn)
# اجرای uvicorn به صورت ماژول پایتون.
# 'bot_app:app' به ماژول 'bot_app.py' و نمونه FastAPI به نام 'app' اشاره می‌کند.
CMD ["python", "-m", "uvicorn", "bot_app:app", "--host", "0.0.0.0", "--port", "8080"]
