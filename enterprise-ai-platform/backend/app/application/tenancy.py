from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class TenantContext:
    organization_id: UUID
    workspace_id: UUID | None = None
    actor_user_id: UUID | None = None
    roles: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    trace_id: str | None = None

