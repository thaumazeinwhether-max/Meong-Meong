"""Shared Esc confirmation behavior for all minigames."""

import pygame

from src import config
from src.components import Button, draw_panel, draw_text
from src.screens.base import BaseScreen


class BaseMinigame(BaseScreen):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.exit_overlay = False
        self.exit_buttons = [
            Button(pygame.Rect(420, 420, 200, 58), "続ける", self.close_exit_overlay, config.MINT),
            Button(pygame.Rect(660, 420, 200, 58), "終了する", self.abort_game, config.PEACH),
        ]

    def handle_common_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.exit_overlay = not self.exit_overlay
            return True
        if self.exit_overlay:
            for button in self.exit_buttons:
                button.handle_event(event, self.click_sound)
            return True
        return False

    def close_exit_overlay(self) -> None:
        self.exit_overlay = False

    def abort_game(self) -> None:
        # A voluntary exit is not a completed play. It does not update a best
        # score or run an unlock check.
        self.game.change_screen("minigame_select")

    def draw_exit_overlay(self, surface: pygame.Surface) -> None:
        if not self.exit_overlay:
            return
        shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        shade.fill((45, 35, 40, 145))
        surface.blit(shade, (0, 0))
        panel = pygame.Rect(345, 245, 590, 290)
        draw_panel(surface, panel)
        draw_text(surface, "ミニゲームを終了しますか？", self.assets.font(34, True), config.INK, (640, 315), center=True)
        draw_text(surface, "途中の記録は保存されません", self.assets.font(21), config.MUTED_INK, (640, 365), center=True)
        for button in self.exit_buttons:
            button.draw(surface, self.assets.font(23, True))

    def draw_game_header(self, surface: pygame.Surface, title: str, detail: str) -> None:
        header = pygame.Surface((config.SCREEN_WIDTH, 82), pygame.SRCALPHA)
        header.fill((255, 252, 246, 225))
        surface.blit(header, (0, 0))
        draw_text(surface, title, self.assets.font(29, True), config.INK, (30, 20))
        draw_text(surface, detail, self.assets.font(25, True), config.PEACH_DARK, (950, 22))
        draw_text(surface, "Esc：途中終了", self.assets.font(17), config.MUTED_INK, (30, 57))

