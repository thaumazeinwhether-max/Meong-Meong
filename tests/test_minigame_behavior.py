"""Event and generation checks that do not require a visible game window."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from src.minigames.catch_game import CatchGame
from src.minigames.typing_game import TypingGame


class DummySound:
    def play(self) -> None:
        return None


class DummySounds:
    def __init__(self) -> None:
        self.played: list[str] = []

    def play(self, name: str, minimum_interval_ms: int = 0) -> bool:
        self.played.append(name)
        return True


class DummyAssets:
    def __init__(self) -> None:
        self.sounds = DummySounds()

    def sound(self, _name: str) -> DummySound:
        return DummySound()


class DummyGame:
    def __init__(self) -> None:
        self.assets = DummyAssets()
        self.completed = None

    def complete_game(self, result) -> None:
        self.completed = result

    def change_screen(self, _name: str) -> None:
        return None


def key(character: str) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=ord(character), unicode=character)


def test_typing_correct_word_scores_and_barks() -> None:
    game = DummyGame()
    typing = TypingGame(game)
    typing.word = "dog"
    for character in "dog":
        typing.handle_event(key(character))
    assert typing.score == 1
    assert "bark" in game.assets.sounds.played
    assert typing.animator.state == "bark"


def test_typing_wrong_key_gives_feedback_and_backspace_repairs_input() -> None:
    game = DummyGame()
    typing = TypingGame(game)
    typing.word = "dog"
    typing.handle_event(key("x"))
    assert typing.score == 0
    assert typing.input_text == "x"
    assert typing.error_time > 0
    assert "typing_error" in game.assets.sounds.played
    typing.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE, unicode=""))
    assert typing.input_text == ""


def test_catch_spawn_creates_independent_falling_items() -> None:
    catch = CatchGame(DummyGame())
    first = catch.spawn_item()
    first_timer = catch.spawn_timer
    second = catch.spawn_item()
    assert first.y < 0 and second.y < 0
    assert first.speed > 0 and second.speed > 0
    assert len(catch.items) == 2
    assert first_timer > 0 and catch.spawn_timer > 0
