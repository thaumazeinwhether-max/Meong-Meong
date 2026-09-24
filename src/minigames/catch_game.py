"""Thirty-second treat-catching game."""

from dataclasses import dataclass
import random

import pygame

from src import config
from src.animation import CharacterAnimator, KURUM_CLIPS
from src.components import draw_pooh, draw_text, draw_treat
from src.game_rules import apply_catch_item, catch_is_clear
from src.minigames.base import BaseMinigame
from src.minigames.difficulty import catch_difficulty
from src.models import GameResult


@dataclass
class FallingItem:
    x: float
    y: float
    speed: float
    is_treat: bool
    size: int = 46

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.size / 2), int(self.y - self.size / 2), self.size, self.size)


class CatchGame(BaseMinigame):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.dog_x = float(config.SCREEN_WIDTH / 2)
        self.elapsed = 0.0
        self.spawn_timer = random.uniform(0.55, 0.95)
        self.score = 0
        self.items: list[FallingItem] = []
        self.reaction = ""
        self.reaction_time = 0.0
        self.facing_right = True
        self.animator = CharacterAnimator(KURUM_CLIPS, "idle")
        self.finished = False

    def handle_event(self, event: pygame.event.Event) -> None:
        self.handle_common_event(event)

    def update(self, dt: float) -> None:
        if self.exit_overlay or self.finished:
            return
        keys = pygame.key.get_pressed()
        direction = int(keys[pygame.K_RIGHT]) - int(keys[pygame.K_LEFT])
        previous_x = self.dog_x
        self.dog_x += direction * config.CATCH_DOG_SPEED * dt
        self.dog_x = max(90, min(config.SCREEN_WIDTH - 90, self.dog_x))
        if direction:
            self.facing_right = direction > 0
            if self.reaction_time <= 0.12:
                self.animator.play("walk")
        elif self.reaction_time <= 0.12:
            self.animator.play("idle")

        self.elapsed += dt
        self.spawn_timer -= dt
        self.reaction_time = max(0.0, self.reaction_time - dt)
        self.animator.update(dt, travel=abs(self.dog_x - previous_x), size=165)
        if self.spawn_timer <= 0:
            self.spawn_item()

        dog_rect = pygame.Rect(int(self.dog_x - 39), 585, 78, 74)
        remaining: list[FallingItem] = []
        for item in self.items:
            item.y += item.speed * dt
            if item.rect.colliderect(dog_rect):
                self.score = apply_catch_item(self.score, item.is_treat)
                self.reaction = "+1" if item.is_treat else "-1"
                self.reaction_time = 0.45
                self.animator.play("catch_eat" if item.is_treat else "blink", restart=True, force=True)
                self.assets.sounds.play("treat" if item.is_treat else "bad", minimum_interval_ms=120)
            elif item.y < config.SCREEN_HEIGHT + 40:
                remaining.append(item)
        self.items = remaining

        if self.elapsed >= config.CATCH_TIME_LIMIT_SECONDS:
            self.finish()

    def spawn_item(self) -> FallingItem:
        """Spawn one independently timed item away from a fresh top-edge cluster."""
        difficulty = catch_difficulty(self.elapsed)
        x = random.uniform(70, config.SCREEN_WIDTH - 70)
        fresh_items = [item for item in self.items if item.y < 170]
        for _ in range(8):
            if all(abs(item.x - x) >= config.CATCH_MIN_SPAWN_X_DISTANCE for item in fresh_items):
                break
            x = random.uniform(70, config.SCREEN_WIDTH - 70)
        item = FallingItem(
            x=x,
            y=-28,
            speed=random.uniform(difficulty.fall_speed_min, difficulty.fall_speed_max),
            is_treat=random.random() < difficulty.treat_chance,
        )
        self.items.append(item)
        self.spawn_timer = random.uniform(difficulty.interval_min, difficulty.interval_max)
        return item

    def finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        self.game.complete_game(
            GameResult(
                game_id="catch",
                title="おやつキャッチ",
                score=self.score,
                unit="点",
                is_clear=catch_is_clear(self.score),
            )
        )

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((246, 226, 210))
        pygame.draw.rect(surface, (222, 240, 220), (0, 390, config.SCREEN_WIDTH, 330))
        for x in range(0, config.SCREEN_WIDTH, 90):
            pygame.draw.circle(surface, (207, 229, 202), (x + 40, 590), 110)
        for item in self.items:
            center = (int(item.x), int(item.y))
            if item.is_treat:
                draw_treat(surface, center, item.size)
            else:
                draw_pooh(surface, center, item.size)

        self.animator.draw(surface, self.assets, 165, (self.dog_x, 680), self.facing_right)
        if self.reaction_time > 0:
            color = config.SUCCESS if self.reaction == "+1" else config.ERROR
            draw_text(surface, self.reaction, self.assets.font(34, True), color, (int(self.dog_x), 525), center=True)

        remaining = max(0.0, config.CATCH_TIME_LIMIT_SECONDS - self.elapsed)
        self.draw_game_header(surface, "おやつキャッチ", f"{self.score} 点　残り {remaining:04.1f} 秒")
        draw_text(surface, "← →：移動", self.assets.font(22, True), config.WHITE, (1090, 660))
        self.draw_exit_overlay(surface)
