"""Regression tests for support points, directions and unbroken motion phases."""

import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from src import config
from src.animation import AnimationClip, CharacterAnimator, KURUM_CLIPS, SpriteFrame
from src.asset_manager import AssetManager
from src.minigames.walk_game import WalkGame
from src.room_behavior import RoomBehavior
from src.sprite_layout import layout_for, should_flip


def test_transition_keeps_remainder_and_notifies_once():
    a, b = SpriteFrame("test", 0, 0), SpriteFrame("test", 0, 1)
    clips = {"once": AnimationClip((a,), .1, False, "loop"),
             "loop": AnimationClip((a, b), .1)}
    animator = CharacterAnimator(clips, "once")
    animator.update(.25)
    assert animator.state == "loop" and animator.current_frame == b
    assert animator.frame_elapsed == pytest.approx(.05)
    assert animator.completed == ["once"]
    animator.update(.01)
    assert animator.completed == []


def test_one_shot_queues_requests_instead_of_cutting_reaction():
    animator = CharacterAnimator(KURUM_CLIPS, "eat")
    animator.update(.5)
    animator.play("walk")
    assert animator.state == "eat"
    animator.update(1.9)
    assert animator.state == "walk"
    assert animator.completed == ["eat"]


def test_loop_is_independent_of_update_frequency():
    slow = CharacterAnimator(KURUM_CLIPS, "walk")
    fast = CharacterAnimator(KURUM_CLIPS, "walk")
    for _ in range(30):
        slow.update(1 / 30)
    for _ in range(144):
        fast.update(1 / 144)
    assert slow.frame_index == fast.frame_index
    assert slow.frame_elapsed == pytest.approx(fast.frame_elapsed)


def test_gait_advances_by_distance_and_stops_when_stationary():
    animator = CharacterAnimator(KURUM_CLIPS, "walk")
    animator.update(10, travel=0, size=330)
    assert animator.frame_index == 0
    animator.update(.01, travel=330 * KURUM_CLIPS["walk"].stride / 4, size=330)
    assert animator.frame_index == 1


@pytest.mark.parametrize("facing_right", [True, False])
def test_front_never_flips_but_side_obeys_requested_direction(facing_right):
    assert not should_flip(layout_for("motion", 0, 0), facing_right)
    assert should_flip(layout_for("gait", 0, 0), facing_right) == facing_right
    assert should_flip(layout_for("action", 1, 2), facing_right) != facing_right


def test_room_walk_stays_in_bounds_and_stops_before_idle():
    routine = RoomBehavior(CharacterAnimator(KURUM_CLIPS, "idle"), random.Random(7))
    for target in (410., 860.):
        routine.target_x = target
        routine.facing_right = target > routine.x
        routine.enter("walk")
        old_x = routine.x
        routine.update(.02)
        assert (routine.x > old_x) == routine.facing_right
        for _ in range(1000):
            routine.update(.02)
            assert 410 <= routine.x <= 860
            if routine.state != "walk":
                break
        assert routine.x == target and routine.state == "stop"
        routine.update(.4)
        assert routine.state == "idle"


def test_room_rest_must_wake_before_requested_idle():
    routine = RoomBehavior(CharacterAnimator(KURUM_CLIPS, "idle"), random.Random(7))
    routine.enter("lie_down")
    routine.update(.9)
    assert routine.state == "rest"
    routine.idle_requested = True
    routine.update(.01)
    assert routine.state == "wake"
    routine.update(.2)
    assert routine.state == "wake"
    routine.update(.8)
    assert routine.state == "idle"


class FakeSounds:
    def play(self, *args, **kwargs):
        return True


class FakeAssets:
    sounds = FakeSounds()

    def sound(self, _name):
        return self.sounds


class FakeGame:
    assets = FakeAssets()

    def complete_game(self, _result):
        raise AssertionError("No obstacle in this physics test")


@pytest.mark.parametrize("dt", [1 / 30, 1 / 60, 1 / 120, 1 / 144, .05])
def test_jump_physics_animation_landing_and_rightward_art(dt):
    walk = WalkGame(FakeGame())
    walk.distance_until_pattern = 1e9
    walk.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    seen = set()
    for _ in range(round(1.5 / dt)):
        walk.update(dt)
        state = walk.animator.state
        seen.add(state)
        frame = walk.animator.current_frame
        assert should_flip(layout_for(frame.sheet, frame.row, frame.column), True)
        if state in {"takeoff", "jump_rise"}:
            assert not walk.on_ground and walk.velocity_y < 0
        elif state == "jump_air":
            assert not walk.on_ground and abs(walk.velocity_y) < 80
        elif state == "jump_fall":
            assert not walk.on_ground and walk.velocity_y > 0
        else:
            assert walk.on_ground
            assert walk.dog_y + config.WALK_DOG_SIZE == config.WALK_GROUND_Y
    assert {"takeoff", "jump_rise", "jump_air", "jump_fall", "land", "run"} <= seen


def test_walk_draw_passes_rightward_direction_and_physical_foot(monkeypatch):
    pygame.init()
    surface = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    try:
        walk = WalkGame(FakeGame())
        walk.assets = AssetManager()
        requests = []

        def record_draw(surface, assets, size, foot, facing_right):
            requests.append((foot, facing_right))

        monkeypatch.setattr(walk.animator, "draw", record_draw)
        for state in ("run", "takeoff", "jump_rise", "jump_air", "jump_fall", "land"):
            walk.animator.play(state, force=True)
            walk.draw(surface)
            foot, facing_right = requests[-1]
            assert facing_right is True
            assert foot == (config.WALK_DOG_X + config.WALK_DOG_SIZE / 2,
                            walk.dog_y + config.WALK_DOG_SIZE)
    finally:
        pygame.quit()


def test_normalized_feet_and_scale_do_not_pulse_or_clip():
    pygame.init()
    pygame.display.set_mode((1, 1))
    try:
        assets = AssetManager()
        boxes = [assets.kurum_frame("gait", r, c, 330).get_bounding_rect()
                 for r in range(2) for c in range(2)]
        assert max(b.bottom for b in boxes) - min(b.bottom for b in boxes) <= 2
        assert max(b.height for b in boxes) - min(b.height for b in boxes) <= 3
        for state in ("idle", "blink", "walk", "jump_rise", "jump_air", "land", "rest"):
            for frame in KURUM_CLIPS[state].frames:
                for facing in (False, True):
                    flip = should_flip(layout_for(frame.sheet, frame.row, frame.column), facing)
                    box = assets.kurum_frame(frame.sheet, frame.row, frame.column, 330, flip).get_bounding_rect()
                    assert 0 < box.left < box.right < 330, (state, box)
                    assert 0 < box.top < box.bottom < 330, (state, box)
    finally:
        pygame.quit()


def test_draw_applies_foot_anchor_and_frame_offset():
    class Assets:
        def kurum_frame(self, sheet, row, column, size, flip):
            return pygame.Surface((size, size), pygame.SRCALPHA)
    frame = SpriteFrame("motion", 0, 0, (.03, -.02))
    animator = CharacterAnimator({"test": AnimationClip((frame,), 1)}, "test")
    surface = pygame.Surface((800, 600))
    rect = animator.draw(surface, Assets(), 100, (400, 300))
    assert rect.topleft == (353, 204)
