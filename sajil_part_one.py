def sajil_part_one_validate(input_list: list) -> tuple[list[float], str | None]:
    """
    وظیفه: اعتبارسنجی و تبدیل لیست ورودی به اعداد ممیز شناور (Float).

    خروجی: (لیست داده‌های تمیز شده, پیام خطا (در صورت وجود))
    """
    # print("--- [بخش یک]: شروع فرآیند اعتبارسنجی داده‌ها ---") # حذف پرینت در ماژول اصلی
    clean_data = []
    
    # 1. بررسی خالی نبودن ورودی
    if not input_list:
        return [], "خطا: لیست ورودی نمی‌تواند خالی باشد."

    # 2. اعتبارسنجی و تبدیل نوع داده
    for index, item in enumerate(input_list):
        try:
            # تلاش برای تبدیل هر آیتم به عدد ممیز شناور
            float_item = float(item)
            clean_data.append(float_item)
        except (ValueError, TypeError):
            error_msg = f"خطا: داده نامعتبر در شاخص {index}. مقدار: '{item}'. تمام ورودی‌ها باید عدد باشند."
            return [], error_msg
            
    # print(f"--- [بخش یک]: با موفقیت {len(clean_data)} داده اعتبارسنجی و آماده شد. ---") # حذف پرینت
    return clean_data, None
