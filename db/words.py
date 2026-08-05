import logging
import aiohttp
from db.database import get_conn

logger = logging.getLogger(__name__)


async def download_words_async() -> int:
    """دانلود کلمات از گیتهاب با aiohttp (غیرهمزمان)."""
    from bot.config import WORDS_GITHUB_BASE_URL, FILE_CATEGORY_MAP

    total = 0
    async with aiohttp.ClientSession() as session:
        for filename, category in FILE_CATEGORY_MAP.items():
            url = f"{WORDS_GITHUB_BASE_URL}/{filename}"
            try:
                logger.info("Downloading: %s → %s", filename, category)
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status != 200:
                        logger.error("HTTP %d for %s", resp.status, filename)
                        continue
                    raw = await resp.text()
                words = raw.split()
                loaded = _insert_words(category, words)
                total += loaded
                logger.info("  ↳ %d words loaded for '%s'", loaded, category)
            except Exception as e:
                logger.error("Failed to download %s: %s", filename, e)

    logger.info("Total words loaded: %d", total)
    return total


def _insert_words(category: str, words: list[str]) -> int:
    """درج کلمات در دیتابیس."""
    count = 0
    with get_conn() as conn:
        for word in words:
            word = word.strip()
            if not word or len(word) < 2:
                continue
            canonical = word.lower().strip()
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO words "
                    "(category, display_form, canonical_form) "
                    "VALUES (?, ?, ?)",
                    (category, word, canonical),
                )
                count += 1
            except Exception:
                pass
    return count


def is_valid_word(category: str, normalized: str) -> bool:
    """آیا کلمه در دیتابیس وجود دارد؟"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM words WHERE category=? AND canonical_form=? LIMIT 1",
            (category, normalized),
        ).fetchone()
        return row is not None


def get_word_count() -> int:
    with get_conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM words").fetchone()
        return row[0] if row else 0
