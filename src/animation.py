"""Small time-based animation system shared by every Kurum scene."""

from dataclasses import dataclass
import math

import pygame

from src.sprite_layout import layout_for, should_flip


@dataclass(frozen=True)
class SpriteFrame:
    sheet: str
    row: int
    column: int
    offset: tuple[float, float] = (0.0, 0.0)


@dataclass(frozen=True)
class AnimationClip:
    frames: tuple[SpriteFrame, ...]
    frame_duration: float
    loop: bool = True
    next_state: str | None = None
    stride: float = 0.0  # Travel per cycle as a fraction of rendered sprite size.

    def __post_init__(self) -> None:
        if not self.frames or self.frame_duration <= 0:
            raise ValueError("An animation needs frames and a positive duration")

    @property
    def duration(self) -> float:
        return len(self.frames) * self.frame_duration


class CharacterAnimator:
    """Advance named clips by elapsed seconds rather than rendered frame count."""

    def __init__(self, clips: dict[str, AnimationClip], initial_state: str) -> None:
        if initial_state not in clips:
            raise ValueError(f"Unknown initial animation: {initial_state}")
        self.clips = clips
        self.state = initial_state
        self.frame_index = 0
        self.frame_elapsed = 0.0
        self.finished = False
        self.pending_state: str | None = None
        self.completed: list[str] = []
        self.total_elapsed = 0.0

    def play(self, state: str, restart: bool = False, force: bool = False) -> None:
        if state not in self.clips:
            raise ValueError(f"Unknown animation: {state}")
        if state == self.state and not restart:
            return
        # Reactions finish before queued requests; jumping/input response can
        # explicitly override this rule with force=True.
        if not force and not self.clips[self.state].loop and not self.finished:
            self.pending_state = state
            return
        self._start(state)

    def _start(self, state: str) -> None:
        self.state = state
        self.frame_index = 0
        self.frame_elapsed = 0.0
        self.finished = False
        self.pending_state = None

    def update(self, elapsed_seconds: float, travel: float | None = None, size: int = 330) -> None:
        self.completed = []
        self.total_elapsed += max(0.0, elapsed_seconds)
        clip = self.clips[self.state]
        advance = max(0.0, elapsed_seconds)
        if clip.stride and travel is not None:
            advance = abs(travel) / (clip.stride * size) * clip.duration
        self.frame_elapsed += advance
        while self.frame_elapsed + 1e-10 >= clip.frame_duration and not self.finished:
            self.frame_elapsed -= clip.frame_duration
            self.frame_elapsed = max(0.0, self.frame_elapsed)
            next_index = self.frame_index + 1
            if next_index < len(clip.frames):
                self.frame_index = next_index
            elif clip.loop:
                self.frame_index = 0
            else:
                self.completed.append(self.state)
                next_state = self.pending_state or clip.next_state
                if next_state is None:
                    self.frame_index = len(clip.frames) - 1
                    self.finished = True
                    self.frame_elapsed = 0.0
                else:
                    remainder = self.frame_elapsed
                    self._start(next_state)
                    self.frame_elapsed = remainder
                    clip = self.clips[self.state]

    @property
    def current_frame(self) -> SpriteFrame:
        return self.clips[self.state].frames[self.frame_index]

    def image(self, assets, size: int, facing_right: bool = True) -> pygame.Surface:
        frame = self.current_frame
        flip = should_flip(layout_for(frame.sheet, frame.row, frame.column), facing_right)
        return assets.kurum_frame(frame.sheet, frame.row, frame.column, size, flip)

    def draw(self, surface, assets, size: int, foot: tuple[float, float], facing_right: bool = True):
        """Every screen supplies the same physical support point, not a top-left."""
        frame = self.current_frame
        image = self.image(assets, size, facing_right)
        dx, dy = frame.offset
        # Subpixel breathing only moves 0.4px at room scale, never changes the face.
        if self.state in {"idle", "rest", "sit"}:
            dy += math.sin(self.total_elapsed * 1.6) * 0.0012
        x = round(foot[0] - size / 2 + dx * size)
        y = round(foot[1] - size * 0.94 + dy * size)
        return surface.blit(image, (x, y))


def M(row, column, offset=(0.0, 0.0)):
    return SpriteFrame("motion", row, column, offset)


def A(row, column, offset=(0.0, 0.0)):
    return SpriteFrame("action", row, column, offset)


def G(row, column):
    return SpriteFrame("gait", row, column)


def R(row, column):
    return SpriteFrame("rest", row, column)


KURUM_CLIPS = {
    "idle": AnimationClip((M(0, 0),), 1.0),
    "blink": AnimationClip((M(0, 1), M(0, 1), M(0, 0)), 0.08, False, "idle"),
    "tail": AnimationClip((M(0, 0), M(0, 2), M(0, 0), M(0, 2), M(0, 0)), 0.18, False, "idle"),
    "happy": AnimationClip((M(2, 3),) * 5, 0.20, False, "idle"),
    "sit_down": AnimationClip((M(0, 0), M(0, 3)), 0.3, False, "sit"),
    "sit": AnimationClip((M(0, 3),), 1.0),
    "lie_down": AnimationClip((M(0, 0), R(0, 1), R(1, 0)), 0.30, False, "rest"),
    "rest": AnimationClip((R(1, 1),), 1.0),
    "wake": AnimationClip((R(1, 0), R(0, 1), M(0, 0)), 0.32, False, "idle"),
    "stand": AnimationClip((M(0, 3), M(0, 0)), 0.26, False, "idle"),
    "walk": AnimationClip((G(0, 0), G(0, 1), G(1, 0), G(1, 1)), 0.22, stride=0.26),
    "run": AnimationClip((G(0, 0), G(0, 1), G(1, 0), G(1, 1)), 0.09, stride=1.05),
    "stop": AnimationClip((G(1, 1), G(0, 1)), 0.18, False, "idle"),
    "takeoff": AnimationClip((G(0, 1), M(1, 3)), 0.045, False, "jump_rise"),
    "jump_rise": AnimationClip((M(1, 3),), 0.1),
    "jump_air": AnimationClip((M(2, 0),), 0.1),
    "jump_fall": AnimationClip((M(2, 0),), 0.1),
    "land": AnimationClip((M(2, 1), G(0, 1)), 0.09, False, "run"),
    "eat": AnimationClip((M(2, 2), M(2, 2, (0, 0.004)), M(2, 2), M(2, 2, (0, -0.003))) * 3, 0.20, False),
    "catch_eat": AnimationClip((M(2, 3), M(0, 1), M(0, 0)), 0.075, False),
    "pet_happy": AnimationClip((A(0, 0),) * 4, 0.28, False),
    "belly": AnimationClip((A(0, 1),) * 4, 0.35, False),
    "sniff": AnimationClip((A(0, 2), A(0, 2, (0.003, 0.002))), 0.30),
    "found": AnimationClip((A(0, 3),) * 4, 0.25, False),
    "tug_bite": AnimationClip((A(1, 0),), 0.70, False),
    "tug_pull": AnimationClip((A(1, 0), A(1, 1), A(1, 0), A(1, 2)), 0.50),
    "tug_win": AnimationClip((A(1, 3),) * 4, 0.25, False),
    "watch_ball": AnimationClip((M(0, 0),), 0.3),
    "chase_ball": AnimationClip((G(0, 0), G(0, 1), G(1, 0), G(1, 1)), 0.16, stride=0.35),
    "carry_ball": AnimationClip((A(2, 2),), 0.30),
    "bark": AnimationClip((M(0, 0), A(2, 3), A(2, 3), M(0, 0)), 0.09, False, "idle"),
}
