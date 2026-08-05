import asyncio
import time
import uuid
import logging
from core.models import (
    Game, Player, GameSettings, Round, Answer,
)
from bot.config import (
    MIN_PLAYERS, MAX_PLAYERS,
    DEFAULT_CATEGORIES, DEFAULT_ROUNDS, DEFAULT_DURATION,
)

logger = logging.getLogger(__name__)


class GameManager:
    """In-memory game state manager."""

    def __init__(self):
        self._games: dict[int, Game] = {}
        self._tasks: dict[int, asyncio.Task] = {}

    # ── create / delete ──────────────────────────────────────
    def create_game(self, group_id: int, host: Player) -> Game:
        game_id = f"{group_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}"
        game = Game(
            id=game_id,
            group_id=group_id,
            host_id=host.user_id,
            players=[host],
            settings=GameSettings(
                total_rounds=DEFAULT_ROUNDS,
                round_duration=DEFAULT_DURATION,
                selected_categories=list(DEFAULT_CATEGORIES),
            ),
            created_at=time.time(),
        )
        self._games[group_id] = game
        logger.info("Game created: %s in group %s", game_id, group_id)
        return game

    def delete_game(self, group_id: int) -> Game | None:
        self.cancel_round_timer(group_id)
        game = self._games.pop(group_id, None)
        if game:
            logger.info("Game deleted: %s", game.id)
        return game

    # ── queries ──────────────────────────────────────────────
    def get_game(self, group_id: int) -> Game | None:
        return self._games.get(group_id)

    def is_active(self, group_id: int) -> bool:
        return group_id in self._games

    def can_start(self, group_id: int) -> tuple[bool, str]:
        game = self._games.get(group_id)
        if not game:
            return False, "بازی فعالی وجود ندارد."
        if game.status != "lobby":
            return False, "بازی قبلاً شروع شده."
        if len(game.players) < MIN_PLAYERS:
            return False, f"حداقل {MIN_PLAYERS} بازیکن نیاز است."
        return True, "ok"

    # ── player management ────────────────────────────────────
    def add_player(self, group_id: int, player: Player) -> tuple[bool, str]:
        game = self._games.get(group_id)
        if not game:
            return False, "بازی فعالی وجود ندارد."
        if game.status != "lobby":
            return False, "لابی بسته شده است."
        if len(game.players) >= MAX_PLAYERS:
            return False, f"لابی پر شده ({MAX_PLAYERS} نفر)."
        if any(p.user_id == player.user_id for p in game.players):
            return False, "شما قبلاً در لابی هستید."
        game.players.append(player)
        return True, "ok"

    def remove_player(self, group_id: int, user_id: int) -> tuple[bool, str]:
        game = self._games.get(group_id)
        if not game:
            return False, "بازی فعالی وجود ندارد."
        if game.host_id == user_id:
            return False, "میزبان نمی‌تواند از بازی خارج شود."
        before = len(game.players)
        game.players = [p for p in game.players if p.user_id != user_id]
        if len(game.players) == before:
            return False, "شما در بازی نیستید."
        return True, "ok"

    def start_game(self, group_id: int) -> Game | None:
        game = self._games.get(group_id)
        if not game:
            return None
        game.status = "playing"
        game.started_at = time.time()
        return game

    # ── Timer Management ─────────────────────────────────────

    def save_round_task(self, group_id: int, task: asyncio.Task) -> None:
        self._tasks[group_id] = task

    def cancel_round_timer(self, group_id: int) -> None:
        task = self._tasks.pop(group_id, None)
        if task and not task.done():
            task.cancel()

    # ── Round Management ─────────────────────────────────────

    def start_round(self, group_id: int) -> tuple | None:
        game = self._games.get(group_id)
        if not game or game.status != "playing":
            return None

        if game.current_round_index >= game.total_rounds:
            return None

        game.current_round_index += 1
        rounds_left = game.total_rounds - game.current_round_index + 1

        from core.letter import select_letter
        letter = select_letter(
            game.used_letters,
            hard_enabled=game.settings.hard_letters_enabled,
            total_rounds=game.total_rounds,
            rounds_left=rounds_left,
        )
        game.used_letters.append(letter)

        round_obj = Round(
            id=f"{game.id}_r{game.current_round_index}",
            game_id=game.id,
            round_number=game.current_round_index,
            letter=letter,
            duration=game.settings.round_duration,
            status="active",
            start_time=time.time(),
        )
        game.current_round = round_obj
        return round_obj

    def get_active_round(self, group_id: int):
        game = self._games.get(group_id)
        return game.current_round if game else None

    def end_round(self, group_id: int) -> Game | None:
        game = self._games.get(group_id)
        if not game or not game.current_round:
            return None
        game.current_round.status = "ended"
        game.current_round.end_time = time.time()
        return game

    def is_round_active(self, group_id: int) -> bool:
        game = self._games.get(group_id)
        return bool(game and game.current_round and game.current_round.status == "active")

    def get_game_by_player(self, user_id: int) -> Game | None:
        for game in self._games.values():
            if any(p.user_id == user_id for p in game.players):
                return game
        return None

    def submit_answer(
        self, group_id: int, player_id: int, category: str,
        display_text: str, normalized_text: str, is_valid: bool,
    ) -> Answer | None:
        game = self._games.get(group_id)
        if not game or not game.current_round:
            return None

        key = (player_id, category)
        if key in game.round_answers:
            return None

        answer = Answer(
            id=f"{game.current_round.id}_p{player_id}_{category}",
            round_id=game.current_round.id,
            player_id=player_id,
            category=category,
            display_text=display_text,
            normalized_text=normalized_text,
            is_valid=is_valid,
            score=0,
            submitted_at=time.time(),
        )
        game.round_answers[key] = answer
        return answer

    def get_round_answers(self, group_id: int) -> list[Answer]:
        game = self._games.get(group_id)
        if not game:
            return []
        return list(game.round_answers.values())

    def get_player_answers(self, group_id: int, player_id: int) -> dict[str, Answer]:
        game = self._games.get(group_id)
        if not game:
            return {}
        return {
            cat: ans
            for (pid, cat), ans in game.round_answers.items()
            if pid == player_id
        }

    def clear_round(self, group_id: int) -> None:
        game = self._games.get(group_id)
        if game:
            game.round_answers = {}
            game.current_round = None


# singleton
game_manager = GameManager()
