"""Headless checks for generated sound effects and overlap protection."""

import os

os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.sound_manager import SoundManager


def test_all_effects_load_and_bark_cooldown_prevents_overlap() -> None:
    pygame.mixer.pre_init(44_100, -16, 1, 512)
    pygame.init()
    try:
        sounds = SoundManager()
        for name in (
            "click",
            "success",
            "jump",
            "correct",
            "treat",
            "bad",
            "unlock",
            "bark",
            "typing_error",
        ):
            assert sounds.get(name) is not None
        assert sounds.play("bark", minimum_interval_ms=10_000) is True
        assert sounds.play("bark", minimum_interval_ms=10_000) is False
    finally:
        pygame.quit()
