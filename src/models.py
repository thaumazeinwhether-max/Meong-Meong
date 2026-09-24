"""Small data objects shared by screens, games, and database code."""

from dataclasses import dataclass


@dataclass
class UserProgress:
    nosework_unlocked: bool = False
    tug_unlocked: bool = False
    ball_unlocked: bool = False
    walk_best: int | None = None
    typing_best: int | None = None
    catch_best: int | None = None


@dataclass
class UserSession:
    user_id: int
    login_name: str
    nickname: str | None
    progress: UserProgress


@dataclass
class GameResult:
    game_id: str
    title: str
    score: int
    unit: str
    is_clear: bool | None
    best_score: int | None = None
    is_new_best: bool = False
    unlocked_play: str | None = None


@dataclass
class SaveResult:
    progress: UserProgress
    best_updated: bool
    newly_unlocked: str | None

