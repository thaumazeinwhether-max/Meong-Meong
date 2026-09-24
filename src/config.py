"""Project-wide settings and game balance values.

The values under ``FIXED INITIAL RELEASE RULES`` are formal specifications.
The values under ``ADJUSTABLE BALANCE`` are intentionally easy to tune after
play-testing without changing the game rules.
"""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "meong_meong.db"

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
GAME_TITLE = "Meong Meong!"

# Soft, warm colors used throughout the interface.
CREAM = (255, 249, 239)
PANEL = (255, 252, 246)
INK = (72, 61, 66)
MUTED_INK = (125, 110, 116)
PEACH = (242, 164, 142)
PEACH_DARK = (211, 126, 109)
MINT = (147, 205, 177)
MINT_DARK = (91, 157, 126)
SKY = (168, 216, 240)
GOLD = (245, 195, 92)
WHITE = (255, 255, 255)
SHADOW = (70, 55, 60, 55)
ERROR = (190, 72, 72)
SUCCESS = (62, 145, 102)

# ---------------------------------------------------------------------------
# FIXED INITIAL RELEASE RULES -- do not change during balance tuning.
# ---------------------------------------------------------------------------
WALK_PIXELS_PER_METER = 20
WALK_UNLOCK_METERS = 500
TYPING_POINTS_PER_WORD = 1
TYPING_UNLOCK_SCORE = 10
CATCH_TIME_LIMIT_SECONDS = 30.0
CATCH_CLEAR_SCORE = 10
CATCH_UNLOCK_SCORE = 15
CATCH_MIN_SCORE = 0

# ---------------------------------------------------------------------------
# ADJUSTABLE BALANCE -- intentionally not part of the fixed specification.
# ---------------------------------------------------------------------------
WALK_GROUND_Y = 590
WALK_DOG_X = 210
WALK_DOG_SIZE = 150
WALK_JUMP_SPEED = -790.0
WALK_GRAVITY = 2150.0
WALK_START_SPEED = 410.0
WALK_MAX_SPEED = 710.0
WALK_SPEED_GAIN_PER_METER = 0.34
WALK_PATTERN_GAP_START = 560
WALK_PATTERN_GAP_MIN = 320
WALK_PATTERN_GAP_VARIATION = 90

TYPING_START_SPEED = 122.0
TYPING_SPEED_PER_POINT = 8.0
TYPING_SPEED_PER_SECOND = 1.15
TYPING_MAX_SPEED = 300.0

CATCH_DOG_SPEED = 430.0
CATCH_ITEM_START_SPEED = 225.0
CATCH_ITEM_MAX_SPEED = 390.0
CATCH_SPAWN_INTERVAL_START = 1.05
CATCH_SPAWN_INTERVAL_MIN = 0.62
CATCH_TREAT_CHANCE_START = 0.70
CATCH_TREAT_CHANCE_END = 0.60
CATCH_MIN_SPAWN_X_DISTANCE = 105

ROOM_CHARACTER_SIZE = 330
MINIGAME_CHARACTER_SIZE = 150
ANIMATION_DURATION = 2.4

ROOM_BACKGROUND_PATH = ASSETS_DIR / "background" / "room.png"
WALK_BACKGROUND_PATH = ASSETS_DIR / "background" / "walk_park.png"
KURUM_MASTER_PATH = ASSETS_DIR / "character" / "master" / "meong_master_front.png"
KURUM_MOTION_SHEET_PATH = ASSETS_DIR / "character" / "animations" / "kurum_motion_sheet.png"
KURUM_ACTION_SHEET_PATH = ASSETS_DIR / "character" / "animations" / "kurum_action_sheet.png"
WORDS_PATH = DATA_DIR / "typing_words.txt"
