# bot_app.py - Polished production-ready webhook bot for Render
# Keeps variable names as requested: BOT_TOKEN, WEBHOOK_URL, PORT, MAIN_MENU
import os
import logging
from typing import Dict, Any
from flask import Flask, request, jsonify
from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from persiantools.jdatetime import JalaliDate

# Environment variables (Render)
BOT_TOKEN = os.environ.get("BOT_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 10000))

if not BOT_TOKEN:
    raise ValueError("❌ متغیر محیطی BOT_TOKEN تنظیم نشده است.")
if not WEBHOOK_URL:
    raise ValueError("❌ متغیر محیطی WEBHOOK_URL تنظیم نشده است.")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Build application
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Import utils (astro and healing)
try:
    from utils import astro, healing
except Exception as e:
    logger.exception("خطا در ایمپورت ماژول‌های utils: %s", e)
    # Continue - handlers will return friendly messages if functions missing

# MAIN MENU - keep variable name MAIN_MENU
MAIN_MENU = ReplyKeyboardMarkup(
    [
        ["📋 معرفی ربات", "🛠 خدمات ربات"],
        ["🔮 طالع‌بینی (امروز)", "🗓 طالع‌بینی (تاریخ تولد)"],
        ["🏷️ نماد شخصی", "💎 سنگ شخصی"],
        ["🌿 گیاه شخصی", "📈 چارت تولد"],
        ["🎯 پیشنهاد شخصی", "🌐 وب‌سایت / شبکه‌ها"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False,
)

# Conversation states for birthdate flow
HOR_CAL, HOR_YEAR, HOR_MONTH, HOR_DAY = range(4)

# Predefined selection lists (chunked in UI)
SHAMSI_YEARS = [str(y) for y in range(1360, 1407)]
MILADI_YEARS = [str(y) for y in range(1970, 2026)]
MONTHS = [str(m) for m in range(1, 13)]
DAYS = [str(d) for d in range(1, 32)]

def chunked(lst, n):
    return [lst[i : i + n] for i in range(0, len(lst), n)]

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! 🤍\n\nربات تخصصی طالع‌بینی و راهنمای انرژی شما فعال شد.\nبرای شروع یکی از گزینه‌های منو را انتخاب کنید.",
        reply_markup=MAIN_MENU,
    )

async def intro_bot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = astro.bot_intro()
    except Exception:
        text = (
            "🔰 معرفی ربات:\n\nاین ربات طالع‌بینی، نمادشناسی، سنگ و گیاه شخصی‌سازی‌شده،"
            " پیشنهادات حوزه‌ای و چارت تولد ارائه می‌دهد."
        )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)

async def services_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = astro.services_list()
    except Exception:
        text = (
            "🛠 خدمات ربات:\n"
            "• طالع‌بینی (امروز / تاریخ تولد)\n"
            "• نماد شخصی (عکس + توضیحات)\n"
            "• سنگ شخصی\n"
            "• گیاه شخصی\n"
            "• پیشنهادات شخصی (سلامت/ثروت/عشق/شغل/موفقیت)\n"
            "• نمایش چارت تولد\n"
            "• لینک‌های خرید زیورآلات مرتبط\n"
        )
    await update.message.reply_text(text, reply_markup=MAIN_MENU)

# Horoscope today
async def horoscope_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = astro.get_daily_horoscope()
    except Exception as e:
        logger.exception("Error in get_daily_horoscope: %s", e)
        text = "خطا در دریافت هوروسکوپ امروز. لطفا بعدا تلاش کنید."
    await update.message.reply_text(f"🔮 هوروسکوپ امروز:\n\n{text}", reply_markup=MAIN_MENU)

# Begin birth-date flow - choose calendar
async def horoscope_birth_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["هجری شمسی", "میلادی"], ["🔙 بازگشت"]]
    await update.message.reply_text("لطفاً نوع تقویم را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))
    return HOR_CAL

async def horoscope_cal_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cal = update.message.text.strip()
    if cal not in ("هجری شمسی", "میلادی"):
        await update.message.reply_text("انتخاب نامعتبر. بازگشت به منو.", reply_markup=MAIN_MENU)
        return ConversationHandler.END
    context.user_data["hor_calendar"] = cal
    # send years in chunked keyboard
    years = SHAMSI_YEARS if cal == "هجری شمسی" else MILADI_YEARS
    kb = chunked(years, 5)
    await update.message.reply_text("سال تولد را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True))
    return HOR_YEAR

async def horoscope_select_year(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    try:
        y = int(txt)
        context.user_data["hor_year"] = y
    except Exception:
        await update.message.reply_text("سال نامعتبر؛ لطفاً از دکمه‌ها انتخاب کنید.")
        return HOR_YEAR
    await update.message.reply_text("ماه تولد را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(chunked(MONTHS, 3), resize_keyboard=True, one_time_keyboard=True))
    return HOR_MONTH

async def horoscope_select_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    try:
        m = int(txt)
        if not (1 <= m <= 12):
            raise ValueError
        context.user_data["hor_month"] = m
    except Exception:
        await update.message.reply_text("ماه نامعتبر؛ لطفاً از دکمه‌ها انتخاب کنید.")
        return HOR_MONTH
    await update.message.reply_text("روز تولد را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(chunked(DAYS, 7), resize_keyboard=True, one_time_keyboard=True))
    return HOR_DAY

async def horoscope_select_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = update.message.text.strip()
    try:
        d = int(txt)
        if not (1 <= d <= 31):
            raise ValueError
        context.user_data["hor_day"] = d
    except Exception:
        await update.message.reply_text("روز نامعتبر؛ لطفاً از دکمه‌ها انتخاب کنید.")
        return HOR_DAY

    cal = context.user_data.get("hor_calendar")
    y = context.user_data.get("hor_year")
    m = context.user_data.get("hor_month")
    d = context.user_data.get("hor_day")

    try:
        if cal == "هجری شمسی":
            g = JalaliDate(y, m, d).to_gregorian()
            gy, gm, gd = g.year, g.month, g.day
        else:
            gy, gm, gd = y, m, d

        iso_date = f"{gy:04d}-{gm:02d}-{gd:02d}"
        horoscope_text = astro.get_horoscope(iso_date)
        await update.message.reply_text(f"🔮 هوروسکوپ برای {iso_date}:\n\n{horoscope_text}", reply_markup=MAIN_MENU)
    except Exception as e:
        logger.exception("Error generating horoscope for birth date: %s", e)
        await update.message.reply_text(f"خطا در تولید هوروسکوپ: {e}", reply_markup=MAIN_MENU)

    # cleanup
    for k in ("hor_calendar", "hor_year", "hor_month", "hor_day"):
        context.user_data.pop(k, None)

    return ConversationHandler.END

# Symbol / stone / plant handlers using utils.astro
async def symbol_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        res = astro.get_personal_symbol(user_id)
    except Exception as e:
        logger.exception("Error in get_personal_symbol: %s", e)
        res = "نماد شخصی در دسترس نیست."
    if isinstance(res, dict):
        caption = res.get("text", "")
        img = res.get("image_url") or res.get("image_path")
        if img:
            try:
                await update.message.reply_photo(photo=img, caption=caption, reply_markup=MAIN_MENU)
            except Exception:
                await update.message.reply_text(caption, reply_markup=MAIN_MENU)
        else:
            await update.message.reply_text(caption, reply_markup=MAIN_MENU)
    else:
        await update.message.reply_text(str(res), reply_markup=MAIN_MENU)

async def stone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        res = astro.get_personal_stone(user_id)
    except Exception as e:
        logger.exception("Error in get_personal_stone: %s", e)
        res = "سنگ شخصی در دسترس نیست."
    if isinstance(res, dict):
        caption = res.get("text", "")
        img = res.get("image_url") or res.get("image_path")
        if img:
            try:
                await update.message.reply_photo(photo=img, caption=caption, reply_markup=MAIN_MENU)
            except Exception:
                await update.message.reply_text(caption, reply_markup=MAIN_MENU)
        else:
            await update.message.reply_text(caption, reply_markup=MAIN_MENU)
    else:
        await update.message.reply_text(str(res), reply_markup=MAIN_MENU)

async def plant_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        res = astro.get_personal_plant(user_id)
    except Exception as e:
        logger.exception("Error in get_personal_plant: %s", e)
        res = "گیاه شخصی در دسترس نیست."
    if isinstance(res, dict):
        caption = res.get("text", "")
        img = res.get("image_url") or res.get("image_path")
        if img:
            try:
                await update.message.reply_photo(photo=img, caption=caption, reply_markup=MAIN_MENU)
            except Exception:
                await update.message.reply_text(caption, reply_markup=MAIN_MENU)
        else:
            await update.message.reply_text(caption, reply_markup=MAIN_MENU)
    else:
        await update.message.reply_text(str(res), reply_markup=MAIN_MENU)

async def suggestion_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["سلامت", "ثروت", "عشق"], ["شغل", "موفقیت"], ["🔙 بازگشت"]]
    await update.message.reply_text("لطفا حوزه مورد نظر را انتخاب کنید:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))

async def suggestion_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    field = update.message.text.strip()
    user_id = update.effective_user.id
    try:
        res = healing.get_suggestion(user_id, field)
    except Exception as e:
        logger.exception("Error in healing.get_suggestion: %s", e)
        res = "پیشنهاد در دسترس نیست."
    if isinstance(res, dict):
        caption = res.get("text", "")
        img = res.get("image_url") or res.get("image_path")
        if img:
            try:
                await update.message.reply_photo(photo=img, caption=caption, reply_markup=MAIN_MENU)
            except Exception:
                await update.message.reply_text(caption, reply_markup=MAIN_MENU)
        else:
            await update.message.reply_text(caption, reply_markup=MAIN_MENU)
    else:
        await update.message.reply_text(str(res), reply_markup=MAIN_MENU)

async def birth_chart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        res = astro.get_birth_chart(user_id)
    except Exception as e:
        logger.exception("Error in get_birth_chart: %s", e)
        res = "چارت تولد در دسترس نیست."
    if isinstance(res, dict):
        caption = res.get("text", "")
        img = res.get("image_url") or res.get("image_path")
        if img:
            try:
                await update.message.reply_photo(photo=img, caption=caption, reply_markup=MAIN_MENU)
            except Exception:
                await update.message.reply_text(caption, reply_markup=MAIN_MENU)
        else:
            await update.message.reply_text(caption, reply_markup=MAIN_MENU)
    else:
        await update.message.reply_text(str(res), reply_markup=MAIN_MENU)

async def shop_links_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        links = astro.get_shop_links()
    except Exception as e:
        logger.exception("Error in get_shop_links: %s", e)
        links = None
    if isinstance(links, list):
        text = "🔗 لینک‌های پیشنهادی:\n\n" + "\n".join([f"• {t}: {u}" for t, u in links])
        await update.message.reply_text(text, reply_markup=MAIN_MENU)
    else:
        await update.message.reply_text(str(links), reply_markup=MAIN_MENU)

# Fallback / echo free text
async def fallback_nontext(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("لطفا یکی از گزینه‌های منو را انتخاب کنید یا متن ارسال کنید.", reply_markup=MAIN_MENU)

async def echo_free(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    mapping = {
        "📋 معرفی ربات": intro_bot,
        "معرفی ربات": intro_bot,
        "🛠 خدمات ربات": services_list,
        "خدمات ربات": services_list,
        "🔮 طالع‌بینی (امروز)": horoscope_today,
        "طالع‌بینی (امروز)": horoscope_today,
        "🗓 طالع‌بینی (تاریخ تولد)": horoscope_birth_entry,
        "طالع‌بینی (تاریخ تولد)": horoscope_birth_entry,
        "🏷️ نماد شخصی": symbol_handler,
        "نماد شخصی": symbol_handler,
        "💎 سنگ شخصی": stone_handler,
        "سنگ شخصی": stone_handler,
        "🌿 گیاه شخصی": plant_handler,
        "گیاه شخصی": plant_handler,
        "🎯 پیشنهاد شخصی": suggestion_entry,
        "پیشنهاد شخصی": suggestion_entry,
        "📈 چارت تولد": birth_chart_handler,
        "چارت تولد": birth_chart_handler,
        "🌐 وب‌سایت / شبکه‌ها": shop_links_handler,
    }
    handler = mapping.get(text)
    if handler:
        return await handler(update, context)
    # fallback: try to detect ISO date YYYY-MM-DD
    if text.count("-") == 2 and all(part.isdigit() for part in text.split("-")):
        try:
            res = astro.get_horoscope(text)
            await update.message.reply_text(res, reply_markup=MAIN_MENU)
            return
        except Exception as e:
            logger.exception("Error in get_horoscope free text: %s", e)
            await update.message.reply_text("خطا در پردازش تاریخ. لطفا از منو استفاده کنید.", reply_markup=MAIN_MENU)
            return
    await update.message.reply_text("پیام شما دریافت شد. لطفاً از منو یکی از گزینه‌ها را انتخاب کنید.", reply_markup=MAIN_MENU)

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", intro_bot))

hor_conv = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("^(🗓 طالع‌بینی \\(تاریخ تولد\\)|طالع‌بینی \\(تاریخ تولد\\))$"), horoscope_birth_entry)],
    states={
        HOR_CAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_cal_selected)],
        HOR_YEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_select_year)],
        HOR_MONTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_select_month)],
        HOR_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, horoscope_select_day)],
    },
    fallbacks=[CommandHandler("cancel", lambda u, c: u.message.reply_text("لغو شد.", reply_markup=MAIN_MENU))],
    per_message=False,
)
application.add_handler(hor_conv)

