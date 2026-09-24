"""Quiet room routines. Random choices happen only after returning to idle."""

import random

from src.animation import CharacterAnimator


class RoomBehavior:
    WALK_SPEED = 72.0
    LEFT_LIMIT = 410.0
    RIGHT_LIMIT = 860.0

    def __init__(self, animator: CharacterAnimator, random_source=None):
        self.animator = animator
        self.random = random_source or random.Random()
        self.x = 650.0
        self.target_x = self.x
        self.facing_right = True
        self.state = "idle"
        self.elapsed = 0.0
        self.speed = 0.0
        self.duration = self.random.uniform(4.5, 8.0)
        self.idle_requested = False

    def enter(self, state: str):
        self.state = state
        self.elapsed = 0.0
        self.animator.play(state, force=True)
        if state == "idle":
            self.duration = self.random.uniform(4.5, 8.0)
        elif state == "sit":
            self.duration = self.random.uniform(3.0, 6.0)
        elif state == "rest":
            self.duration = self.random.uniform(7.0, 12.0)

    def choose(self):
        if self.state != "idle":
            return
        choice = self.random.choices(
            ["blink", "tail", "walk", "sit_down", "lie_down"],
            [35, 25, 20, 12, 8],
        )[0]
        if choice == "walk":
            targets = [x for x in (410.0, 540.0, 700.0, 860.0) if abs(x - self.x) > 90]
            self.target_x = self.random.choice(targets)
            self.facing_right = self.target_x > self.x
            self.speed = 0.0
        self.enter(choice)

    def update(self, dt: float, size: int = 330):
        self.elapsed += dt
        travelled = 0.0
        if self.state == "walk":
            remaining = abs(self.target_x - self.x)
            # Ease in and out, but advance gait by actual distance, not this timer.
            desired_speed = min(self.WALK_SPEED, max(12.0, remaining * 2.5))
            self.speed = min(desired_speed, self.speed + 180 * dt)
            travelled = min(remaining, self.speed * dt)
            self.x += travelled if self.facing_right else -travelled
            self.x = max(self.LEFT_LIMIT, min(self.RIGHT_LIMIT, self.x))
            self.animator.update(dt, travel=travelled, size=size)
            if remaining <= travelled + 0.01:
                self.x = self.target_x
                self.enter("stop")
            return

        self.animator.update(dt)
        if self.state == "idle":
            if self.elapsed >= self.duration and not self.idle_requested:
                self.choose()
        elif self.state in {"blink", "tail", "stop", "wake", "stand"}:
            if self.state in self.animator.completed:
                self.enter("idle")
        elif self.state == "sit_down" and "sit_down" in self.animator.completed:
            self.enter("sit")
        elif self.state == "sit" and (self.idle_requested or self.elapsed >= self.duration):
            self.enter("stand")
        elif self.state == "lie_down" and "lie_down" in self.animator.completed:
            self.enter("rest")
        elif self.state == "rest" and (self.idle_requested or self.elapsed >= self.duration):
            self.enter("wake")
