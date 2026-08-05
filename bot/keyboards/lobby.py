from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from core.models import Game


def lobby_keyboard(game: Game) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []

    rows.append([
        InlineKeyboardButton(
            text="🎮 شرکت در بازی",
            callback_data="lobby:join",
            style="success",          # سبز برای اقدام مثبت
        ),
        InlineKeyboardButton(
            text="🚪 انصراف",
            callback_data="lobby:leave",
            style="danger",           # قرمز برای خروج (هشدار)
        ),
    ])

    rows.append([
        InlineKeyboardButton(
            text="🚀 شروع بازی",
            callback_data="lobby:start",
            style="primary",          # آبی برای اقدام اصلی
        ),
        InlineKeyboardButton(
            text="⚙️ تنظیمات",
            callback_data="lobby:settings",
            style="primary",          # آبی برای رفتن به زیرمنو
        ),
    ])

    row3: list[InlineKeyboardButton] = []
    if not game.extended:
        row3.append(
            InlineKeyboardButton(
                text="⏱️ تمدید",
                callback_data="lobby:extend",
                style="success",      # سبز برای تمدید (اقدام مثبت)
            )
        )
    row3.append(
        InlineKeyboardButton(
            text="🚫 لغو بازی",
            callback_data="lobby:cancel",
            style="danger",           # قرمز برای لغو نهایی
        )
    )
    rows.append(row3)

    return InlineKeyboardMarkup(inline_keyboard=rows)


def transfer_keyboard(game: Game) -> InlineKeyboardMarkup:
    """کیبورد انتقال میزبانی — لیست بازیکنان."""
    rows = []
    for p in game.players:
        if p.user_id == game.host_id:
            continue
        name = p.first_name or "ناشناس"
        rows.append([InlineKeyboardButton(
            text=f"👑 انتقال به {name}",
            callback_data=f"lobby:transfer:{p.user_id}",
            style="primary",          # آبی برای اقدام انتقال
        )])
    rows.append([InlineKeyboardButton(
        text="🔙 بازگشت",
        callback_data="lobby:back",
        style="danger",               # قرمز برای خروج از صفحه
    )])
    return InlineKeyboardMarkup(inline_keyboard=rows)