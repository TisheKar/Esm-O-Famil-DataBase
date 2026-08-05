import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- Bot ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set. Create .env file with your token.")

# --- Database ---
DATABASE_PATH = DATA_DIR / "bot.db"

# --- Lobby ---
LOBBY_TIMEOUT = 180
LOBBY_WARNING_AT = 150
LOBBY_EXTEND_SECONDS = 120
LOBBY_EXTEND_MAX = 1

# --- Game ---
MIN_PLAYERS = 2
MAX_PLAYERS = 20

# --- Letters ---
ACTIVE_LETTERS = [
    "ا", "ب", "پ", "ت", "ج", "چ", "ح", "خ", "د", "ر", "ز", "س", "ش",
    "ص", "ض", "ط", "ع", "ف", "ق", "ک", "گ", "ل", "م", "ن", "و", "ه", "ی",
]
COMMON_LETTERS = ["ا", "م", "ن", "ر", "س", "ش", "ب", "ت", "د", "ل", "ه", "و", "ی"]
HARD_LETTERS = ["ث", "ذ", "ظ", "ژ", "غ"]

# --- Categories ---
DEFAULT_CATEGORIES = ["اسم", "فامیل", "شهر", "کشور", "حیوان"]
ALL_CATEGORIES = [
    "اسم", "فامیل", "شهر", "کشور", "حیوان",
    "غذا", "رنگ", "میوه", "گل", "شغل", "اشیا", "وسیله نقلیه",
]
CATEGORY_ICONS = {
    "اسم": "👤", "فامیل": "👪", "شهر": "🏙️", "کشور": "🌍", "حیوان": "🐾",
    "غذا": "🍽️", "رنگ": "🎨", "میوه": "🍎", "گل": "🌸",
    "شغل": "💼", "اشیا": "📦", "وسیله نقلیه": "🚗",
}

# --- Scoring ---
SCORE_UNIQUE = 10
SCORE_DUPLICATE_2 = 5
SCORE_DUPLICATE_3 = 3
SCORE_DUPLICATE_4_PLUS = 0
SCORE_FIRST_COMPLETE_BONUS = 5

# --- Rounds ---
DEFAULT_ROUNDS = 3
MIN_ROUNDS = 1
MAX_ROUNDS = 8
DEFAULT_DURATION = 45
MIN_DURATION = 20
MAX_DURATION = 120

# --- Timer ---
TIMER_INTERVALS = {"fast": 5, "normal": 7, "slow": 10}

# --- Words Database ---
WORDS_GITHUB_BASE_URL = "https://raw.githubusercontent.com/TisheKar/Esm-O-Famil-DataBase/main"

FILE_CATEGORY_MAP = {
    "persian_names.txt": "اسم",
    "surnames.txt": "فامیل",
    "cities.txt": "شهر",
    "countries.txt": "کشور",
    "animals.txt": "حیوان",
    "foods.txt": "غذا",
    "colors.txt": "رنگ",
    "fruits.txt": "میوه",
    "flowers.txt": "گل",
    "jobs.txt": "شغل",
    "objects.txt": "اشیا",
    "cars.txt": "وسیله نقلیه",
}
