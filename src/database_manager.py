"""SQLite persistence for accounts, progress, and per-user best scores."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from src.auth_service import AuthService
from src.game_rules import unlock_for_result
from src.models import SaveResult, UserProgress, UserSession


class DuplicateUserError(ValueError):
    """Raised when a login name already exists."""


class DatabaseManager:
    BEST_COLUMNS = {
        "walk": "walk_best",
        "typing": "typing_best",
        "catch": "catch_best",
    }
    UNLOCK_COLUMNS = {
        "nosework": "nosework_unlocked",
        "tug": "tug_unlocked",
        "ball": "ball_unlocked",
    }

    def __init__(self, database_path: str | Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Commit or roll back a unit of work, then always close its file handle."""
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    login_name TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    nickname TEXT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS user_progress (
                    user_id INTEGER PRIMARY KEY,
                    nosework_unlocked INTEGER NOT NULL DEFAULT 0 CHECK (nosework_unlocked IN (0, 1)),
                    tug_unlocked INTEGER NOT NULL DEFAULT 0 CHECK (tug_unlocked IN (0, 1)),
                    ball_unlocked INTEGER NOT NULL DEFAULT 0 CHECK (ball_unlocked IN (0, 1)),
                    walk_best INTEGER NULL CHECK (walk_best IS NULL OR walk_best >= 0),
                    typing_best INTEGER NULL CHECK (typing_best IS NULL OR typing_best >= 0),
                    catch_best INTEGER NULL CHECK (catch_best IS NULL OR catch_best >= 0),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )

    def register_user(self, login_name: str, password: str) -> UserSession:
        login_name = login_name.strip()
        error = AuthService.validate_login_name(login_name) or AuthService.validate_password(password)
        if error:
            raise ValueError(error)
        password_hash = AuthService.hash_password(password)
        try:
            with self.connection() as connection:
                cursor = connection.execute(
                    "INSERT INTO users (login_name, password_hash) VALUES (?, ?)",
                    (login_name, password_hash),
                )
                user_id = int(cursor.lastrowid)
                connection.execute(
                    "INSERT INTO user_progress (user_id) VALUES (?)",
                    (user_id,),
                )
        except sqlite3.IntegrityError as error_detail:
            if "UNIQUE" in str(error_detail).upper():
                raise DuplicateUserError("そのユーザー名はすでに使用されています。") from error_detail
            raise
        return self.load_session(user_id)

    def authenticate(self, login_name: str, password: str) -> UserSession | None:
        if not login_name or not password:
            return None
        with self.connection() as connection:
            row = connection.execute(
                "SELECT id, password_hash FROM users WHERE login_name = ?",
                (login_name.strip(),),
            ).fetchone()
        if row is None or not AuthService.verify_password(password, row["password_hash"]):
            return None
        return self.load_session(int(row["id"]))

    def set_nickname(self, user_id: int, nickname: str) -> UserSession:
        nickname = nickname.strip()
        if not 1 <= len(nickname) <= 10:
            raise ValueError("ニックネームは1〜10文字で入力してください。")
        with self.connection() as connection:
            cursor = connection.execute(
                "UPDATE users SET nickname = ? WHERE id = ?",
                (nickname, user_id),
            )
            if cursor.rowcount != 1:
                raise ValueError("ユーザーが見つかりません。")
        return self.load_session(user_id)

    def load_session(self, user_id: int) -> UserSession:
        with self.connection() as connection:
            row = connection.execute(
                """
                SELECT u.id, u.login_name, u.nickname,
                       p.nosework_unlocked, p.tug_unlocked, p.ball_unlocked,
                       p.walk_best, p.typing_best, p.catch_best
                FROM users AS u
                JOIN user_progress AS p ON p.user_id = u.id
                WHERE u.id = ?
                """,
                (user_id,),
            ).fetchone()
        if row is None:
            raise ValueError("ユーザーデータが見つかりません。")
        return UserSession(
            user_id=int(row["id"]),
            login_name=str(row["login_name"]),
            nickname=row["nickname"],
            progress=self._progress_from_row(row),
        )

    def save_game_result(self, user_id: int, game_id: str, score: int) -> SaveResult:
        if game_id not in self.BEST_COLUMNS:
            raise ValueError(f"Unknown game id: {game_id}")
        score = max(0, int(score))
        best_column = self.BEST_COLUMNS[game_id]
        requested_unlock = unlock_for_result(game_id, score)
        newly_unlocked: str | None = None
        best_updated = False

        with self.connection() as connection:
            row = connection.execute(
                f"SELECT {best_column} FROM user_progress WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if row is None:
                raise ValueError("進行データが見つかりません。")

            current_best = row[best_column]
            if current_best is None or score > int(current_best):
                connection.execute(
                    f"UPDATE user_progress SET {best_column} = ? WHERE user_id = ?",
                    (score, user_id),
                )
                best_updated = True

            if requested_unlock is not None:
                unlock_column = self.UNLOCK_COLUMNS[requested_unlock]
                cursor = connection.execute(
                    f"""
                    UPDATE user_progress
                    SET {unlock_column} = 1
                    WHERE user_id = ? AND {unlock_column} = 0
                    """,
                    (user_id,),
                )
                if cursor.rowcount == 1:
                    newly_unlocked = requested_unlock

        # Loading after the transaction verifies the saved state before the UI
        # is allowed to show an unlock animation.
        session = self.load_session(user_id)
        return SaveResult(session.progress, best_updated, newly_unlocked)

    def _progress_from_row(self, row: sqlite3.Row) -> UserProgress:
        return UserProgress(
            nosework_unlocked=bool(row["nosework_unlocked"]),
            tug_unlocked=bool(row["tug_unlocked"]),
            ball_unlocked=bool(row["ball_unlocked"]),
            walk_best=row["walk_best"],
            typing_best=row["typing_best"],
            catch_best=row["catch_best"],
        )
