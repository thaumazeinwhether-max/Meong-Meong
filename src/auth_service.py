"""Password hashing and basic account validation."""

import hashlib
import hmac
import secrets


class AuthService:
    HASH_NAME = "sha256"
    ITERATIONS = 180_000
    SALT_BYTES = 16

    @staticmethod
    def validate_login_name(login_name: str) -> str | None:
        if not login_name:
            return "ユーザー名を入力してください。"
        if not 3 <= len(login_name) <= 20:
            return "ユーザー名は3〜20文字で入力してください。"
        if not all(character.isalnum() or character in "_-" for character in login_name):
            return "ユーザー名には英数字、_、-を使用できます。"
        return None

    @staticmethod
    def validate_password(password: str) -> str | None:
        if len(password) < 6:
            return "パスワードは6文字以上で入力してください。"
        if len(password) > 64:
            return "パスワードは64文字以内で入力してください。"
        return None

    @classmethod
    def hash_password(cls, password: str) -> str:
        salt = secrets.token_bytes(cls.SALT_BYTES)
        digest = hashlib.pbkdf2_hmac(
            cls.HASH_NAME,
            password.encode("utf-8"),
            salt,
            cls.ITERATIONS,
        )
        return f"pbkdf2_{cls.HASH_NAME}${cls.ITERATIONS}${salt.hex()}${digest.hex()}"

    @classmethod
    def verify_password(cls, password: str, stored_hash: str) -> bool:
        try:
            algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$")
            hash_name = algorithm.removeprefix("pbkdf2_")
            candidate = hashlib.pbkdf2_hmac(
                hash_name,
                password.encode("utf-8"),
                bytes.fromhex(salt_hex),
                int(iterations),
            )
        except (ValueError, TypeError):
            return False
        return hmac.compare_digest(candidate.hex(), digest_hex)

