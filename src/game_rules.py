"""Pure game-rule functions.

Keeping these rules separate makes the fixed specifications easy to test and
prevents screen drawing code from silently changing progression behavior.
"""

import math

from src import config


def walk_distance_meters(distance_pixels: float) -> int:
    """Convert accumulated pixel distance to the one canonical integer result."""
    safe_pixels = max(0.0, float(distance_pixels))
    return math.floor(safe_pixels / config.WALK_PIXELS_PER_METER)


def awards_nosework(distance_meters: int) -> bool:
    return distance_meters >= config.WALK_UNLOCK_METERS


def typing_score_for_correct_words(correct_words: int) -> int:
    return max(0, int(correct_words)) * config.TYPING_POINTS_PER_WORD


def awards_tug(typing_score: int) -> bool:
    return typing_score >= config.TYPING_UNLOCK_SCORE


def apply_catch_item(score: int, is_treat: bool) -> int:
    change = 1 if is_treat else -1
    return max(config.CATCH_MIN_SCORE, int(score) + change)


def catch_is_clear(final_score: int) -> bool:
    return final_score >= config.CATCH_CLEAR_SCORE


def awards_ball(final_score: int) -> bool:
    return final_score >= config.CATCH_UNLOCK_SCORE


def unlock_for_result(game_id: str, score: int) -> str | None:
    checks = {
        "walk": (awards_nosework, "nosework"),
        "typing": (awards_tug, "tug"),
        "catch": (awards_ball, "ball"),
    }
    if game_id not in checks:
        raise ValueError(f"Unknown game id: {game_id}")
    check, play_id = checks[game_id]
    return play_id if check(score) else None


def catch_result_after_time(elapsed_seconds: float, score: int) -> bool | None:
    """Return None while playing, then the clear result at 30 seconds."""
    if elapsed_seconds < config.CATCH_TIME_LIMIT_SECONDS:
        return None
    return catch_is_clear(score)

