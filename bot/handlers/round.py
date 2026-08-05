import asyncio
import time
import logging

from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.config import TIMER_INTERVALS
from bot.utils.normalize import normalize
from bot.utils.messages import (
    build_round_message,
    build_pv_round_text,
    build_pv_round_summary,
    build_round_results_message,
    build_final_results_text,
)
from bot.keyboards.pv import pv_answer_keyboard, pv_locked_keyboard
from core.engine import game_manager
from core.scoring import score_answers, apply_first_complete_bonus
from db.words import is_valid_word

logger = logging.getLogger(__name__)
router = Router(name="round")


class PvState(StatesGroup):
    waiting_answer = State()


def _build_answers_dict(group_id: int, player_id: int) -> dict[str, tuple[str, bool]]:
    pa = game_manager.get_player_answers(group_id, player_id)
    return {cat: (a.display_text, a.is_valid) for cat, a in pa.items()}


# ═══════════════════════════════════════════════════════════
#  helper: ارسال پیام جدید در گروه
# ═══════════════════════════════════════════════════════════
async def _send_round_message(bot: Bot, group_id: int, game, text: str) -> None:
    if game.status_message_id:
        try:
            await bot.unpin_chat_message(chat_id=group_id, message_id=game.status_message_id)
        except TelegramBadRequest:
            pass
        try:
            await bot.delete_message(group_id, game.status_message_id)
        except TelegramBadRequest:
            pass
        game.status_message_id = None

    try:
        msg = await bot.send_message(group_id, text, parse_mode="HTML")
        game.status_message_id = msg.message_id
    except TelegramBadRequest:
        return

    try:
        await bot.pin_chat_message(
            chat_id=group_id,
            message_id=game.status_message_id,
            disable_notification=True,
        )
    except TelegramBadRequest:
        pass


async def _edit_status(bot: Bot, group_id: int, game, text: str) -> None:
    if not game.status_message_id:
        try:
            msg = await bot.send_message(group_id, text, parse_mode="HTML")
            game.status_message_id = msg.message_id
        except TelegramBadRequest:
            pass
        return
    try:
        await bot.edit_message_text(
            chat_id=group_id,
            message_id=game.status_message_id,
            text=text,
            parse_mode="HTML",
        )
    except TelegramBadRequest:
        pass


# ═══════════════════════════════════════════════════════════
#  helper: پاک کردن state بازیکن
# ═══════════════════════════════════════════════════════════
async def _clear_player_states(bot: Bot, group_id: int) -> None:
    """پاک کردن state FSM همه بازیکنان یه گروه."""
    game = game_manager.get_game(group_id)
    if not game:
        return
    dp = bot.get("dispatcher")
    if not dp:
        return
    for player in game.players:
        try:
            state = dp.fsm.storage  # MemoryStorage
            # ساخت کلید FSM برای aiogram
            key = str(player.user_id)
            if hasattr(state, 'storage') and hasattr(state.storage, '_data'):
                state.storage._data.pop(key, None)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════
#  helper: شروع راند
# ═══════════════════════════════════════════════════════════
async def start_next_round(bot: Bot, group_id: int) -> None:
    result = game_manager.start_round(group_id)
    if not result:
        return

    round_obj = result
    game = game_manager.get_game(group_id)
    if not game:
        return

    await _send_round_message(bot, group_id, game, build_round_message(
        game, round_obj.letter, round_obj.round_number,
        game.total_rounds, game.settings.round_duration,
    ))

    for player in game.players:
        try:
            old_msg = game.pv_message_ids.get(player.user_id)
            if old_msg:
                try:
                    await bot.delete_message(player.user_id, old_msg)
                except TelegramBadRequest:
                    pass

            msg = await bot.send_message(
                player.user_id,
                build_pv_round_text(
                    round_obj.letter, round_obj.round_number,
                    game.total_rounds, game.settings.round_duration,
                    0, len(game.settings.selected_categories),
                    answers={},
                    categories=game.settings.selected_categories,
                ),
                reply_markup=pv_answer_keyboard(
                    game.settings.selected_categories, {},
                ),
                parse_mode="HTML",
            )
            game.pv_message_ids[player.user_id] = msg.message_id
        except TelegramBadRequest:
            logger.warning("Could not send PV to %s", player.user_id)

    # ذخیره reference تایمر
    task = asyncio.create_task(_round_timer(bot, group_id, game.settings.round_duration))
    game_manager.save_round_task(group_id, task)


