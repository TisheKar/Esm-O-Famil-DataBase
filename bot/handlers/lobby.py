import asyncio
import logging

from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery, ReactionTypeEmoji,
)
from aiogram.exceptions import TelegramBadRequest

from bot.config import (
    MIN_PLAYERS,
    LOBBY_TIMEOUT, LOBBY_WARNING_AT, LOBBY_EXTEND_SECONDS,
)
from bot.utils.messages import (
    build_lobby_text, build_lobby_warning,
    build_cancelled_text,
    build_no_active_game,
)
from bot.utils.scheduler import LobbyScheduler
from bot.keyboards.lobby import lobby_keyboard, transfer_keyboard
from core.engine import game_manager
from core.models import Player

logger = logging.getLogger(__name__)
router = Router(name="lobby")
scheduler = LobbyScheduler()


# ─── helper: بروزرسانی پیام لابی ───────────────────────────
async def _refresh_lobby(bot, group_id: int) -> None:
    game = game_manager.get_game(group_id)
    if not game or not game.lobby_message_id:
        return
    try:
        await bot.edit_message_text(
            chat_id=group_id,
            message_id=game.lobby_message_id,
            text=build_lobby_text(game),
            reply_markup=lobby_keyboard(game),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass


# ─── helper: پاک‌سازی لابی ─────────────────────────────────
async def _cleanup_lobby(bot, group_id: int, delete_msg: bool = True) -> None:
    game = game_manager.get_game(group_id)
    if not game:
        return
    scheduler.cancel(game.id)
    if game.lobby_message_id:
        try:
            await bot.unpin_chat_message(chat_id=group_id, message_id=game.lobby_message_id)
        except TelegramBadRequest:
            pass
        if delete_msg:
            try:
                await bot.delete_message(group_id, game.lobby_message_id)
            except TelegramBadRequest:
                pass
    game_manager.delete_game(group_id)


# ─── helper: لود تنظیمات ذخیره‌شده کاربر ───────────────────
def _load_saved_settings(host_id: int, game) -> None:
    """تنظیمات ذخیره‌شده کاربر رو روی بازی اعمال کن."""
    try:
        from db.database import load_user_settings
        saved = load_user_settings(host_id)
        if saved:
            game.settings.total_rounds = saved["total_rounds"]
            game.settings.round_duration = saved["round_duration"]
            game.settings.selected_categories = saved["selected_categories"]
            game.settings.hard_letters_enabled = saved["hard_letters_enabled"]
            game.total_rounds = saved["total_rounds"]
    except Exception as e:
        logger.warning("Failed to load user settings: %s", e)


# ═══════════════════════════════════════════════════════════
#  1) شروع بازی — تشخیص دستورات متنی
# ═══════════════════════════════════════════════════════════
_START_KEYWORDS = {
    "اسم فامیل", "اسم و فامیل",
    "بازی اسم و فامیل", "بازی اسم فامیل",
}


@router.message(F.text, F.chat.type.in_({"group", "supergroup"}))
async def handle_text(message: Message):
    text = (message.text or "").strip()
    if text not in _START_KEYWORDS:
        return

    group_id = message.chat.id
    bot = message.bot

    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    if game_manager.is_active(group_id):
        temp = await message.answer(build_no_active_game())
        await asyncio.sleep(2)
        try:
            await temp.delete()
        except TelegramBadRequest:
            pass
        return

    host = Player(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name or "ناشناس",
    )
    game = game_manager.create_game(group_id, host)

    # لود تنظیمات ذخیره‌شده
    _load_saved_settings(message.from_user.id, game)

    game.lobby_message_id = (await message.answer(
        text=build_lobby_text(game),
        reply_markup=lobby_keyboard(game),
        parse_mode="HTML",
    )).message_id

    try:
        await bot.pin_chat_message(
            chat_id=group_id,
            message_id=game.lobby_message_id,
            disable_notification=True,
        )
    except TelegramBadRequest:
        pass

    try:
        from aiogram.methods import SetMessageReaction
        await bot(SetMessageReaction(
            chat_id=group_id,
            message_id=message.message_id,
            reaction=[ReactionTypeEmoji(emoji="🎯")],
        ))
    except Exception:
        pass

    async def _on_warning():
        g = game_manager.get_game(group_id)
        if not g or g.status != "lobby":
            return
        try:
            await bot.send_message(group_id, build_lobby_warning())
        except TelegramBadRequest:
            pass

    async def _on_expire():
        g = game_manager.get_game(group_id)
        if not g or g.status != "lobby":
            return
        if len(g.players) < MIN_PLAYERS:
            await _cleanup_lobby(bot, group_id)

    await scheduler.start(
        game.id, LOBBY_TIMEOUT, LOBBY_WARNING_AT, _on_warning, _on_expire
    )


# ═══════════════════════════════════════════════════════════
#  2) Join
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "lobby:join")
async def handle_join(callback: CallbackQuery):
    group_id = callback.message.chat.id
    player = Player(
        user_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name or "ناشناس",
    )
    ok, msg = game_manager.add_player(group_id, player)

    if ok:
        await callback.answer("✅ شما به لابی پیوستید!", show_alert=False)
        await _refresh_lobby(callback.bot, group_id)
    else:
        await callback.answer(msg, show_alert=True)


