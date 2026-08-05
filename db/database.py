import json
import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager

logger = logging.getLogger(__name__)

_db_path: Path | None = None


def init(path: Path) -> None:
    """Initialize database and create all tables."""
    global _db_path
    _db_path = path
    _create_tables()
    logger.info("Database initialized: %s", path)


@contextmanager
def get_conn():
    """Context manager for database connections."""
    if _db_path is None:
        raise RuntimeError("Database not initialized. Call db.init() first.")
    conn = sqlite3.connect(str(_db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _create_tables() -> None:
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS known_groups (
                group_id INTEGER PRIMARY KEY,
                name TEXT,
                joined_at REAL DEFAULT (strftime('%s','now'))
            );

            CREATE TABLE IF NOT EXISTS games (
                id TEXT PRIMARY KEY,
                group_id INTEGER NOT NULL,
                host_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'lobby',
                total_rounds INTEGER NOT NULL DEFAULT 3,
                current_round_index INTEGER DEFAULT 0,
                letter TEXT,
                players TEXT DEFAULT '[]',
                used_letters TEXT DEFAULT '[]',
                settings TEXT DEFAULT '{}',
                created_at REAL DEFAULT (strftime('%s','now')),
                started_at REAL
            );

            CREATE TABLE IF NOT EXISTS rounds (
                id TEXT PRIMARY KEY,
                game_id TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                letter TEXT NOT NULL,
                duration INTEGER NOT NULL DEFAULT 45,
                status TEXT NOT NULL DEFAULT 'waiting',
                start_time REAL,
                end_time REAL,
                player_scores TEXT DEFAULT '{}',
                FOREIGN KEY (game_id) REFERENCES games(id)
            );

            CREATE TABLE IF NOT EXISTS answers (
                id TEXT PRIMARY KEY,
                round_id TEXT NOT NULL,
                player_id INTEGER NOT NULL,
                category TEXT NOT NULL,
                display_text TEXT NOT NULL,
                normalized_text TEXT NOT NULL,
                is_valid INTEGER NOT NULL DEFAULT 0,
                score INTEGER NOT NULL DEFAULT 0,
                is_final INTEGER NOT NULL DEFAULT 0,
                submitted_at REAL,
                FOREIGN KEY (round_id) REFERENCES rounds(id)
            );

            CREATE TABLE IF NOT EXISTS scores (
                id TEXT PRIMARY KEY,
                game_id TEXT NOT NULL,
                round_id TEXT NOT NULL,
                player_id INTEGER NOT NULL,
                score INTEGER NOT NULL DEFAULT 0,
                total_score INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (game_id) REFERENCES games(id),
                FOREIGN KEY (round_id) REFERENCES rounds(id)
            );

            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                round_duration INTEGER NOT NULL DEFAULT 45,
                total_rounds INTEGER NOT NULL DEFAULT 3,
                selected_categories TEXT DEFAULT '["اسم","فامیل","شهر","کشور","حیوان"]',
                hard_letters_enabled INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS game_events (
                id TEXT PRIMARY KEY,
                game_id TEXT NOT NULL,
                event TEXT NOT NULL,
                data TEXT DEFAULT '{}',
                created_at REAL DEFAULT (strftime('%s','now'))
            );

            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                display_form TEXT NOT NULL,
                canonical_form TEXT NOT NULL,
                source TEXT DEFAULT 'github',
                created_at REAL DEFAULT (strftime('%s','now')),
                UNIQUE(category, canonical_form)
            );

            CREATE INDEX IF NOT EXISTS idx_words_cat_can
                ON words(category, canonical_form);
            CREATE INDEX IF NOT EXISTS idx_games_group_status
                ON games(group_id, status);
            CREATE INDEX IF NOT EXISTS idx_rounds_game
                ON rounds(game_id);
            CREATE INDEX IF NOT EXISTS idx_answers_round
                ON answers(round_id);
            CREATE INDEX IF NOT EXISTS idx_scores_game
                ON scores(game_id);
            CREATE INDEX IF NOT EXISTS idx_events_game
                ON game_events(game_id);
        """)
        logger.info("All tables created successfully.")


# ═══════════════════════════════════════════════════════════
#  User Settings — ذخیره و لود تنظیمات شخصی
# ═══════════════════════════════════════════════════════════

def save_user_settings(
    user_id: int,
    round_duration: int,
    total_rounds: int,
    selected_categories: list[str],
    hard_letters_enabled: bool,
) -> None:
    """ذخیره تنظیمات شخصی کاربر در دیتابیس."""
    with get_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO user_settings
            (user_id, round_duration, total_rounds, selected_categories, hard_letters_enabled)
            VALUES (?, ?, ?, ?, ?)""",
            (
                user_id,
                round_duration,
                total_rounds,
                json.dumps(selected_categories, ensure_ascii=False),
                int(hard_letters_enabled),
            ),
        )


def load_user_settings(user_id: int) -> dict | None:
    """لود تنظیمات شخصی کاربر از دیتابیس. اگر نباشد None برمیگرداند."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM user_settings WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "round_duration": row["round_duration"],
            "total_rounds": row["total_rounds"],
            "selected_categories": json.loads(row["selected_categories"]),
            "hard_letters_enabled": bool(row["hard_letters_enabled"]),
        }
