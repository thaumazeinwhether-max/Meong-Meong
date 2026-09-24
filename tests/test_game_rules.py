"""Tests for the fixed, screen-independent game rules."""

from src.game_rules import (
    apply_catch_item,
    awards_ball,
    awards_nosework,
    awards_tug,
    catch_is_clear,
    catch_result_after_time,
    typing_score_for_correct_words,
    walk_distance_meters,
)


def test_walk_uses_twenty_pixels_per_meter_and_floors_result() -> None:
    assert walk_distance_meters(9_999.9) == 499
    assert walk_distance_meters(10_000.0) == 500
    assert awards_nosework(499) is False
    assert awards_nosework(500) is True


def test_typing_awards_one_point_per_word_and_unlocks_at_ten() -> None:
    assert typing_score_for_correct_words(7) == 7
    assert awards_tug(9) is False
    assert awards_tug(10) is True


def test_catch_score_never_falls_below_zero() -> None:
    assert apply_catch_item(0, is_treat=False) == 0
    assert apply_catch_item(2, is_treat=False) == 1
    assert apply_catch_item(2, is_treat=True) == 3


def test_catch_clear_and_unlock_are_separate_thresholds() -> None:
    assert catch_is_clear(9) is False
    assert catch_is_clear(10) is True
    assert awards_ball(14) is False
    assert awards_ball(15) is True


def test_catch_does_not_finish_before_thirty_seconds() -> None:
    assert catch_result_after_time(29.999, 20) is None
    assert catch_result_after_time(30.0, 9) is False
    assert catch_result_after_time(30.0, 10) is True
