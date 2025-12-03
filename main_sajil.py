import sajil_part_one
import sajil_part_two
import keyboards # برای بازگرداندن کیبورد در انتها
import utils # برای ارسال پیام نهایی

# ==============================================================================
# تابع اصلی که از bot_app.py فراخوانی می‌شود
# ==============================================================================
async def run_sajil_workflow(chat_id: int, raw_input_data_str: str):
    """
    مدیریت جریان کار کامل سجیل (از ورودی خام تا نتیجه نهایی) و ارسال پیام به کاربر.
    
    Args:
        chat_id: شناسه گفتگوی کاربر تلگرام.
        raw_input_data_str: رشته ورودی خام از کاربر (مثلاً "10, 20.5, 30").
    """
    
    # 1. استخراج لیست ورودی‌ها از رشته (فرض می‌کنیم ورودی‌ها با کاما جدا شده‌اند)
    try:
        raw_input_data = [item.strip() for item in raw_input_data_str.split(',')]
    except Exception:
        await utils.send_telegram_message(
            chat_id, 
            "❌ خطای فرمت ورودی. لطفاً اعداد را با کاما (,) جدا کنید.",
            "Markdown"
        )
        return

    # --- مرحله ۱: اعتبارسنجی (Part One) ---
    prepared_data, error = sajil_part_one.sajil_part_one_validate(raw_input_data)
    
    if error:
        # ارسال پیام خطا به کاربر
        await utils.send_telegram_message(
            chat_id, 
            f"❌ **خطا در اعتبارسنجی داده‌ها:**\n{error}",
            "Markdown"
        )
        return
        
    # --- مرحله ۲: پردازش (Part Two) ---
    processing_results = sajil_part_two.sajil_part_two_process(prepared_data)
    
    # --- مرحله ۳: آماده‌سازی و ارسال گزارش نهایی ---
    
    if processing_results.get("status") == "Success":
        
        report = (
            f"✨ **گزارش نمادشناسی (سجیل) شخصی** ✨\n\n"
            f"**خلاصه تحلیل:** {processing_results['analysis_summary']}\n"
            f"**نماد اصلی پیشنهادی:** {processing_results['generated_symbol']}\n"
            f"**مجموع ارزش‌های ورودی:** {processing_results['total_sum']:.2f}\n"
            f"**میانگین:** {processing_results['average_value']:.2f}\n\n"
            f"**تعداد آیتم‌های پردازش شده:** {processing_results['total_items']}\n"
            f"**زمان گزارش:** {processing_results['report_time']}"
        )
        
        await utils.send_telegram_message(
            chat_id, 
            report, 
            "Markdown", 
            keyboards.services_menu_keyboard() # بازگشت به منوی خدمات
        )
        
    else:
        # خطای داخلی در مرحله پردازش
        await utils.send_telegram_message(
            chat_id, 
            f"❌ **خطای پردازش داخلی:**\n{processing_results.get('message', 'خطای نامشخص در تولید گزارش.')}",
            "Markdown"
        )
