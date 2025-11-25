# utils/payment.py
import sqlite3
from datetime import datetime
import uuid

DB_PATH = "data/payment.db"

# ایجاد دیتابیس و جدول‌ها
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # جدول کاربران
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            referred_by TEXT,
            created_at TEXT
        )
    """)
    # جدول پرداخت‌ها
    c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            user_id INTEGER,
            amount REAL,
            status TEXT,
            created_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
        )
    """)
    conn.commit()
    conn.close()

# ثبت کاربر
def add_user(user_id: int, username: str, referred_by: str = None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT OR IGNORE INTO users (user_id, username, referred_by, created_at)
        VALUES (?, ?, ?, ?)
    """, (user_id, username, referred_by, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

# ایجاد پرداخت جدید
def create_payment(user_id: int, amount: float) -> str:
    payment_id = str(uuid.uuid4())
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO payments (payment_id, user_id, amount, status, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (payment_id, user_id, amount, "pending", datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return payment_id

# بروزرسانی وضعیت پرداخت
def update_payment_status(payment_id: str, status: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE payments SET status = ? WHERE payment_id = ?
    """, (status, payment_id))
    conn.commit()
    conn.close()

# دریافت تاریخچه پرداخت‌ها
def get_user_payments(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM payments WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows
