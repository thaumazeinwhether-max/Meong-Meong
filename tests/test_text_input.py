"""Pygame event tests for the shared account-screen text inputs."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from src.screens.auth_screens import LoginScreen, NicknameScreen, RegisterScreen


class DummySound:
    def play(self) -> None:
        return None


class DummyAssets:
    def sound(self, _name: str) -> DummySound:
        return DummySound()


class DummyGame:
    def __init__(self) -> None:
        self.assets = DummyAssets()

    def change_screen(self, _screen_name: str) -> None:
        return None


@pytest.fixture(autouse=True)
def pygame_text_input() -> None:
    pygame.init()
    yield
    pygame.key.stop_text_input()
    pygame.quit()


def click(screen, position: tuple[int, int]) -> None:
    screen.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=position)
    )


def type_text(screen, text: str) -> None:
    screen.handle_event(pygame.event.Event(pygame.TEXTINPUT, text=text))


def press_backspace(screen) -> None:
    screen.handle_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE, unicode="")
    )


@pytest.mark.parametrize("screen_class", [LoginScreen, RegisterScreen])
def test_click_focus_ascii_input_backspace_and_field_switch(screen_class) -> None:
    screen = screen_class(DummyGame())

    click(screen, screen.username.rect.center)
    assert screen.username.active is True
    assert screen.password.active is False
    type_text(screen, "User123")
    assert screen.username.text == "User123"

    press_backspace(screen)
    assert screen.username.text == "User12"

    click(screen, screen.password.rect.center)
    assert screen.username.active is False
    assert screen.password.active is True
    type_text(screen, "Pass456")
    assert screen.username.text == "User12"
    assert screen.password.text == "Pass456"
    assert screen.password.display_text == "●" * len("Pass456")


def test_register_can_switch_from_password_to_confirmation() -> None:
    screen = RegisterScreen(DummyGame())
    click(screen, screen.password.rect.center)
    type_text(screen, "secret1")
    click(screen, screen.confirm.rect.center)
    type_text(screen, "secret1")

    assert screen.password.active is False
    assert screen.confirm.active is True
    assert screen.password.text == "secret1"
    assert screen.confirm.text == "secret1"
    assert screen.confirm.display_text == "●" * len("secret1")


def test_nickname_screen_receives_textinput_and_backspace() -> None:
    screen = NicknameScreen(DummyGame())
    click(screen, screen.nickname.rect.center)
    type_text(screen, "Kurum7")
    press_backspace(screen)

    assert screen.nickname.active is True
    assert screen.nickname.text == "Kurum"


def test_ascii_only_username_rejects_spaces_and_non_ascii_text() -> None:
    screen = RegisterScreen(DummyGame())
    click(screen, screen.username.rect.center)
    type_text(screen, "abc １２3")

    assert screen.username.text == "abc3"


def test_nickname_ime_composition_is_visible_then_committed() -> None:
    screen = NicknameScreen(DummyGame())
    click(screen, screen.nickname.rect.center)
    screen.handle_event(
        pygame.event.Event(pygame.TEXTEDITING, text="くる", start=0, length=2)
    )
    assert screen.nickname.composition_text == "くる"
    assert screen.nickname.text == ""

    type_text(screen, "くるむ")
    assert screen.nickname.text == "くるむ"
    assert screen.nickname.composition_text == ""


def test_ime_composition_clears_on_backspace_or_focus_loss() -> None:
    screen = NicknameScreen(DummyGame())
    screen.handle_event(
        pygame.event.Event(pygame.TEXTEDITING, text="変換中", start=0, length=3)
    )
    press_backspace(screen)
    assert screen.nickname.composition_text == ""

    screen.handle_event(
        pygame.event.Event(pygame.TEXTEDITING, text="入力中", start=0, length=3)
    )
    click(screen, (20, 20))
    assert screen.nickname.active is False
    assert screen.nickname.composition_text == ""
