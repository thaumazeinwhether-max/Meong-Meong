"""Tests for account and per-user SQLite persistence."""

import sqlite3
from contextlib import closing
from pathlib import Path
from uuid import uuid4

import pytest

from src.database_manager import DatabaseManager, DuplicateUserError


@pytest.fixture
def database() -> DatabaseManager:
    """Use a workspace-local database because this Windows host blocks pytest's temp ACLs."""
    database_path = Path("data") / f"test_{uuid4().hex}.db"
    manager = DatabaseManager(database_path)
    try:
        yield manager
    finally:
        database_path.unlink(missing_ok=True)


def test_database_initializes_required_tables(database: DatabaseManager) -> None:
    with closing(database.connect()) as connection:
        names = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
    assert {"users", "user_progress"}.issubset(names)


def test_registration_creates_null_bests_and_password_is_not_plaintext(
    database: DatabaseManager,
) -> None:
    session = database.register_user("kurum_fan", "secret12")
    assert session.progress.walk_best is None
    assert session.progress.typing_best is None
    assert session.progress.catch_best is None
    assert session.progress.nosework_unlocked is False

    with closing(database.connect()) as connection:
        stored = connection.execute(
            "SELECT password_hash FROM users WHERE id = ?", (session.user_id,)
        ).fetchone()["password_hash"]
    assert stored != "secret12"
    assert "secret12" not in stored


def test_authentication_and_duplicate_registration(database: DatabaseManager) -> None:
    registered = database.register_user("student01", "password1")
    authenticated = database.authenticate("student01", "password1")
    assert authenticated is not None
    assert authenticated.user_id == registered.user_id
    assert database.authenticate("student01", "wrongpass") is None
    assert database.authenticate("missing", "password1") is None
    with pytest.raises(DuplicateUserError):
        database.register_user("student01", "password1")


def test_nickname_is_saved(database: DatabaseManager) -> None:
    user = database.register_user("nickname_user", "password1")
    updated = database.set_nickname(user.user_id, "くるむ")
    assert updated.nickname == "くるむ"
    assert database.load_session(user.user_id).nickname == "くるむ"


def test_best_score_only_updates_when_higher(database: DatabaseManager) -> None:
    user = database.register_user("best_user", "password1")
    first = database.save_game_result(user.user_id, "typing", 7)
    lower = database.save_game_result(user.user_id, "typing", 3)
    higher = database.save_game_result(user.user_id, "typing", 9)
    assert first.best_updated is True
    assert lower.best_updated is False
    assert lower.progress.typing_best == 7
    assert higher.best_updated is True
    assert higher.progress.typing_best == 9


@pytest.mark.parametrize(
    ("game_id", "below", "threshold", "play_id"),
    [
        ("walk", 499, 500, "nosework"),
        ("typing", 9, 10, "tug"),
        ("catch", 14, 15, "ball"),
    ],
)
def test_unlock_boundaries_and_unlock_only_once(
    database: DatabaseManager,
    game_id: str,
    below: int,
    threshold: int,
    play_id: str,
) -> None:
    user = database.register_user(f"{game_id}_user", "password1")
    assert database.save_game_result(user.user_id, game_id, below).newly_unlocked is None
    unlocked = database.save_game_result(user.user_id, game_id, threshold)
    assert unlocked.newly_unlocked == play_id
    assert getattr(unlocked.progress, f"{play_id}_unlocked") is True
    repeated = database.save_game_result(user.user_id, game_id, threshold + 1)
    assert repeated.newly_unlocked is None
    assert getattr(repeated.progress, f"{play_id}_unlocked") is True


def test_progress_is_isolated_between_users(database: DatabaseManager) -> None:
    first = database.register_user("first_user", "password1")
    second = database.register_user("second_user", "password2")
    database.save_game_result(first.user_id, "walk", 500)
    first_loaded = database.load_session(first.user_id)
    second_loaded = database.load_session(second.user_id)
    assert first_loaded.progress.walk_best == 500
    assert first_loaded.progress.nosework_unlocked is True
    assert second_loaded.progress.walk_best is None
    assert second_loaded.progress.nosework_unlocked is False


def test_foreign_keys_are_enabled(database: DatabaseManager) -> None:
    with closing(database.connect()) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("INSERT INTO user_progress (user_id) VALUES (99999)")