# ═══════════════════════════════════════════════════════════
#  helper: تایمر راند
# ═══════════════════════════════════════════════════════════
async def _round_timer(bot: Bot, group_id: int, duration: int) -> None:
    game = game_manager.get_game(group_id)
    if not game or not game.current_round:
        return

    n = len(game.players)
    if n > 15:
        interval = TIMER_INTERVALS["slow"]
    elif n < 5:
        interval = TIMER_INTERVALS["fast"]
    else:
        interval = TIMER_INTERVALS["normal"]

    elapsed = 0
    while elapsed < duration:
        sleep_time = min(interval, duration - elapsed)
        await asyncio.sleep(sleep_time)
        elapsed += sleep_time
        time_left = max(0, duration - elapsed)

        # بررسی اینکه بازی هنوز فعاله
        game = game_manager.get_game(group_id)
        if not game or not game.current_round or game.current_round.status != "active":
            return

        for player in game.players:
            msg_id = game.pv_message_ids.get(player.user_id)
            if not msg_id:
                continue
            answers_dict = _build_answers_dict(group_id, player.user_id)
            try:
                await bot.edit_message_text(
                    chat_id=player.user_id,
                    message_id=msg_id,
                    text=build_pv_round_text(
                        game.current_round.letter,
                        game.current_round.round_number,
                        game.total_rounds, time_left,
                        len(answers_dict), len(game.settings.selected_categories),
                        answers=answers_dict,
                        categories=game.settings.selected_categories,
                    ),
                    reply_markup=pv_answer_keyboard(
                        game.settings.selected_categories, answers_dict,
                    ),
                    parse_mode="HTML",
                )
            except TelegramBadRequest:
                pass

        if game.status_message_id:
            try:
                await bot.edit_message_text(
                    chat_id=group_id,
                    message_id=game.status_message_id,
                    text=build_round_message(
                        game, game.current_round.letter,
                        game.current_round.round_number,
                        game.total_rounds, time_left,
                    ),
                    parse_mode="HTML",
                )
            except TelegramBadRequest:
                pass

    await _finish_round(bot, group_id)


# ═══════════════════════════════════════════════════════════
#  helper: پایان راند
# ═══════════════════════════════════════════════════════════
async def _finish_round(bot: Bot, group_id: int) -> None:
    game = game_manager.end_round(group_id)
    if not game or not game.current_round:
        return

    round_number = game.current_round.round_number

    # پاک کردن state همه بازیکنان
    await _clear_player_states(bot, group_id)

    # پیوی: ویرایش گزارش خلاصه + قفل کیبورد
    for player in game.players:
        msg_id = game.pv_message_ids.get(player.user_id)
        if not msg_id:
            continue
        answers_dict = _build_answers_dict(group_id, player.user_id)
        try:
            await bot.edit_message_text(
                chat_id=player.user_id,
                message_id=msg_id,
                text=build_pv_round_summary(
                    game.current_round.letter,
                    round_number,
                    game.total_rounds,
                    answers_dict,
                    game.settings.selected_categories,
                ),
                reply_markup=pv_locked_keyboard(game.settings.selected_categories),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass

    # محاسبه امتیاز
    answers = game_manager.get_round_answers(group_id)
    round_scores = score_answers(answers)
    apply_first_complete_bonus(
        round_scores, answers, game.settings.selected_categories,
    )
    for pid, pts in round_scores.items():
        game.round_scores[pid] = game.round_scores.get(pid, 0) + pts

    results = []
    for p in game.players:
        results.append({
            "name": p.first_name or "ناشناس",
            "user_id": p.user_id,
            "score": round_scores.get(p.user_id, 0),
        })
    results.sort(key=lambda x: x["score"], reverse=True)

    game_manager.clear_round(group_id)

    if game.current_round_index >= game.total_rounds:
        await _end_game(bot, group_id)
        return

    await _edit_status(bot, group_id, game, build_round_results_message(
        game, results, round_number, game.total_rounds, game.used_letters,
    ))

    await asyncio.sleep(5)
    await start_next_round(bot, group_id)


# ═══════════════════════════════════════════════════════════
#  helper: پایان بازی
# ═══════════════════════════════════════════════════════════
async def _end_game(bot: Bot, group_id: int) -> None:
    game = game_manager.get_game(group_id)
    if not game:
        return

    if game.status_message_id:
        try:
            await bot.unpin_chat_message(chat_id=group_id, message_id=game.status_message_id)
        except TelegramBadRequest:
            pass

    results = []
    for p in game.players:
        results.append({
            "name": p.first_name or "ناشناس",
            "user_id": p.user_id,
            "total": game.round_scores.get(p.user_id, 0),
        })
    results.sort(key=lambda x: x["total"], reverse=True)

    # ← اضافه شد: حروف راندها توی نتایج نهایی
    await _edit_status(bot, group_id, game, build_final_results_text(results, game.used_letters))

    for player in game.players:
        msg_id = game.pv_message_ids.get(player.user_id)
        if msg_id:
            try:
                await bot.delete_message(player.user_id, msg_id)
            except TelegramBadRequest:
                pass

    game_manager.delete_game(group_id)
    logger.info("Game ended in group %s", group_id)


# ═══════════════════════════════════════════════════════════
#  PV: کلیک کیبورد قفل شده
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data == "pv:locked")
async def handle_locked(callback: CallbackQuery):
    try:
        await callback.answer("⏰ زمان راند تمام شده!", show_alert=True)
    except TelegramBadRequest:
        pass


