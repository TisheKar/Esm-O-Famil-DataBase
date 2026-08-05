from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def pv_answer_keyboard(
    categories: list[str],
    answers: dict[str, tuple[str, bool]],
) -> InlineKeyboardMarkup:
    """کیبورد انتخاب دسته‌بندی — ۴ تایی (وضعیت با رنگ مشخص می‌شود)."""
    buttons = []

    for row_start in range(0, len(categories), 4):
        row = []
        for cat in categories[row_start:row_start + 4]:
            if cat in answers:
                _, valid = answers[cat]
                # رنگ‌بندی: سبز برای معتبر، قرمز برای نامعتبر
                style = "success" if valid else "danger"
                row.append(InlineKeyboardButton(
                    text=cat,  # فقط نام دسته (بدون ایموجی وضعیت)
                    callback_data=f"pv:ans:{cat}",
                    style=style,
                ))
            else:
                # بدون پاسخ: بی‌رنگ
                row.append(InlineKeyboardButton(
                    text=cat,
                    callback_data=f"pv:ans:{cat}",
                    # بدون style
                ))
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def pv_locked_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    """کیبورد قفل شده — دکمه‌ها غیرفعال (فقط برای نمایش)."""
    buttons = []

    for row_start in range(0, len(categories), 4):
        row = []
        for cat in categories[row_start:row_start + 4]:
            row.append(InlineKeyboardButton(
                text=f"🔒 {cat}",  # ایموجی قفل حفظ می‌شود
                callback_data="pv:locked",
            ))
        buttons.append(row)

    return InlineKeyboardMarkup(inline_keyboard=buttons)