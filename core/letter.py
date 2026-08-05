import random
from bot.config import ACTIVE_LETTERS, HARD_LETTERS, COMMON_LETTERS


def select_letter(
    used_letters: list[str],
    hard_enabled: bool = False,
    total_rounds: int = 3,
    rounds_left: int = 1,
) -> str:
    """
    انتخاب حرف تصادفی با اولویت حروف پرکاربرد.
    اگر حروف سخت فعال باشه، حداقل راند//3 حرف سخت تضمین میشه.
    """
    hard_needed = total_rounds // 3
    hard_used = sum(1 for l in used_letters if l in HARD_LETTERS)
    hard_still_needed = max(0, hard_needed - hard_used)

    available_hard = [l for l in HARD_LETTERS if l not in used_letters]
    available_normal = [l for l in ACTIVE_LETTERS if l not in used_letters]

    # ── اگر حروف سخت فعاله ──
    if hard_enabled and available_hard:
        if hard_still_needed >= rounds_left:
            return random.choice(available_hard)

        available = available_normal + available_hard
    else:
        available = available_normal if available_normal else list(ACTIVE_LETTERS)

    # اگر لیست خالی بود (تمام حروف استفاده شده)
    if not available:
        available = list(ACTIVE_LETTERS)

    weighted = []
    for letter in available:
        if letter in COMMON_LETTERS:
            weight = 3
        elif hard_enabled and letter in HARD_LETTERS:
            weight = 2
        else:
            weight = 1
        weighted.extend([letter] * weight)

    return random.choice(weighted) if weighted else random.choice(list(ACTIVE_LETTERS))
