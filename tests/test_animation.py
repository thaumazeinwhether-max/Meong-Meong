"""Tests for elapsed-time character animation behavior."""

from src.animation import AnimationClip, CharacterAnimator, SpriteFrame


FRAME_1 = SpriteFrame("test", 0, 0)
FRAME_2 = SpriteFrame("test", 0, 1)


def test_animation_advances_using_elapsed_time() -> None:
    animator = CharacterAnimator({"idle": AnimationClip((FRAME_1, FRAME_2), 0.2)}, "idle")
    animator.update(0.19)
    assert animator.current_frame == FRAME_1
    animator.update(0.02)
    assert animator.current_frame == FRAME_2


def test_looping_animation_wraps_to_first_frame() -> None:
    animator = CharacterAnimator({"walk": AnimationClip((FRAME_1, FRAME_2), 0.1)}, "walk")
    animator.update(0.21)
    assert animator.current_frame == FRAME_1
    assert animator.finished is False


def test_one_shot_animation_finishes_on_last_frame() -> None:
    animator = CharacterAnimator({"reaction": AnimationClip((FRAME_1, FRAME_2), 0.1, False)}, "reaction")
    animator.update(0.25)
    assert animator.current_frame == FRAME_2
    assert animator.finished is True


def test_one_shot_can_transition_to_another_state() -> None:
    animator = CharacterAnimator(
        {
            "blink": AnimationClip((FRAME_2,), 0.1, False, "idle"),
            "idle": AnimationClip((FRAME_1,), 0.3),
        },
        "blink",
    )
    animator.update(0.11)
    assert animator.state == "idle"
    assert animator.current_frame == FRAME_1

