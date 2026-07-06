from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

import jwt

from app.core.config import Settings
from app.core.errors import AppError


@dataclass(frozen=True)
class TokenPair:
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105


@dataclass(frozen=True)
class TokenSubject:
    user_id: UUID
    token_type: str


class PasswordHasher:
    _algorithm = "pbkdf2_sha256"
    _iterations = 390_000

    def hash(self, password: str) -> str:
        self._validate_password(password)
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self._iterations,
        )
        return "$".join(
            [
                self._algorithm,
                str(self._iterations),
                base64.b64encode(salt).decode("ascii"),
                base64.b64encode(digest).decode("ascii"),
            ]
        )

    def verify(self, password: str, encoded_hash: str) -> bool:
        try:
            algorithm, iterations_text, salt_text, digest_text = encoded_hash.split("$", 3)
            if algorithm != self._algorithm:
                return False

            iterations = int(iterations_text)
            salt = base64.b64decode(salt_text.encode("ascii"))
            expected_digest = base64.b64decode(digest_text.encode("ascii"))
            actual_digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt,
                iterations,
            )
        except (ValueError, TypeError):
            return False

        return hmac.compare_digest(actual_digest, expected_digest)

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 12:
            raise AppError(
                code="auth.password_too_short",
                message="Password must be at least 12 characters.",
                status_code=422,
                details={},
            )


@dataclass(frozen=True)
class JwtTokenService:
    settings: Settings

    def issue_pair(self, user_id: UUID) -> TokenPair:
        return TokenPair(
            access_token=self._encode(user_id=user_id, token_type="access"),  # noqa: S106
            refresh_token=self._encode(user_id=user_id, token_type="refresh"),  # noqa: S106
        )

    def verify(self, token: str, expected_type: str) -> TokenSubject:
        try:
            claims = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
        except jwt.ExpiredSignatureError as exc:
            raise AppError(
                code="auth.token_expired",
                message="Token has expired.",
                status_code=401,
                details={},
            ) from exc
        except jwt.InvalidTokenError as exc:
            raise AppError(
                code="auth.invalid_token",
                message="Token is invalid.",
                status_code=401,
                details={},
            ) from exc

        token_type = str(claims.get("typ", ""))
        if token_type != expected_type:
            raise AppError(
                code="auth.invalid_token_type",
                message="Token type is not valid for this operation.",
                status_code=401,
                details={"expected": expected_type, "actual": token_type},
            )

        return TokenSubject(user_id=UUID(str(claims["sub"])), token_type=token_type)

    def _encode(self, user_id: UUID, token_type: str) -> str:
        now = datetime.now(timezone.utc)  # noqa: UP017
        expires_at = now + self._ttl(token_type)
        claims: dict[str, Any] = {
            "sub": str(user_id),
            "typ": token_type,
            "iat": int(now.timestamp()),
            "exp": int(expires_at.timestamp()),
            "jti": str(uuid4()),
        }
        return jwt.encode(
            claims,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def _ttl(self, token_type: str) -> timedelta:
        if token_type == "access":  # noqa: S105
            return timedelta(minutes=self.settings.access_token_expire_minutes)
        if token_type == "refresh":  # noqa: S105
            return timedelta(days=self.settings.refresh_token_expire_days)
        raise ValueError(f"Unsupported token type: {token_type}")


class RbacPolicy:
    _role_permissions: dict[str, frozenset[str]] = {
        "organization_admin": frozenset(
            {
                "organizations.read",
                "organizations.manage",
                "workspaces.read",
                "workspaces.create",
                "documents.read",
                "documents.search",
                "documents.upload",
                "users.invite",
                "metrics.view",
            }
        ),
        "manager": frozenset(
            {
                "organizations.read",
                "workspaces.read",
                "documents.read",
                "documents.search",
                "metrics.view",
            }
        ),
        "knowledge_editor": frozenset(
            {
                "organizations.read",
                "workspaces.read",
                "documents.read",
                "documents.search",
                "documents.upload",
            }
        ),
        "standard_user": frozenset(
            {"organizations.read", "workspaces.read", "documents.read", "documents.search"}
        ),
        "guest": frozenset({"organizations.read", "workspaces.read", "documents.read"}),
    }

    def permissions_for_role(self, role: str) -> frozenset[str]:
        return self._role_permissions.get(role, frozenset())

    def has_permission(self, role: str, permission: str) -> bool:
        return permission in self.permissions_for_role(role)