# ═══════════════════════════════════════════════════════════
#  3) Leave
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "lobby:leave")
async def handle_leave(callback: CallbackQuery):
    group_id = callback.message.chat.id
    user_id = callback.from_user.id
    game = game_manager.get_game(group_id)

    # اگه میزبان Leave زد و بازیکن دیگه هست، خودکار انتقال بده
    if game and game.host_id == user_id and len(game.players) > 1:
        game.players = [p for p in game.players if p.user_id != user_id]
        game.host_id = game.players[0].user_id
        new_name = game.players[0].first_name or "ناشناس"
        try:
            await callback.bot.send_message(
                group_id,
                f"👑 میزبانی به <b>{new_name}</b> منتقل شد.",
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass
        await _refresh_lobby(callback.bot, group_id)
        await callback.answer("🚪 خارج شدید و میزبانی منتقل شد.", show_alert=False)
        return

    ok, msg = game_manager.remove_player(group_id, user_id)

    if ok:
        await callback.answer("🚪 شما از لابی خارج شدید.", show_alert=False)
        await _refresh_lobby(callback.bot, group_id)
    else:
        await callback.answer(msg, show_alert=True)


# ═══════════════════════════════════════════════════════════
#  4) Start
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "lobby:start")
async def handle_start(callback: CallbackQuery):
    group_id = callback.message.chat.id
    game = game_manager.get_game(group_id)

    if not game:
        await callback.answer("بازی یافت نشد.", show_alert=True)
        return

    if callback.from_user.id != game.host_id:
        await callback.answer("فقط میزبان می‌تواند بازی را شروع کند.", show_alert=True)
        return

    ok, msg = game_manager.can_start(group_id)
    if not ok:
        await callback.answer(msg, show_alert=True)
        return

    scheduler.cancel(game.id)
    game_manager.start_game(group_id)

    try:
        await callback.bot.unpin_chat_message(chat_id=group_id, message_id=game.lobby_message_id)
    except TelegramBadRequest:
        pass
    try:
        await callback.bot.delete_message(group_id, game.lobby_message_id)
    except TelegramBadRequest:
        pass

    await callback.answer("🚀 بازی شروع شد!")
    logger.info("Game started in group %s with %d players", group_id, len(game.players))

    from bot.handlers.round import start_next_round
    await start_next_round(callback.bot, group_id)


# ═══════════════════════════════════════════════════════════
#  5) Cancel
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "lobby:cancel")
async def handle_cancel(callback: CallbackQuery):
    group_id = callback.message.chat.id
    game = game_manager.get_game(group_id)

    if not game:
        await callback.answer("بازی یافت نشد.", show_alert=True)
        return

    is_host = callback.from_user.id == game.host_id
    member = await callback.bot.get_chat_member(group_id, callback.from_user.id)
    is_admin = member.status in ("creator", "administrator")

    if not is_host and not is_admin:
        await callback.answer("فقط میزبان یا مدیران گروه می‌توانند لغو کنند.", show_alert=True)
        return

    await _cleanup_lobby(callback.bot, group_id, delete_msg=True)

    try:
        cancel_msg = await callback.bot.send_message(
            group_id, build_cancelled_text(), parse_mode="HTML"
        )
        await callback.answer("🚫 بازی لغو شد.")

        # حذف ساده بعد از ۱۰ ثانیه
        await asyncio.sleep(10)
        try:
            await callback.bot.delete_message(group_id, cancel_msg.message_id)
        except TelegramBadRequest:
            pass

    except TelegramBadRequest:
        pass


