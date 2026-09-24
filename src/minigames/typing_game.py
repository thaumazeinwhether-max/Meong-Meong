"""Endless English-word typing game."""

import random

import pygame

from src import config
from src.animation import CharacterAnimator, KURUM_CLIPS
from src.components import draw_panel, draw_text
from src.minigames.base import BaseMinigame
from src.minigames.difficulty import typing_speed, typing_word_lengths
from src.models import GameResult


class TypingGame(BaseMinigame):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.words = self._load_words()
        opening_words = [word for word in self.words if 3 <= len(word) <= 5]
        self.word = random.choice(opening_words or self.words)
        self.word_x = float(config.SCREEN_WIDTH - 120)
        self.word_y = 250
        self.input_text = ""
        self.score = 0
        self.elapsed = 0.0
        self.bark_time = 0.0
        self.error_time = 0.0
        self.animator = CharacterAnimator(KURUM_CLIPS, "idle")
        self.finished = False

    def _load_words(self) -> list[str]:
        try:
            words = [line.strip().lower() for line in config.WORDS_PATH.read_text(encoding="utf-8").splitlines()]
            return [word for word in words if word.isalpha()] or ["dog", "happy", "play"]
        except OSError as error:
            print(f"Word data warning: {error}")
            return ["dog", "happy", "play"]

    @property
    def speed(self) -> float:
        return typing_speed(self.score, self.elapsed)

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.handle_common_event(event):
            return
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_BACKSPACE:
            self.input_text = self.input_text[:-1]
            return
        if event.unicode and event.unicode.isascii() and event.unicode.isalpha():
            self.input_text += event.unicode.lower()
            if not self.word.startswith(self.input_text):
                self.error_time = 0.32
                self.assets.sounds.play("typing_error", minimum_interval_ms=140)
                return
            if self.input_text == self.word:
                self.score += config.TYPING_POINTS_PER_WORD
                self.assets.sounds.play("bark", minimum_interval_ms=240)
                self.bark_time = 0.38
                self.animator.play("bark", restart=True)
                self._next_word()

    def _next_word(self) -> None:
        minimum, maximum = typing_word_lengths(self.score)
        choices = [word for word in self.words if word != self.word and minimum <= len(word) <= maximum]
        if not choices:
            choices = [word for word in self.words if word != self.word]
        self.word = random.choice(choices or self.words)
        self.word_x = float(config.SCREEN_WIDTH - 120)
        self.word_y = random.choice([220, 260, 300])
        self.input_text = ""

    def update(self, dt: float) -> None:
        if self.exit_overlay or self.finished:
            return
        self.elapsed += dt
        self.word_x -= self.speed * dt
        self.bark_time = max(0.0, self.bark_time - dt)
        self.error_time = max(0.0, self.error_time - dt)
        self.animator.update(dt)
        if self.word_x <= 70:
            self.finish()

    def finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        self.game.complete_game(
            GameResult(
                game_id="typing",
                title="吠えるタイピング",
                score=self.score,
                unit="点",
                is_clear=None,
            )
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((218, 239, 247))
        for x, y, radius in [(130, 150, 90), (1110, 135, 120), (1040, 590, 170), (230, 610, 145)]:
            pygame.draw.circle(surface, (232, 247, 247), (x, y), radius)
        pygame.draw.line(surface, config.MINT_DARK, (72, 155), (72, 410), 5)
        draw_text(surface, "ここまで来る前に入力！", self.assets.font(18, True), config.MINT_DARK, (85, 173))

        word_font = self.assets.font(54, True)
        word_rect = draw_text(surface, self.word, word_font, config.INK, (int(self.word_x), self.word_y))
        pygame.draw.line(surface, config.PEACH, (word_rect.left, word_rect.bottom + 8), (word_rect.right, word_rect.bottom + 8), 5)
        panel = pygame.Rect(350, 430, 580, 105)
        draw_panel(surface, panel)
        shown_input = self.input_text or "入力してください"
        input_color = config.INK if self.input_text else config.MUTED_INK
        if self.error_time > 0:
            input_color = config.ERROR
        draw_text(surface, shown_input, self.assets.font(35, True), input_color, panel.center, center=True)
        if self.error_time > 0:
            pygame.draw.rect(surface, config.ERROR, panel, width=4, border_radius=24)
            draw_text(surface, "入力ミス　Backspaceで直そう", self.assets.font(18, True), config.ERROR, (640, 552), center=True)

        self.animator.draw(surface, self.assets, 175, (640, 710))
        if self.bark_time > 0:
            draw_text(surface, "ワン！", self.assets.font(26, True), config.PEACH_DARK, (745, 560))
        self.draw_game_header(surface, "吠えるタイピング", f"{self.score} 点")
        draw_text(surface, "英字入力　Backspace：修正", self.assets.font(19), config.MUTED_INK, (900, 655))
        self.draw_exit_overlay(surface)
