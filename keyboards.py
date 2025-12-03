# ======================================================================
# Keyboards Module (keyboards.py)
# این فایل شامل توابعی برای تولید کیبوردهای اینلاین تلگرام است.
# توجه: در محیط دیپلوی، باید مطمئن شوید که کتابخانه 'python-telegram-bot' یا
# معادل آن که شامل این کلاس‌هاست، نصب شده باشد (مثلاً در requirements.txt).
# از آنجایی که ما در bot_app از FastAPI و API مستقیم تلگرام استفاده می‌کنیم،
# این ایمپورت باید با یک ساختار داده‌ای ساده که پیام‌ها را می‌سازد، جایگزین شود.
#
# برای سازگاری با API مستقیم تلگرام/FastAPI:
# ما ساختار داده‌ای مورد نیاز API تلگرام را برمی‌گردانیم.
# ======================================================================

# توجه: ما کلاس‌ها را ایمپورت نمی‌کنیم، بلکه دیکشنری‌های JSON تلگرام را تولید می‌کنیم.

# **قالب ثابت برای Callback Data:**
# <منو>|<زیرمنو>|<پارامتر>
# مثال: 'SERVICES|ASTRO|CHART'

# --- توابع کمکی برای تولید دکمه ---
def create_button(text, callback_data=None, url=None):
    """ایجاد یک شیء دکمه برای API تلگرام"""
    button = {"text": text}
    if callback_data:
        button["callback_data"] = callback_data
    if url:
        button["url"] = url
    return button

def create_keyboard(rows):
    """تولید شیء InlineKeyboardMarkup نهایی برای API تلگرام"""
    return {"inline_keyboard": rows}

# --- منوی اصلی ---
def main_menu_keyboard():
    keyboard = [
        [create_button("به ربات خوش آمدید و معرفی 🌟", callback_data='MAIN|WELCOME|0')],
        [create_button("خدمات 🔮", callback_data='MAIN|SERVICES|0')],
        [create_button("فروشگاه 🛍️", callback_data='MAIN|SHOP|0')],
        [create_button("شبکه‌های اجتماعی و سایت 🌐", callback_data='MAIN|SOCIALS|0')],
        [create_button("درباره ما 🧑‍💻", callback_data='MAIN|ABOUT|0')],
    ]
    return create_keyboard(keyboard)

# --- منوی خدمات (سطح ۲) ---
def services_menu_keyboard():
    keyboard = [
        [create_button("آسترولوژی 🔭", callback_data='SERVICES|ASTRO|0')],
        [create_button("سنگ شناسی 💎", callback_data='SERVICES|GEM|0')],
        [create_button("نماد شناسی (سجیل) ✨", callback_data='SERVICES|SIGIL|0')],
        [create_button("گیاه شناسی 🌿", callback_data='SERVICES|HERB|0')],
        [create_button("بازگشت به منوی اصلی 🔙", callback_data='MAIN|WELCOME|0')], # به MAIN|WELCOME|0 تغییر داده شد
    ]
    return create_keyboard(keyboard)

# --- منوی آسترولوژی (سطح ۳) ---
def astrology_menu_keyboard():
    keyboard = [
        [create_button("تولید چارت تولد (زایچه) 📝", callback_data='SERVICES|ASTRO|CHART_INPUT')], # نیاز به دریافت ورودی از کاربر
        [create_button("پیش‌گویی روزانه ستاره‌شناسی 🗓️", callback_data='SERVICES|ASTRO|DAILY')],
        [create_button("بازگشت به خدمات ↩️", callback_data='MAIN|SERVICES|0')],
    ]
    return create_keyboard(keyboard)

# --- منوهای تخصصی (سطح ۳) ---
def gem_menu_keyboard():
    keyboard = [
        [create_button("سنگ مناسب شخصی 👤", callback_data='SERVICES|GEM|PERSONAL_INPUT')], # نیاز به اطلاعات تولد
        [create_button("خواص هر سنگ 🔍", callback_data='SERVICES|GEM|INFO')],
        [create_button("سنگ هر سال تولد 🎂", callback_data='SERVICES|GEM|YEAR')],
        [create_button("سنگ هر ماه تولد 📅", callback_data='SERVICES|GEM|MONTH')],
        [create_button("بازگشت به خدمات ↩️", callback_data='MAIN|SERVICES|0')],
    ]
    return create_keyboard(keyboard)

# --- منوی فروشگاه (سطح ۲) ---
def shop_menu_keyboard():
    keyboard = [
        [create_button("سفارش پکیج کلی آسترولوژی 🎁", callback_data='SHOP|ORDER|PACKAGE')],
        [create_button("سفارش چارت تولد 📄", callback_data='SHOP|ORDER|CHART')],
        [create_button("سفارش پیشگویی روزانه (۱ ماه) 🔮", callback_data='SHOP|ORDER|DAILY')],
        [create_button("سفارش سنگ شخصی 💍", callback_data='SHOP|ORDER|GEM')],
        [create_button("سفارش نماد (سجیل) شخصی 🖼️", callback_data='SHOP|ORDER|SIGIL')],
        [create_button("سفارش گیاه شخصی 🪴", callback_data='SHOP|ORDER|HERB')],
        [create_button("بازگشت به منوی اصلی 🔙", callback_data='MAIN|WELCOME|0')], # به MAIN|WELCOME|0 تغییر داده شد
    ]
    return create_keyboard(keyboard)

# --- منوی شبکه‌های اجتماعی (سطح ۲) ---
def socials_menu_keyboard():
    # *****************************************************************
    # *نکته: خط آخر در کد اصلی شما سینتکس نادرستی داشت و اصلاح شد.*
    # *همچنین لینک‌ها را به عنوان جایگزین قرار دادم.*
    # *****************************************************************
    keyboard = [
        [create_button("وبسایت 🖥️", url="https://your-website.com")], 
        [create_button("اینستاگرام 📸", url="https://instagram.com/your-page")],
        [create_button("یوتیوب ▶️", url="https://youtube.com/your-channel")],
        [create_button("بازگشت به منوی اصلی 🔙", callback_data='MAIN|WELCOME|0')], # به MAIN|WELCOME|0 تغییر داده شد
    ]
    return create_keyboard([keyboard]) # از آنجایی که کل دکمه‌ها در یک سطر است، نیاز به یک سطح آرایه اضافی داریم
