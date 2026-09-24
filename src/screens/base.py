"""Base class shared by all normal screens."""

from typing import TYPE_CHECKING

import pygame

from src import config

if TYPE_CHECKING:
    from src.game import Game


class BaseScreen:
    def __init__(self, game: "Game") -> None:
        self.game = game
        self.assets = game.assets
        self.click_sound = self.assets.sound("click")

    def handle_event(self, event: pygame.event.Event) -> None:
        return None

    def update(self, dt: float) -> None:
        return None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(config.CREAM)

    def draw_room_background(self, surface: pygame.Surface, dim: bool = False) -> None:
        surface.blit(self.assets.room_background(), (0, 0))
        if dim:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((50, 40, 45, 95))
            surface.blit(overlay, (0, 0))

