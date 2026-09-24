"""Progressively harder, always-avoidable Space-key jump game."""

from dataclasses import dataclass
import random

import pygame

from src import config
from src.animation import CharacterAnimator, KURUM_CLIPS
from src.components import draw_text
from src.game_rules import walk_distance_meters
from src.minigames.base import BaseMinigame
from src.minigames.difficulty import (
    generate_walk_pattern,
    pattern_is_avoidable,
    safe_next_pattern_distance,
    walk_difficulty,
)
from src.models import GameResult


@dataclass
class Obstacle:
    x: float
    width: int
    height: int
    kind: str

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), config.WALK_GROUND_Y - self.height, self.width, self.height)


class WalkGame(BaseMinigame):
    def __init__(self, game) -> None:
        super().__init__(game)
        self.dog_y = float(config.WALK_GROUND_Y - config.WALK_DOG_SIZE)
        self.velocity_y = 0.0
        self.on_ground = True
        self.animator = CharacterAnimator(KURUM_CLIPS, "run")
        self.distance_pixels = 0.0
        self.speed = config.WALK_START_SPEED
        self.background_x = 0.0
        self.obstacles: list[Obstacle] = []
        self.distance_until_pattern = 620.0
        self.finished = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.handle_common_event(event):
            return
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and self.on_ground:
            self.velocity_y = config.WALK_JUMP_SPEED
            self.on_ground = False
            self.animator.play("takeoff", restart=True, force=True)
            self.assets.sounds.play("jump")

    def update(self, dt: float) -> None:
        if self.exit_overlay or self.finished:
            return
        meters = walk_distance_meters(self.distance_pixels)
        difficulty = walk_difficulty(meters)
        self.speed = difficulty.speed
        moved = self.speed * dt
        self.distance_pixels += moved
        self.background_x = (self.background_x - moved * 0.18) % config.SCREEN_WIDTH

        self.velocity_y += config.WALK_GRAVITY * dt
        self.dog_y += self.velocity_y * dt
        ground_top = config.WALK_GROUND_Y - config.WALK_DOG_SIZE
        landed = not self.on_ground and self.dog_y >= ground_top
        if self.dog_y >= ground_top:
            self.dog_y = float(ground_top)
            self.velocity_y = 0.0
            self.on_ground = True
            if landed:
                self.animator.play("land", restart=True, force=True)
        elif self.animator.state != "takeoff":
            if abs(self.velocity_y) < 80:
                state = "jump_air"
            elif self.velocity_y < 0:
                state = "jump_rise"
            else:
                state = "jump_fall"
            self.animator.play(state, force=True)
        self.animator.update(dt, travel=moved, size=config.WALK_DOG_SIZE)

        self.distance_until_pattern -= moved
        if self.distance_until_pattern <= 0:
            self._spawn_pattern(meters)
        for obstacle in self.obstacles:
            obstacle.x -= moved
        self.obstacles = [item for item in self.obstacles if item.rect.right > -30]

        dog_collision = pygame.Rect(config.WALK_DOG_X + 38, int(self.dog_y) + 55, 74, 82)
        if any(dog_collision.colliderect(item.rect) for item in self.obstacles):
            self.finish()

    def _spawn_pattern(self, distance_meters: int) -> None:
        pattern = generate_walk_pattern(distance_meters)
        difficulty = walk_difficulty(distance_meters)
        if not pattern_is_avoidable(pattern, difficulty.speed):
            pattern = generate_walk_pattern(0)
        start_x = config.SCREEN_WIDTH + 50
        for spec in pattern:
            self.obstacles.append(Obstacle(start_x + spec.offset, spec.width, spec.height, spec.kind))
        safe_distance = safe_next_pattern_distance(pattern, difficulty)
        self.distance_until_pattern = safe_distance + random.randint(0, config.WALK_PATTERN_GAP_VARIATION)

    def finish(self) -> None:
        if self.finished:
            return
        self.finished = True
        final_meters = walk_distance_meters(self.distance_pixels)
        self.game.complete_game(GameResult("walk", "お散歩ジャンプ", final_meters, "m", None))

    def draw(self, surface: pygame.Surface) -> None:
        background = self.assets.walk_background()
        x = int(self.background_x)
        surface.blit(background, (x - config.SCREEN_WIDTH, 0))
        surface.blit(background, (x, 0))
        pygame.draw.rect(surface, (205, 166, 110), (0, config.WALK_GROUND_Y, config.SCREEN_WIDTH, 130))
        pygame.draw.rect(surface, (237, 207, 151), (0, config.WALK_GROUND_Y, config.SCREEN_WIDTH, 15))
        for obstacle in self.obstacles:
            self._draw_obstacle(surface, obstacle)
        # Obstacles move left: the dog advances right in every physical phase.
        self.animator.draw(surface, self.assets, config.WALK_DOG_SIZE,
                           (config.WALK_DOG_X + config.WALK_DOG_SIZE / 2,
                            self.dog_y + config.WALK_DOG_SIZE), facing_right=True)
        meters = walk_distance_meters(self.distance_pixels)
        self.draw_game_header(surface, "お散歩ジャンプ", f"{meters} m")
        draw_text(surface, "Space：ジャンプ", self.assets.font(22, True), config.WHITE, (1030, 655))
        self.draw_exit_overlay(surface)

    def _draw_obstacle(self, surface: pygame.Surface, obstacle: Obstacle) -> None:
        rect = obstacle.rect
        if obstacle.kind == "cone":
            pygame.draw.polygon(surface, (236, 119, 79), [(rect.centerx, rect.top), (rect.left + 4, rect.bottom), (rect.right - 4, rect.bottom)])
            pygame.draw.rect(surface, (255, 230, 185), (rect.left + 10, rect.centery, max(8, rect.width - 20), 10), border_radius=4)
            pygame.draw.rect(surface, (173, 88, 64), (rect.left, rect.bottom - 9, rect.width, 9), border_radius=4)
        else:
            pygame.draw.rect(surface, (94, 115, 73), (rect.centerx - 5, rect.centery, 10, rect.height // 2))
            radius = max(13, min(25, rect.height // 3))
            for dx, dy in [(-rect.width // 4, 8), (0, 0), (rect.width // 4, 12)]:
                pygame.draw.circle(surface, (94, 165, 91), (rect.centerx + dx, rect.top + dy + radius), radius)
