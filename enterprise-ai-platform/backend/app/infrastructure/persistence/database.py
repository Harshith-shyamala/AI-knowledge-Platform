from __future__ import annotations

from pathlib import Path
from time import perf_counter

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.schemas.health import ReadinessDependency


def create_database_engine(settings: Settings) -> Engine:
    connect_args: dict[str, object] = {}
    engine_kwargs: dict[str, object] = {
        "pool_pre_ping": True,
        "future": True,
    }

    if settings.database_url.startswith("sqlite"):
        if settings.database_url.startswith("sqlite:///./"):
            database_path = settings.database_url.removeprefix("sqlite:///./")
            Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        connect_args["check_same_thread"] = False

        if settings.database_url == "sqlite://":
            engine_kwargs["poolclass"] = StaticPool

    return create_engine(settings.database_url, connect_args=connect_args, **engine_kwargs)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


class DatabaseReadinessProbe:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    async def check(self) -> ReadinessDependency:
        started_at = perf_counter()
        try:
            with self._session_factory() as session:
                session.execute(text("select 1"))
        except Exception:
            return ReadinessDependency(
                name="database",
                status="degraded",
                latency_ms=_elapsed_ms(started_at),
            )

        return ReadinessDependency(
            name="database",
            status="ready",
            latency_ms=_elapsed_ms(started_at),
        )


def _elapsed_ms(started_at: float) -> float:
    return round((perf_counter() - started_at) * 1000, 3)

