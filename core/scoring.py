from core.models import Answer
from bot.config import (
    SCORE_UNIQUE, SCORE_DUPLICATE_2, SCORE_DUPLICATE_3,
    SCORE_DUPLICATE_4_PLUS, SCORE_FIRST_COMPLETE_BONUS,
)


def score_answers(answers: list[Answer]) -> dict[int, int]:
    """محاسبه امتیاز هر بازیکن. فقط پاسخ‌های معتبر امتیاز می‌گیرن."""
    answers = [a for a in answers if a.is_valid]
    scores: dict[int, int] = {}

    by_category: dict[str, list[Answer]] = {}
    for a in answers:
        by_category.setdefault(a.category, []).append(a)

    for cat_answers in by_category.values():
        by_text: dict[str, list[Answer]] = {}
        for a in cat_answers:
            by_text.setdefault(a.normalized_text, []).append(a)

        for text_answers in by_text.values():
            count = len(text_answers)
            if count == 1:
                pts = SCORE_UNIQUE
            elif count == 2:
                pts = SCORE_DUPLICATE_2
            elif count == 3:
                pts = SCORE_DUPLICATE_3
            else:
                pts = SCORE_DUPLICATE_4_PLUS

            for a in text_answers:
                scores[a.player_id] = scores.get(a.player_id, 0) + pts

    return scores


def apply_first_complete_bonus(
    scores: dict[int, int],
    answers: list[Answer],
    categories: list[str],
) -> int | None:
    """اگر کسی اول تموم کرده باشه، بونوس بگیره — بر اساس زمان واقعی."""
    answers = [a for a in answers if a.is_valid]
    cat_set = set(categories)

    # گروه‌بندی: player_id → {category: submitted_at}
    by_player: dict[int, dict[str, float]] = {}
    for a in answers:
        by_player.setdefault(a.player_id, {})[a.category] = a.submitted_at or 0

    first_pid = None
    first_time = float("inf")

    for pid, cat_times in by_player.items():
        if set(cat_times.keys()) >= cat_set:
            # زمان آخرین پاسخ = زمان تموم کردن
            finish_time = max(cat_times.values())
            if finish_time < first_time:
                first_time = finish_time
                first_pid = pid

    if first_pid is not None:
        scores[first_pid] = scores.get(first_pid, 0) + SCORE_FIRST_COMPLETE_BONUS
    return first_pid
