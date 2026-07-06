from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from app.application.unit_of_work import UnitOfWorkFactory
from app.core.errors import AppError
from app.domain.tenancy import Organization, Workspace

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class CreateOrganizationCommand:
    name: str
    slug: str | None = None
    plan: str = "developer"


@dataclass(frozen=True)
class CreateWorkspaceCommand:
    organization_id: UUID
    name: str
    slug: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class OrganizationService:
    uow_factory: UnitOfWorkFactory

    def create_organization(self, command: CreateOrganizationCommand) -> Organization:
        slug = _normalize_slug(command.slug or command.name)
        now = _utc_now()
        organization = Organization(
            id=uuid4(),
            name=command.name.strip(),
            slug=slug,
            plan=command.plan,
            status="active",
            created_at=now,
            updated_at=now,
        )

        with self.uow_factory() as uow:
            if uow.organizations.get_by_slug(slug) is not None:
                raise AppError(
                    code="organization.slug_conflict",
                    message="An organization with this slug already exists.",
                    status_code=409,
                    details={"slug": slug},
                )
            uow.organizations.add(organization)
            uow.commit()

        return organization

    def list_organizations(self) -> list[Organization]:
        with self.uow_factory() as uow:
            return uow.organizations.list()

    def get_organization(self, organization_id: UUID) -> Organization:
        with self.uow_factory() as uow:
            organization = uow.organizations.get(organization_id)

        if organization is None:
            raise AppError(
                code="organization.not_found",
                message="Organization not found.",
                status_code=404,
                details={"organization_id": str(organization_id)},
            )

        return organization

    def create_workspace(self, command: CreateWorkspaceCommand) -> Workspace:
        slug = _normalize_slug(command.slug or command.name)
        now = _utc_now()
        workspace = Workspace(
            id=uuid4(),
            organization_id=command.organization_id,
            name=command.name.strip(),
            slug=slug,
            description=command.description,
            created_at=now,
            updated_at=now,
        )

        with self.uow_factory() as uow:
            if uow.organizations.get(command.organization_id) is None:
                raise AppError(
                    code="organization.not_found",
                    message="Organization not found.",
                    status_code=404,
                    details={"organization_id": str(command.organization_id)},
                )
            if uow.workspaces.get_by_slug(command.organization_id, slug) is not None:
                raise AppError(
                    code="workspace.slug_conflict",
                    message="A workspace with this slug already exists in this organization.",
                    status_code=409,
                    details={"organization_id": str(command.organization_id), "slug": slug},
                )
            uow.workspaces.add(workspace)
            uow.commit()

        return workspace

    def list_workspaces(self, organization_id: UUID) -> list[Workspace]:
        with self.uow_factory() as uow:
            if uow.organizations.get(organization_id) is None:
                raise AppError(
                    code="organization.not_found",
                    message="Organization not found.",
                    status_code=404,
                    details={"organization_id": str(organization_id)},
                )
            return uow.workspaces.list_for_organization(organization_id)


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
