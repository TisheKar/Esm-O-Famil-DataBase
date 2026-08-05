from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from core.models import GameSettings
from bot.config import ALL_CATEGORIES, CATEGORY_ICONS


def settings_keyboard(settings: GameSettings) -> InlineKeyboardMarkup:
    buttons = []

    # ⏱ زمان هر راند
    buttons.append([InlineKeyboardButton(text="⏱ زمان هر راند", callback_data="settings:info")])
    buttons.append([
        InlineKeyboardButton(text="◀️", callback_data="settings:duration:-1", style="primary"),
        InlineKeyboardButton(text=f"{settings.round_duration} ثانیه", callback_data="settings:info"),
        InlineKeyboardButton(text="▶️", callback_data="settings:duration:+1", style="primary"),
    ])

    # 🎯 تعداد راندها
    buttons.append([InlineKeyboardButton(text="🎯 تعداد راندها", callback_data="settings:info")])
    buttons.append([
        InlineKeyboardButton(text="◀️", callback_data="settings:rounds:-1", style="primary"),
        InlineKeyboardButton(text=f"{settings.total_rounds} راند", callback_data="settings:info"),
        InlineKeyboardButton(text="▶️", callback_data="settings:rounds:+1", style="primary"),
    ])

    # 🔤 حروف سخت - رنگ بر اساس وضعیت (سبز=فعال، قرمز=غیرفعال)
    hard_style = "success" if settings.hard_letters_enabled else "danger"
    buttons.append([InlineKeyboardButton(
        text="🔤 حروف سخت",
        callback_data="settings:hard",
        style=hard_style,
    )])

    # 📂 انتخاب دسته‌ها (آبی برای رفتن به زیرمنو)
    active = len(settings.selected_categories)
    total = len(ALL_CATEGORIES)
    buttons.append([InlineKeyboardButton(
        text=f"📂 انتخاب دسته‌ها ({active}/{total})",
        callback_data="settings:open_cats",
        style="primary",
    )])

    # 🔙 بازگشت (قرمز برای خروج)
    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="settings:back", style="danger")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def categories_keyboard(settings: GameSettings) -> InlineKeyboardMarkup:
    buttons = []

    for row_start in range(0, len(ALL_CATEGORIES), 2):
        row = []
        for cat in ALL_CATEGORIES[row_start:row_start + 2]:
            icon = CATEGORY_ICONS.get(cat, "📝")
            is_on = cat in settings.selected_categories
            # حذف 🟢 و ⚫، فقط آیکون + نام دسته با رنگ مناسب
            row.append(InlineKeyboardButton(
                text=f"{icon} {cat}",
                callback_data=f"settings:cat:{cat}",
                style="success" if is_on else None,  # سبز برای فعال، بی‌رنگ برای غیرفعال
            ))
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 بازگشت", callback_data="settings:back", style="danger")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def settings_summary_text(settings: GameSettings) -> str:
    cats_per_line = 4
    cat_lines = []
    cats = settings.selected_categories
    for i in range(0, len(cats), cats_per_line):
        chunk = cats[i:i + cats_per_line]
        cat_lines.append(
            " ".join(f"{CATEGORY_ICONS.get(c, '')}{c}" for c in chunk)
        )
    cats_text = "\n".join(cat_lines)

    if settings.hard_letters_enabled:
        hard_text = "🟢 فعال\n📌 حروف: ث ذ ظ ژ غ"
    else:
        hard_text = "🔴 غیرفعال"

    return (
        "⚙️ <b>تنظیمات بازی</b>\n\n"
        f"⏱ مدت هر راند: <b>{settings.round_duration} ثانیه</b>\n"
        f"🎯 تعداد راندها: <b>{settings.total_rounds} راند</b>\n"
        f"🔤 حروف سخت: <b>{hard_text}</b>\n"
        f"📂 دسته‌ها ({len(cats)}):\n{cats_text}"
    )
