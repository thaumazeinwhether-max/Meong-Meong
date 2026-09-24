"""State-machine checks for room feeding and unlocked play sequences."""

from src.models import UserProgress, UserSession
from src.screens.home_screens import PlaySelectScreen, RoomScreen


class DummySound:
    def play(self) -> None:
        return None


class DummySounds:
    def play(self, _name: str, minimum_interval_ms: int = 0) -> bool:
        return True


class DummyAssets:
    def __init__(self) -> None:
        self.sounds = DummySounds()

    def sound(self, _name: str) -> DummySound:
        return DummySound()


class DummyGame:
    def __init__(self) -> None:
        self.assets = DummyAssets()
        self.changed_to: str | None = None
        self.current_user = UserSession(
            1,
            "tester",
            "クルム",
            UserProgress(True, True, True),
        )

    def change_screen(self, name: str) -> None:
        self.changed_to = name


def test_feeding_runs_through_approach_eating_happy_and_returns_idle() -> None:
    room = RoomScreen(DummyGame())
    room.feed()
    visited = set()
    for _ in range(500):
        if room.feed_phase:
            visited.add(room.feed_phase)
        room.update(0.02)
    assert {"bowl", "approach", "eating", "happy"}.issubset(visited)
    assert room.feed_phase is None
    assert room.animator.state == "idle"


def test_every_play_sequence_finishes_back_in_room() -> None:
    for play_id in ("pet", "nosework", "tug", "ball"):
        game = DummyGame()
        screen = PlaySelectScreen(game)
        screen.start_play(play_id)
        for _ in range(300):
            screen.update(0.03)
            if game.changed_to:
                break
        assert game.changed_to == "room", play_id


def test_feed_request_waits_for_waking_instead_of_interrupting_rest() -> None:
    room = RoomScreen(DummyGame())
    room.routine.enter("rest")
    room.feed()
    assert room.feed_requested and room.feed_phase is None
    room.update(.02)
    assert room.routine.state == "wake" and room.feed_phase is None
    for _ in range(40):
        room.update(.02)
        assert room.feed_phase is None
    for _ in range(20):
        room.update(.02)
    assert room.feed_phase == "bowl"
    for _ in range(500):
        room.update(.02)
    assert room.feed_phase is None
    assert not room.feed_requested and not room.routine.idle_requested
