"""Tests for progressive, reachable minigame difficulty."""

import random

from src.minigames.difficulty import (
    WALK_PATTERNS,
    catch_difficulty,
    generate_walk_pattern,
    pattern_is_avoidable,
    safe_next_pattern_distance,
    typing_speed,
    typing_word_lengths,
    walk_difficulty,
)


def test_walk_difficulty_increases_gradually() -> None:
    start = walk_difficulty(0)
    goal = walk_difficulty(500)
    late = walk_difficulty(1_000)
    assert start.speed < goal.speed <= late.speed
    assert start.pattern_gap > goal.pattern_gap >= late.pattern_gap
    assert "double" not in start.allowed_patterns
    assert "double" in goal.allowed_patterns


def test_every_walk_pattern_is_physically_avoidable_when_available() -> None:
    for distance in (0, 80, 170, 300, 500, 1_000):
        difficulty = walk_difficulty(distance)
        for name in difficulty.allowed_patterns:
            assert pattern_is_avoidable(WALK_PATTERNS[name], difficulty.speed), name


def test_walk_pattern_generator_uses_only_unlocked_patterns() -> None:
    random_source = random.Random(7)
    allowed = set(walk_difficulty(170).allowed_patterns)
    for _ in range(40):
        generated = generate_walk_pattern(170, random_source)
        assert generated in [WALK_PATTERNS[name] for name in allowed]


def test_walk_patterns_leave_time_to_land_before_next_pattern() -> None:
    for distance in (0, 170, 500, 1_000):
        difficulty = walk_difficulty(distance)
        air_time = 2 * 790 / 2150
        minimum_landing_distance = difficulty.speed * air_time + 80
        for name in difficulty.allowed_patterns:
            spacing = safe_next_pattern_distance(WALK_PATTERNS[name], difficulty)
            assert spacing >= minimum_landing_distance


def test_typing_uses_longer_words_and_faster_motion_later() -> None:
    assert typing_word_lengths(0) == (3, 5)
    assert typing_word_lengths(5) == (4, 7)
    assert typing_word_lengths(10) == (6, 10)
    assert typing_speed(0, 0) < typing_speed(5, 20) < typing_speed(10, 40)


def test_catch_items_accelerate_and_spawn_more_often() -> None:
    start = catch_difficulty(0)
    end = catch_difficulty(30)
    assert end.interval_min < start.interval_min
    assert end.interval_max < start.interval_max
    assert end.fall_speed_min > start.fall_speed_min
    assert end.fall_speed_max > start.fall_speed_max
    assert end.treat_chance < start.treat_chance
