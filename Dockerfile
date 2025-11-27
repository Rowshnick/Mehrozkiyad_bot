# استفاده از یک Image پایه پایتون 3.13
FROM python:3.13-slim

# تنظیم متغیرهای محیطی
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /usr/src/app
RUN mkdir -p $APP_HOME
WORKDIR $APP_HOME

# 1. نصب وابستگی‌های سیستمی (مهم برای کامپایل pyswisseph)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. کپی و نصب وابستگی‌های پایتون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. کپی بقیه کدهای پروژه
COPY . .

# 4. دستور اجرا (CMD) ⬅️ **این خط مهم است**
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "bot_app:app"]
