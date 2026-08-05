from dataclasses import dataclass, field


@dataclass
class Player:
    user_id: int
    username: str | None
    first_name: str
    score: int = 0


@dataclass
class GameSettings:
    total_rounds: int = 3
    round_duration: int = 45
    selected_categories: list[str] = field(
        default_factory=lambda: ["اسم", "فامیل", "شهر", "کشور", "حیوان"]
    )
    hard_letters_enabled: bool = False


@dataclass
class Round:
    id: str
    game_id: str
    round_number: int
    letter: str
    duration: int
    status: str = "waiting"
    start_time: float | None = None
    end_time: float | None = None


@dataclass
class Answer:
    id: str
    round_id: str
    player_id: int
    category: str
    display_text: str
    normalized_text: str
    is_valid: bool = False
    score: int = 0
    is_final: bool = False
    submitted_at: float | None = None


@dataclass
class Game:
    id: str
    group_id: int
    host_id: int
    status: str = "lobby"
    total_rounds: int = 3
    current_round_index: int = 0
    letter: str | None = None
    players: list[Player] = field(default_factory=list)
    used_letters: list[str] = field(default_factory=list)
    settings: GameSettings = field(default_factory=GameSettings)
    created_at: float = 0.0
    started_at: float | None = None
    lobby_message_id: int | None = None
    game_message_id: int | None = None
    extended: bool = False
    status_message_id: int | None = None
    current_round: Round | None = None
    pv_message_ids: dict[int, int] = field(default_factory=dict)
    round_scores: dict[int, int] = field(default_factory=dict)
    round_answers: dict[tuple[int, str], Answer] = field(default_factory=dict)
