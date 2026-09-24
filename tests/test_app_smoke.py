"""Headless drawing checks for every initial-version screen."""

import os
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.animation import KURUM_CLIPS
from src.game import Game
from src.models import GameResult, UserProgress, UserSession
from src.screens.result_screens import ResultScreen, UnlockScreen


def test_all_screens_draw_without_missing_assets_or_exceptions() -> None:
    database_path = Path("data") / f"screen_test_{uuid4().hex}.db"
    pygame.mixer.pre_init(44_100, -16, 1, 512)
    pygame.init()
    try:
        game = Game(database_path)
        game.current_user = UserSession(
            user_id=1,
            login_name="screen_test",
            nickname="クルム",
            progress=UserProgress(
                nosework_unlocked=True,
                tug_unlocked=True,
                ball_unlocked=True,
            ),
        )

        for clip in KURUM_CLIPS.values():
            for frame in clip.frames:
                image = game.assets.kurum_frame(frame.sheet, frame.row, frame.column, 180)
                assert image.get_bounding_rect().width > 20

        for screen_name in (
            "title",
            "login",
            "register",
            "nickname",
            "room",
            "play_select",
            "minigame_select",
            "walk",
            "typing",
            "catch",
        ):
            game.change_screen(screen_name)
            game.current_screen.update(0.016)
            game.current_screen.draw(game.surface)

        result = GameResult("catch", "おやつキャッチ", 15, "点", True, 15, True, "ball")
        ResultScreen(game, result).draw(game.surface)
        UnlockScreen(game, "ball", "room").draw(game.surface)

        game.change_screen("walk")
        game.current_screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game.current_screen.draw(game.surface)
        pygame.display.flip()
    finally:
        pygame.quit()
        database_path.unlink(missing_ok=True)