# Services & menu handlers mapping via regex
application.add_handler(MessageHandler(filters.Regex("^(📋 معرفی ربات|معرفی ربات)$"), intro_bot))
application.add_handler(MessageHandler(filters.Regex("^(🛠 خدمات ربات|خدمات ربات)$"), services_list))
application.add_handler(MessageHandler(filters.Regex("^(🔮 طالع‌بینی \\(امروز\\)|طالع‌بینی \\(امروز\\))$"), horoscope_today))
application.add_handler(MessageHandler(filters.Regex("^(🏷️ نماد شخصی|نماد شخصی)$"), symbol_handler))
application.add_handler(MessageHandler(filters.Regex("^(💎 سنگ شخصی|سنگ شخصی)$"), stone_handler))
application.add_handler(MessageHandler(filters.Regex("^(🌿 گیاه شخصی|گیاه شخصی)$"), plant_handler))
application.add_handler(MessageHandler(filters.Regex("^(🎯 پیشنهاد شخصی|پیشنهاد شخصی)$"), suggestion_entry))
application.add_handler(MessageHandler(filters.Regex("^(📈 چارت تولد|چارت تولد)$"), birth_chart_handler))
application.add_handler(MessageHandler(filters.Regex("^(🌐 وب‌سایت / شبکه‌ها|وب‌سایت / شبکه‌ها)$"), shop_links_handler))

# Non-text fallback and text fallback
application.add_handler(MessageHandler(filters.ALL & ~filters.TEXT, fallback_nontext))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_free))

# Flask webhook endpoint
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "ربات فعال است!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
        update = Update.de_json(data, application.bot)
        application.update_queue.put_nowait(update)
    except Exception as e:
        logger.exception("خطا در پردازش وب‌هوک: %s", e)
    return jsonify({"ok": True})

if __name__ == "__main__":
    # run_webhook will set the webhook URL automatically
    try:
        application.run_webhook(listen="0.0.0.0", port=PORT, url_path="webhook", webhook_url=f"{WEBHOOK_URL}/webhook")
    except Exception as e:
        logger.exception("run_webhook failed; falling back to Flask app.run: %s", e)
        app.run(host="0.0.0.0", port=PORT)