# ═══════════════════════════════════════════════════════════
#  6) Extend
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "lobby:extend")
async def handle_extend(callback: CallbackQuery):
    group_id = callback.message.chat.id
    game = game_manager.get_game(group_id)

    if not game:
        await callback.answer("بازی یافت نشد.", show_alert=True)
        return

    if callback.from_user.id != game.host_id:
        await callback.answer("فقط میزبان می‌تواند زمان را تمدید کند.", show_alert=True)
        return

    if game.extended:
        await callback.answer("شما قبلاً تمدید کرده‌اید.", show_alert=True)
        return

    game.extended = True
    scheduler.cancel(game.id)
    bot = callback.bot

    async def _on_warning():
        g = game_manager.get_game(group_id)
        if not g or g.status != "lobby":
            return
        try:
            await bot.send_message(group_id, build_lobby_warning())
        except TelegramBadRequest:
            pass

    async def _on_expire():
        g = game_manager.get_game(group_id)
        if not g or g.status != "lobby":
            return
        if len(g.players) < MIN_PLAYERS:
            await _cleanup_lobby(bot, group_id)

    await scheduler.start(
        game.id, LOBBY_EXTEND_SECONDS, LOBBY_EXTEND_SECONDS - 30,
        _on_warning, _on_expire,
    )

    await callback.answer("⏱️ ۲ دقیقه اضافه شد!", show_alert=False)
    await _refresh_lobby(callback.bot, group_id)


# ═══════════════════════════════════════════════════════════
#  7) Settings
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "lobby:settings")
async def handle_settings(callback: CallbackQuery):
    from bot.handlers.settings import open_settings
    await open_settings(callback)


# ═══════════════════════════════════════════════════════════
#  8) Transfer — شروع
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "lobby:transfer")
async def handle_transfer_start(callback: CallbackQuery):
    group_id = callback.message.chat.id
    game = game_manager.get_game(group_id)

    if not game:
        await callback.answer("بازی یافت نشد.", show_alert=True)
        return

    is_host = callback.from_user.id == game.host_id
    member = await callback.bot.get_chat_member(group_id, callback.from_user.id)
    is_admin = member.status in ("creator", "administrator")

    if not is_host and not is_admin:
        await callback.answer("فقط میزبان یا مدیران گروه.", show_alert=True)
        return

    if len(game.players) < 2:
        await callback.answer("بازیکن دیگه‌ای نیست!", show_alert=True)
        return

    try:
        await callback.message.edit_text(
            "👑 <b>چه کسی میزبان بشه؟</b>",
            reply_markup=transfer_keyboard(game),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass

    await callback.answer()


# ═══════════════════════════════════════════════════════════
#  9) Transfer — اجرا
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("lobby:transfer:"))
async def handle_transfer_do(callback: CallbackQuery):
    group_id = callback.message.chat.id
    game = game_manager.get_game(group_id)

    if not game:
        await callback.answer("بازی یافت نشد.", show_alert=True)
        return

    is_host = callback.from_user.id == game.host_id
    member = await callback.bot.get_chat_member(group_id, callback.from_user.id)
    is_admin = member.status in ("creator", "administrator")

    if not is_host and not is_admin:
        await callback.answer("فقط میزبان یا مدیران گروه.", show_alert=True)
        return

    new_host_id = int(callback.data.split(":")[-1])
    new_host = next((p for p in game.players if p.user_id == new_host_id), None)

    if not new_host:
        await callback.answer("بازیکن یافت نشد.", show_alert=True)
        return

    game.host_id = new_host_id
    new_name = new_host.first_name or "ناشناس"

    try:
        await callback.message.edit_text(
            build_lobby_text(game),
            reply_markup=lobby_keyboard(game),
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass

    try:
        await callback.answer(f"👑 میزبانی به {new_name} منتقل شد!")
    except TelegramBadRequest:
        pass


# ═══════════════════════════════════════════════════════════
#  10) Back — برگشت از صفحه انتقال به لابی
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "lobby:back")
async def handle_back(callback: CallbackQuery):
    group_id = callback.message.chat.id
    game = game_manager.get_game(group_id)

    if not game:
        return

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
#  11) پاک کردن پیام سرویسی پین
# ═══════════════════════════════════════════════════════════
@router.message(F.pinned_message)
async def handle_pinned_service_message(message: Message):
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
