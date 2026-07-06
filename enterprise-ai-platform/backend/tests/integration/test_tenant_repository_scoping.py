from app.application.organizations import CreateOrganizationCommand, CreateWorkspaceCommand
from app.core.config import Environment, Settings
from app.core.container import AppContainer


def test_workspace_repository_scopes_results_by_organization() -> None:
    settings = Settings(
        environment=Environment.test,
        database_url="sqlite://",
        auto_create_schema=True,
    )
    service = AppContainer.build(settings).organization_service

    org_a = service.create_organization(CreateOrganizationCommand(name="Tenant A"))
    org_b = service.create_organization(CreateOrganizationCommand(name="Tenant B"))
    workspace_a = service.create_workspace(
        CreateWorkspaceCommand(organization_id=org_a.id, name="Engineering")
    )
    workspace_b = service.create_workspace(
        CreateWorkspaceCommand(organization_id=org_b.id, name="Engineering")
    )

    scoped_a = service.list_workspaces(org_a.id)
    scoped_b = service.list_workspaces(org_b.id)

    assert [workspace.id for workspace in scoped_a] == [workspace_a.id]
    assert [workspace.id for workspace in scoped_b] == [workspace_b.id]
    assert scoped_a[0].organization_id == org_a.id
    assert scoped_b[0].organization_id == org_b.id
