from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.application.security import JwtTokenService, PasswordHasher, RbacPolicy, TokenPair
from app.application.unit_of_work import UnitOfWorkFactory
from app.core.errors import AppError
from app.domain.tenancy import Organization, OrganizationMembership, User

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class RegisterCommand:
    email: str
    password: str
    display_name: str
    organization_name: str
    organization_slug: str | None = None


@dataclass(frozen=True)
class LoginCommand:
    email: str
    password: str


@dataclass(frozen=True)
class AuthenticatedSession:
    user: User
    tokens: TokenPair
    memberships: list[OrganizationMembership]


@dataclass(frozen=True)
class AuthService:
    uow_factory: UnitOfWorkFactory
    password_hasher: PasswordHasher
    token_service: JwtTokenService
    rbac_policy: RbacPolicy

    def register(self, command: RegisterCommand) -> AuthenticatedSession:
        email = _normalize_email(command.email)
        organization_slug = _normalize_slug(command.organization_slug or command.organization_name)
        now = _utc_now()
        user = User(
            id=uuid4(),
            email=email,
            display_name=command.display_name.strip(),
            password_hash=self.password_hasher.hash(command.password),
            is_active=True,
            email_verified_at=None,
            created_at=now,
            updated_at=now,
        )
        organization = Organization(
            id=uuid4(),
            name=command.organization_name.strip(),
            slug=organization_slug,
            plan="developer",
            status="active",
            created_at=now,
            updated_at=now,
        )
        membership = OrganizationMembership(
            id=uuid4(),
            organization_id=organization.id,
            user_id=user.id,
            role="organization_admin",
            created_at=now,
        )

        with self.uow_factory() as uow:
            if uow.users.get_by_email(email) is not None:
                raise AppError(
                    code="auth.email_conflict",
                    message="An account with this email already exists.",
                    status_code=409,
                    details={"email": email},
                )
            if uow.organizations.get_by_slug(organization_slug) is not None:
                raise AppError(
                    code="organization.slug_conflict",
                    message="An organization with this slug already exists.",
                    status_code=409,
                    details={"slug": organization_slug},
                )
            uow.users.add(user)
            uow.organizations.add(organization)
            uow.organization_memberships.add(membership)
            uow.commit()

        return AuthenticatedSession(
            user=user,
            tokens=self.token_service.issue_pair(user.id),
            memberships=[membership],
        )

    def login(self, command: LoginCommand) -> AuthenticatedSession:
        email = _normalize_email(command.email)
        with self.uow_factory() as uow:
            user = uow.users.get_by_email(email)
            if user is None:
                raise AppError(
                    code="auth.invalid_credentials",
                    message="Email or password is incorrect.",
                    status_code=401,
                    details={},
                )
            if not self.password_hasher.verify(command.password, user.password_hash):
                raise AppError(
                    code="auth.invalid_credentials",
                    message="Email or password is incorrect.",
                    status_code=401,
                    details={},
                )
            if not user.is_active:
                raise AppError(
                    code="auth.user_inactive",
                    message="User is inactive.",
                    status_code=403,
                    details={},
                )
            memberships = uow.organization_memberships.list_for_user(user.id)

        return AuthenticatedSession(
            user=user,
            tokens=self.token_service.issue_pair(user.id),
            memberships=memberships,
        )

    def refresh(self, refresh_token: str) -> TokenPair:
        subject = self.token_service.verify(refresh_token, expected_type="refresh")
        with self.uow_factory() as uow:
            user = uow.users.get(subject.user_id)

        if user is None or not user.is_active:
            raise AppError(
                code="auth.invalid_token_subject",
                message="Token subject is not active.",
                status_code=401,
                details={},
            )
        return self.token_service.issue_pair(user.id)

    def authenticate_access_token(self, access_token: str) -> AuthenticatedSession:
        subject = self.token_service.verify(access_token, expected_type="access")
        with self.uow_factory() as uow:
            user = uow.users.get(subject.user_id)
            if user is None or not user.is_active:
                raise AppError(
                    code="auth.invalid_token_subject",
                    message="Token subject is not active.",
                    status_code=401,
                    details={},
                )
            memberships = uow.organization_memberships.list_for_user(user.id)

        return AuthenticatedSession(
            user=user,
            tokens=TokenPair(access_token=access_token, refresh_token=""),
            memberships=memberships,
        )

    def require_permission(
        self,
        session: AuthenticatedSession,
        organization_id: UUID,
        permission: str,
    ) -> OrganizationMembership:
        for membership in session.memberships:
            if membership.organization_id == organization_id and self.rbac_policy.has_permission(
                membership.role,
                permission,
            ):
                return membership

        raise AppError(
            code="auth.permission_denied",
            message="You do not have permission to perform this action.",
            status_code=403,
            details={"organization_id": str(organization_id), "permission": permission},
        )


def _normalize_email(email: str) -> str:
    normalized = email.strip().lower()
    if "@" not in normalized:
        raise AppError(
            code="auth.invalid_email",
            message="Email address is invalid.",
            status_code=422,
            details={},
        )
    return normalized


def _normalize_slug(value: str) -> str:
    slug = _SLUG_PATTERN.sub("-", value.strip().lower()).strip("-")
    if not slug:
        raise AppError(
            code="slug.invalid",
            message="Slug must contain at least one letter or number.",
            status_code=422,
            details={},
        )
    return slug


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)  # noqa: UP017
