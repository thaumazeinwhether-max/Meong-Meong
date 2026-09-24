"""Shared minigame result and first-time unlock screens."""

import math

import pygame

from src import config
from src.animation import CharacterAnimator, KURUM_CLIPS
from src.components import Button, draw_panel, draw_play_icon, draw_text
from src.models import GameResult
from src.screens.base import BaseScreen


class ResultScreen(BaseScreen):
    def __init__(self, game, result: GameResult) -> None:
        super().__init__(game)
        self.result = result
        self.animator = CharacterAnimator(KURUM_CLIPS, "happy" if result.is_new_best else "idle")
        self.buttons = [
            Button(pygame.Rect(250, 545, 230, 60), "もう一度", lambda: game.leave_result(result.game_id), config.PEACH),
            Button(pygame.Rect(525, 545, 230, 60), "ゲーム選択へ", lambda: game.leave_result("minigame_select"), config.MINT),
            Button(pygame.Rect(800, 545, 230, 60), "部屋へ戻る", lambda: game.leave_result("room"), config.SKY),
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        for button in self.buttons:
            button.handle_event(event, self.click_sound)

    def update(self, dt: float) -> None:
        self.animator.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self.draw_room_background(surface, dim=True)
        panel = pygame.Rect(190, 70, 900, 575)
        draw_panel(surface, panel)
        draw_text(surface, self.result.title, self.assets.font(43, True), config.INK, (640, 125), center=True)

        if self.result.is_clear is True:
            status = "クリア！"
            status_color = config.SUCCESS
        elif self.result.is_clear is False:
            status = "もう一度チャレンジ！"
            status_color = config.PEACH_DARK
        else:
            status = "今回の記録"
            status_color = config.MINT_DARK
        draw_text(surface, status, self.assets.font(28, True), status_color, (640, 185), center=True)
        draw_text(
            surface,
            f"{self.result.score} {self.result.unit}",
            self.assets.font(76, True),
            config.INK,
            (640, 285),
            center=True,
        )
        best = "未記録" if self.result.best_score is None else f"{self.result.best_score} {self.result.unit}"
        draw_text(surface, f"自己ベスト　{best}", self.assets.font(25, True), config.MUTED_INK, (640, 380), center=True)
        if self.result.is_new_best:
            draw_text(surface, "NEW BEST!", self.assets.font(28, True), config.GOLD, (640, 425), center=True)
        self.animator.draw(surface, self.assets, 145, (330, 511))
        draw_text(surface, "次に進む先を選んでください", self.assets.font(20), config.MUTED_INK, (640, 495), center=True)
        for button in self.buttons:
            button.draw(surface, self.assets.font(21, True))


class UnlockScreen(BaseScreen):
    LABELS = {
        "nosework": "ノーズワーク",
        "tug": "ひっぱりっこ",
        "ball": "ボール遊び",
    }

    def __init__(self, game, play_id: str, destination: str) -> None:
        super().__init__(game)
        self.play_id = play_id
        self.destination = destination
        self.time = 0.0
        self.animator = CharacterAnimator(KURUM_CLIPS, "happy")
        self.continue_button = Button(
            pygame.Rect(500, 580, 280, 62),
            "つづける",
            lambda: game.finish_unlock(destination),
            config.PEACH,
        )
        self.assets.sound("unlock").play()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.time > 0.7:
            self.continue_button.handle_event(event, self.click_sound)

    def update(self, dt: float) -> None:
        self.time += dt
        self.animator.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((255, 241, 210))
        for index in range(22):
            angle = index / 22 * math.tau + self.time * 0.25
            radius = 250 + (index % 3) * 45
            x = int(640 + math.cos(angle) * radius)
            y = int(330 + math.sin(angle) * radius * 0.62)
            pygame.draw.circle(surface, [config.PEACH, config.MINT, config.SKY, config.GOLD][index % 4], (x, y), 8 + index % 5)

        draw_text(surface, "新しい遊びが増えた！", self.assets.font(48, True), config.INK, (640, 75), center=True)
        self.animator.draw(surface, self.assets, 300, (505, 537))
        draw_play_icon(surface, self.play_id, (830, 330), 1.8)
        draw_text(surface, self.LABELS[self.play_id], self.assets.font(38, True), config.PEACH_DARK, (830, 420), center=True)
        draw_text(surface, "これから「あそぶ」で選べます", self.assets.font(23), config.MUTED_INK, (830, 475), center=True)
        self.continue_button.draw(surface, self.assets.font(24, True))