# ═══════════════════════════════════════════════════════════
#  PV: انتخاب دسته‌بندی
# ═══════════════════════════════════════════════════════════
@router.callback_query(F.data.startswith("pv:ans:"))
async def handle_category_click(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    category = callback.data.split(":")[-1]

    game = game_manager.get_game_by_player(user_id)
    if not game or not game.current_round or game.current_round.status != "active":
        try:
            await callback.answer("⏰ راند تمام شده است.", show_alert=True)
        except TelegramBadRequest:
            pass
        await state.clear()
        return

    # حذف پیام قبلی "📝 ... بنویس" اگر مونده
    old_data = await state.get_data()
    old_prompt_id = old_data.get("prompt_msg_id")
    if old_prompt_id:
        try:
            await callback.bot.delete_message(user_id, old_prompt_id)
        except TelegramBadRequest:
            pass

    await state.clear()
    await state.update_data(
        game_group_id=game.group_id,
        current_category=category,
    )
    await state.set_state(PvState.waiting_answer)

    letter = game.current_round.letter

    try:
        prompt_msg = await callback.message.answer(
            f"📝 <b>{category}</b> رو با حرف «<b>{letter}</b>» بنویس:"
        )
        await state.update_data(prompt_msg_id=prompt_msg.message_id)
    except TelegramBadRequest:
        pass

    try:
        await callback.answer()
    except TelegramBadRequest:
        pass


# ═══════════════════════════════════════════════════════════
#  PV: دریافت پاسخ
# ═══════════════════════════════════════════════════════════
@router.message(PvState.waiting_answer)
async def handle_answer(message: Message, state: FSMContext):
    if message.chat.type != "private":
        return

    user_id = message.from_user.id
    data = await state.get_data()
    group_id = data.get("game_group_id")
    category = data.get("current_category")
    prompt_msg_id = data.get("prompt_msg_id")

    if not group_id or not category:
        await message.answer("❌ خطا! دوباره روی دکمه بزن.")
        await state.clear()
        return

    game = game_manager.get_game(group_id)
    if not game or not game.current_round or game.current_round.status != "active":
        await message.answer("⏰ راند تمام شده است!")
        await state.clear()
        return

    # بررسی جواب تکراری
    existing = game_manager.get_player_answers(group_id, user_id)
    if category in existing:
        old_text = existing[category].display_text
        await message.answer(
            f"⚠️ قبلاً برای «{category}» جواب دادی: <b>{old_text}</b>\n"
            "اگر میخوای عوضش کنی، اول این جواب رو پاک کن.",
        )
        try:
            await message.delete()
        except Exception:
            pass
        await state.clear()
        return

    display_text = message.text.strip()
    normalized = normalize(display_text)
    letter = game.current_round.letter
    starts_with_letter = normalized.startswith(letter)
    valid = is_valid_word(category, normalized) and starts_with_letter

    game_manager.submit_answer(
        group_id, user_id, category, display_text, normalized, valid,
    )

    # حذف پیام تایپ شده کاربر
    try:
        await message.delete()
    except TelegramBadRequest:
        pass

    # حذف پیام "📝 ... بنویس"
    if prompt_msg_id:
        try:
            await message.bot.delete_message(user_id, prompt_msg_id)
        except TelegramBadRequest:
            pass

    # آپدیت کیبورد + گزارش اصلی
    answers_dict = _build_answers_dict(group_id, user_id)
    elapsed = time.time() - game.current_round.start_time
    time_left = max(0, int(game.settings.round_duration - elapsed))

    msg_id = game.pv_message_ids.get(user_id)
    if msg_id:
        try:
            await message.bot.edit_message_text(
                chat_id=user_id,
                message_id=msg_id,
                text=build_pv_round_text(
                    game.current_round.letter,
                    game.current_round.round_number,
                    game.total_rounds, time_left,
                    len(answers_dict), len(game.settings.selected_categories),
                    answers=answers_dict,
                    categories=game.settings.selected_categories,
                ),
                reply_markup=pv_answer_keyboard(
                    game.settings.selected_categories, answers_dict,
                ),
                parse_mode="HTML",
            )
        except TelegramBadRequest:
            pass

    await state.clear()
