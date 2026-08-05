import time
from bot.config import CATEGORY_ICONS, MAX_PLAYERS
from core.models import Game


def build_lobby_text(game: Game) -> str:
    count = len(game.players)
    lines = [f"🎮 <b>لابی بازی اسم و فامیل</b>\n"]
    for p in game.players:
        name = p.first_name or "ناشناس"
        link = f'<a href="tg://user?id={p.user_id}">{name}</a>'
        if p.user_id == game.host_id:
            lines.append(f"• 👑 {link} <b>(میزبان)</b>")
        else:
            lines.append(f"• {link}")
    lines.append(f"\n💡 حداقل ۲ نفر برای شروع")
    return "\n".join(lines)


def build_lobby_warning() -> str:
    return "⏳ ۳۰ ثانیه دیگه لابی بسته میشه!"


def build_game_started_text(game: Game) -> str:
    lines = ["✅ <b>بازی شروع شد!</b>\n"]
    lines.append(f"👥 <b>بازیکنان</b> ({len(game.players)} نفر):\n")
    for p in game.players:
        name = p.first_name or "ناشناس"
        link = f'<a href="tg://user?id={p.user_id}">{name}</a>'
        if p.user_id == game.host_id:
            lines.append(f"• 👑 {link} <b>(میزبان)</b>")
        else:
            lines.append(f"• {link}")
    lines.append(f"\n🎯 تعداد راند: {game.settings.total_rounds}")
    lines.append("⏳ راند اول به‌زودی آغاز می‌شود...")
    return "\n".join(lines)


def build_cancelled_text() -> str:
    return "🚫 <b>بازی لغو شد.</b>"


def build_no_active_game() -> str:
    return "⚠️ در حال حاضر یک بازی فعال است."


def build_settings_coming_soon() -> str:
    return "⚙️ بخش تنظیمات هنوز فعال نیست. به‌زودی اضافه می‌شود."


def category_label(cat: str) -> str:
    icon = CATEGORY_ICONS.get(cat, "")
    return f"{icon} {cat}"


# ── PV Messages ────────────────────────────────────────────


def _build_progress_bar(
    answers: dict[str, tuple[str, bool]],
    categories: list[str],
) -> str:
    """ساخت نوار پیشرفت — معکوس برای RTL."""
    progress = ""
    for cat in categories:
        if cat in answers:
            _, valid = answers[cat]
            progress += "🟩" if valid else "🟥"
        else:
            progress += "⬜"
    return progress[::-1]


def build_pv_round_text(
    letter: str, round_number: int, total_rounds: int,
    time_left: int, answered_count: int, total_categories: int,
    answers: dict[str, tuple[str, bool]] | None = None,
    categories: list[str] | None = None,
) -> str:
    if answers is not None and categories is not None:
        progress = _build_progress_bar(answers, categories)
        progress_line = f"📊 پاسخ‌ها: {progress} {answered_count}/{total_categories}"
    else:
        progress_line = f"📊 پاسخ‌ها: {answered_count}/{total_categories}"

    return (
        f"🎯 <b>راند {round_number}/{total_rounds}</b>\n\n"
        f"🔤 حرف راند فعلی: <b>{letter}</b>\n"
        f"{progress_line}\n"
        f"⏰ {time_left} ثانیه باقی‌مانده"
    )


def build_pv_round_summary(
    letter: str, round_number: int, total_rounds: int,
    answers: dict[str, tuple[str, bool]],
    categories: list[str],
) -> str:
    """گزارش خلاصه راند در پیوی — بعد از پایان راند."""
    progress = _build_progress_bar(answers, categories)
    lines = [
        f"⏰ <b>راند {round_number}/{total_rounds} تمام شد!</b>\n",
        f"🔤 حرف: <b>{letter}</b>\n",
        f"📊 پاسخ‌ها: {progress} {len(answers)}/{len(categories)}\n",
    ]
    for cat in categories:
        if cat in answers:
            text, valid = answers[cat]
            icon = "✅" if valid else "⚠️"
            lines.append(f"  {icon} {cat}: {text}")
        else:
            lines.append(f"  ⬜ {cat}: —")
    return "\n".join(lines)


# ── Group Messages ─────────────────────────────────────────


def _player_link(game, p) -> str:
    name = p.first_name or "ناشناس"
    link = f'<a href="tg://user?id={p.user_id}">{name}</a>'
    if p.user_id == game.host_id:
        return f"👑 {link}"
    return link


def _player_lines(game: Game) -> list[str]:
    return [_player_link(game, p) for p in game.players]


def _past_letters_text(game: Game) -> list[str]:
    lines = []
    ordinal = ["اول", "دوم", "سوم", "چهارم", "پنجم", "ششم", "هفتم", "هشتم"]
    past = game.used_letters[:-1] if game.used_letters else []
    if past:
        for i, l in enumerate(past):
            if i < len(ordinal):
                lines.append(f"🔤 حرف راند {ordinal[i]}: {l}")
    return lines


def build_round_message(
    game: Game, letter: str, round_number: int, total_rounds: int,
    duration: int,
) -> str:
    lines = [f"🎯 <b>راند {round_number}/{total_rounds}</b>\n"]
    lines.append("👥 <b>بازیکنان:</b>")
    for pl in _player_lines(game):
        lines.append(f"• {pl}")
    lines.append("")
    lines.extend(_past_letters_text(game))
    lines.append("")
    lines.append(f"🔤 <b>حرف راند فعلی: {letter}</b>")
    lines.append(f"⏰ زمان: {duration} ثانیه")
    lines.append("\n💬 پاسخ‌ها رو توی پیوی بفرستید!")
    return "\n".join(lines)


def build_round_results_message(
    game: Game, results: list[dict], round_number: int,
    total_rounds: int, used_letters: list[str],
) -> str:
    lines = [f"📊 <b>نتایج راند {round_number}/{total_rounds}</b>\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(results):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = r["name"]
        uid = r.get("user_id")
        if uid:
            link = f'<a href="tg://user?id={uid}">{name}</a>'
            lines.append(f"{medal} {link} — {r['score']} امتیاز")
        else:
            lines.append(f"{medal} {name} — {r['score']} امتیاز")

    if used_letters:
        lines.append("")
        ordinal = ["اول", "دوم", "سوم", "چهارم", "پنجم", "ششم", "هفتم", "هشتم"]
        for i, l in enumerate(used_letters):
            if i < len(ordinal):
                lines.append(f"🔤 حرف راند {ordinal[i]}: {l}")

    return "\n".join(lines)


def build_final_results_text(results: list[dict], used_letters: list[str] = None) -> str:
    lines = ["🏆 <b>نتایج نهایی بازی</b>\n"]
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(results):
        medal = medals[i] if i < 3 else f"{i+1}."
        name = r["name"]
        uid = r.get("user_id")
        if uid:
            link = f'<a href="tg://user?id={uid}">{name}</a>'
            lines.append(f"{medal} {link} — <b>{r['total']}</b> امتیاز")
        else:
            lines.append(f"{medal} {name} — <b>{r['total']}</b> امتیاز")

    # نمایش حروف راندها
    if used_letters:
        lines.append("")
        ordinal = ["اول", "دوم", "سوم", "چهارم", "پنجم", "ششم", "هفتم", "هشتم"]
        lines.append("📝 حروف راندها:")
        for i, l in enumerate(used_letters):
            if i < len(ordinal):
                lines.append(f"  • راند {ordinal[i]}: <b>{l}</b>")

    return "\n".join(lines)


def build_round_end_text() -> str:
    return "⏰ <b>زمان تمام شد!</b>"
