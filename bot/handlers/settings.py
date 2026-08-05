import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from bot.config import MIN_ROUNDS, MAX_ROUNDS, MIN_DURATION, MAX_DURATION
from bot.keyboards.settings import (
    settings_keyboard, categories_keyboard, settings_summary_text,
)
from bot.keyboards.lobby import lobby_keyboard
from bot.utils.messages import build_lobby_text
from core.engine import game_manager

logger = logging.getLogger(__name__)
router = Router(name="settings")


def _get_game_and_settings(callback: CallbackQuery):
    group_id = callback.message.chat.id
    game = game_manager.get_game(group_id)
    if not game:
        return None, None
    return game, game.settings


def _is_host(callback: CallbackQuery, game) -> bool:
    return callback.from_user.id == game.host_id


def _save_settings(user_id: int, settings) -> None:
    """ذخیره تنظیمات در دیتابیس."""
    try:
        from db.database import save_user_settings
        save_user_settings(
            user_id,
            settings.round_duration,
            settings.total_rounds,
            settings.selected_categories,
            settings.hard_letters_enabled,
        )
    except Exception as e:
        logger.warning("Failed to save user settings: %s", e)


# ═══════════════════════════════════════════════════════════
#  باز کردن تنظیمات (جایگزین لابی)
# ═══════════════════════════════════════════════════════════
async def open_settings(callback: CallbackQuery) -> None:
    game, settings = _get_game_and_settings(callback)
    if not game or not _is_host(callback, game):
        return

    try:
        await callback.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=game.lobby_message_id,
            text=settings_summary_text(settings),
            reply_markup=settings_keyboard(settings),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass

    try:
        await callback.answer()
    except TelegramBadRequest:
        pass


# ═══════════════════════════════════════════════════════════
#  اطلاعاتی
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "settings:info")
async def handle_info(callback: CallbackQuery):
    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  تعداد راند
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("settings:rounds:"))
async def handle_rounds(callback: CallbackQuery):
    game, settings = _get_game_and_settings(callback)
    if not game or not _is_host(callback, game):
        await callback.answer("فقط میزبان", show_alert=True)
        return

    delta = int(callback.data.split(":")[-1])
    new_val = settings.total_rounds + delta

    if new_val < MIN_ROUNDS or new_val > MAX_ROUNDS:
        await callback.answer(f"محدوده: {MIN_ROUNDS} تا {MAX_ROUNDS}", show_alert=True)
        return

    settings.total_rounds = new_val
    game.total_rounds = new_val  # هماهنگ‌سازی

    _save_settings(callback.from_user.id, settings)

    try:
        await callback.message.edit_text(
            settings_summary_text(settings),
            reply_markup=settings_keyboard(settings),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass

    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  مدت زمان
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("settings:duration:"))
async def handle_duration(callback: CallbackQuery):
    game, settings = _get_game_and_settings(callback)
    if not game or not _is_host(callback, game):
        await callback.answer("فقط میزبان", show_alert=True)
        return

    delta = int(callback.data.split(":")[-1]) * 5
    new_val = settings.round_duration + delta

    if new_val < MIN_DURATION or new_val > MAX_DURATION:
        await callback.answer(f"محدوده: {MIN_DURATION} تا {MAX_DURATION} ثانیه", show_alert=True)
        return

    settings.round_duration = new_val

    _save_settings(callback.from_user.id, settings)

    try:
        await callback.message.edit_text(
            settings_summary_text(settings),
            reply_markup=settings_keyboard(settings),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass

    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  حروف سخت
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "settings:hard")
async def handle_hard(callback: CallbackQuery):
    game, settings = _get_game_and_settings(callback)
    if not game or not _is_host(callback, game):
        await callback.answer("فقط میزبان", show_alert=True)
        return

    settings.hard_letters_enabled = not settings.hard_letters_enabled

    _save_settings(callback.from_user.id, settings)

    try:
        await callback.message.edit_text(
            settings_summary_text(settings),
            reply_markup=settings_keyboard(settings),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass

    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  باز کردن دسته‌بندی‌ها
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "settings:open_cats")
async def handle_open_cats(callback: CallbackQuery):
    game, settings = _get_game_and_settings(callback)
    if not game or not _is_host(callback, game):
        return

    try:
        await callback.message.edit_text(
            "📂 <b>دسته‌بندی‌ها را انتخاب کنید:</b>",
            reply_markup=categories_keyboard(settings),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass

    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  تغییر دسته‌بندی
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("settings:cat:"))
async def handle_cat_toggle(callback: CallbackQuery):
    game, settings = _get_game_and_settings(callback)
    if not game or not _is_host(callback, game):
        return

    cat = callback.data.split(":")[-1]

    if cat in settings.selected_categories:
        if len(settings.selected_categories) <= 1:
            await callback.answer("حداقل یک دسته باید فعال باشد!", show_alert=True)
            return
        settings.selected_categories.remove(cat)
    else:
        settings.selected_categories.append(cat)

    _save_settings(callback.from_user.id, settings)

    try:
        await callback.message.edit_reply_markup(
            reply_markup=categories_keyboard(settings),
        )
    except TelegramBadRequest:
        pass

    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  بازگشت
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "settings:back")
async def handle_back(callback: CallbackQuery):
    game, settings = _get_game_and_settings(callback)
    if not game:
        return

    current_text = callback.message.text or ""

    if "دسته‌بندی‌ها را انتخاب کنید" in current_text:
        try:
            await callback.message.edit_text(
                settings_summary_text(settings),
                reply_markup=settings_keyboard(settings),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass
    else:
        try:
            await callback.message.edit_text(
                build_lobby_text(game),
                reply_markup=lobby_keyboard(game),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass

    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  ذخیره (برگشت به لابی)
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "settings:save")
async def handle_save(callback: CallbackQuery):
    game, settings = _get_game_and_settings(callback)
    if not game or not _is_host(callback, game):
        await callback.answer()
        return

    _save_settings(callback.from_user.id, settings)

    try:
        await callback.message.edit_text(
            build_lobby_text(game),
            reply_markup=lobby_keyboard(game),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass

    try:
        await callback.answer("✅ تنظیمات ذخیره شد!")
    except TelegramBadRequest:
        pass
