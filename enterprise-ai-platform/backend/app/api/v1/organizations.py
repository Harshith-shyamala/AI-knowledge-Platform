from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Request, status

from app.api.dependencies import AuthServiceDep, CurrentSessionDep
from app.application.organizations import (
    CreateOrganizationCommand,
    CreateWorkspaceCommand,
    OrganizationService,
)
from app.core.container import AppContainer
from app.schemas.organizations import (
    CreateOrganizationRequest,
    CreateWorkspaceRequest,
    OrganizationResponse,
    WorkspaceResponse,
)

router = APIRouter(prefix="/organizations")


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create organization",
)
async def create_organization(
    request: Request,
    payload: CreateOrganizationRequest,
) -> OrganizationResponse:
    service = _organization_service(request)
    organization = service.create_organization(
        CreateOrganizationCommand(
            name=payload.name,
            slug=payload.slug,
            plan=payload.plan,
        )
    )
    return OrganizationResponse.model_validate(organization)


@router.get(
    "",
    response_model=list[OrganizationResponse],
    summary="List organizations",
)
async def list_organizations(
    request: Request,
    session: CurrentSessionDep,
) -> list[OrganizationResponse]:
    service = _organization_service(request)
    return [
        OrganizationResponse.model_validate(service.get_organization(membership.organization_id))
        for membership in session.memberships
    ]


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get organization",
)
async def get_organization(
    request: Request,
    organization_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> OrganizationResponse:
    auth_service.require_permission(session, organization_id, "organizations.read")
    service = _organization_service(request)
    return OrganizationResponse.model_validate(service.get_organization(organization_id))


@router.post(
    "/{organization_id}/workspaces",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create workspace",
)
async def create_workspace(
    request: Request,
    organization_id: UUID,
    payload: CreateWorkspaceRequest,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> WorkspaceResponse:
    auth_service.require_permission(session, organization_id, "workspaces.create")
    service = _organization_service(request)
    workspace = service.create_workspace(
        CreateWorkspaceCommand(
            organization_id=organization_id,
            name=payload.name,
            slug=payload.slug,
            description=payload.description,
        )
    )
    return WorkspaceResponse.model_validate(workspace)


@router.get(
    "/{organization_id}/workspaces",
    response_model=list[WorkspaceResponse],
    summary="List organization workspaces",
)
async def list_workspaces(
    request: Request,
    organization_id: UUID,
    session: CurrentSessionDep,
    auth_service: AuthServiceDep,
) -> list[WorkspaceResponse]:
    auth_service.require_permission(session, organization_id, "workspaces.read")
    service = _organization_service(request)
    return [
        WorkspaceResponse.model_validate(workspace)
        for workspace in service.list_workspaces(organization_id)
    ]


def _organization_service(request: Request) -> OrganizationService:
    container: AppContainer = request.app.state.container
    return container.organization_service
