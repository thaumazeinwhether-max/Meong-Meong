"""Adjustable, testable difficulty curves for the three minigames."""

from dataclasses import dataclass
import random

from src import config


@dataclass(frozen=True)
class ObstacleSpec:
    offset: int
    width: int
    height: int
    kind: str


@dataclass(frozen=True)
class WalkDifficulty:
    speed: float
    pattern_gap: int
    allowed_patterns: tuple[str, ...]


WALK_PATTERNS: dict[str, tuple[ObstacleSpec, ...]] = {
    "short": (ObstacleSpec(0, 52, 56, "cone"),),
    "tall": (ObstacleSpec(0, 48, 82, "cone"),),
    "wide_low": (ObstacleSpec(0, 102, 48, "bush"),),
    "double": (ObstacleSpec(0, 46, 58, "cone"), ObstacleSpec(112, 48, 62, "cone")),
    "mixed": (ObstacleSpec(0, 48, 78, "cone"), ObstacleSpec(116, 68, 48, "bush")),
    "long_short": (ObstacleSpec(0, 82, 46, "bush"), ObstacleSpec(142, 42, 72, "cone")),
}


def walk_difficulty(distance_meters: int) -> WalkDifficulty:
    progress = min(1.0, max(0, distance_meters) / 700)
    speed = min(config.WALK_MAX_SPEED, config.WALK_START_SPEED + distance_meters * config.WALK_SPEED_GAIN_PER_METER)
    gap = round(config.WALK_PATTERN_GAP_START - (config.WALK_PATTERN_GAP_START - config.WALK_PATTERN_GAP_MIN) * progress)
    patterns = ["short", "tall"]
    if distance_meters >= 80:
        patterns.append("wide_low")
    if distance_meters >= 170:
        patterns.append("double")
    if distance_meters >= 300:
        patterns.extend(["mixed", "long_short"])
    return WalkDifficulty(speed, gap, tuple(patterns))


def generate_walk_pattern(distance_meters: int, random_source: random.Random | None = None) -> tuple[ObstacleSpec, ...]:
    source = random_source or random
    difficulty = walk_difficulty(distance_meters)
    return WALK_PATTERNS[source.choice(difficulty.allowed_patterns)]


def pattern_is_avoidable(pattern: tuple[ObstacleSpec, ...], speed: float) -> bool:
    """Conservatively verify that one full jump can clear the generated span."""
    if not pattern:
        return False
    span = max(spec.offset + spec.width for spec in pattern) - min(spec.offset for spec in pattern)
    air_time = 2 * abs(config.WALK_JUMP_SPEED) / config.WALK_GRAVITY
    horizontal_reach = speed * air_time
    maximum_jump_height = config.WALK_JUMP_SPEED**2 / (2 * config.WALK_GRAVITY)
    return span + 70 <= horizontal_reach * 0.92 and max(spec.height for spec in pattern) <= maximum_jump_height * 0.78


def safe_next_pattern_distance(pattern: tuple[ObstacleSpec, ...], difficulty: WalkDifficulty) -> int:
    """Leave enough distance to land before the next pattern can begin."""
    span = max(spec.offset + spec.width for spec in pattern) - min(spec.offset for spec in pattern)
    air_time = 2 * abs(config.WALK_JUMP_SPEED) / config.WALK_GRAVITY
    horizontal_reach = difficulty.speed * air_time
    return max(span + difficulty.pattern_gap, round(horizontal_reach + 90))


@dataclass(frozen=True)
class CatchDifficulty:
    interval_min: float
    interval_max: float
    fall_speed_min: float
    fall_speed_max: float
    treat_chance: float


def catch_difficulty(elapsed_seconds: float) -> CatchDifficulty:
    progress = min(1.0, max(0.0, elapsed_seconds) / config.CATCH_TIME_LIMIT_SECONDS)
    interval = config.CATCH_SPAWN_INTERVAL_START - (config.CATCH_SPAWN_INTERVAL_START - config.CATCH_SPAWN_INTERVAL_MIN) * progress
    speed = config.CATCH_ITEM_START_SPEED + (config.CATCH_ITEM_MAX_SPEED - config.CATCH_ITEM_START_SPEED) * progress
    treat_chance = config.CATCH_TREAT_CHANCE_START + (config.CATCH_TREAT_CHANCE_END - config.CATCH_TREAT_CHANCE_START) * progress
    return CatchDifficulty(max(0.48, interval - 0.16), interval + 0.20, speed * 0.88, speed * 1.10, treat_chance)


def typing_word_lengths(score: int) -> tuple[int, int]:
    if score < 4:
        return 3, 5
    if score < 8:
        return 4, 7
    return 6, 10


def typing_speed(score: int, elapsed_seconds: float) -> float:
    return min(
        config.TYPING_MAX_SPEED,
        config.TYPING_START_SPEED + score * config.TYPING_SPEED_PER_POINT + elapsed_seconds * config.TYPING_SPEED_PER_SECOND,
    )
