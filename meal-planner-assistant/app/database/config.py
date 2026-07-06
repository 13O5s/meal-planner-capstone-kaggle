from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import quote_plus


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(
        default_factory=lambda: int(os.getenv("DB_PORT", "5432"))
    )
    database: str = field(
        default_factory=lambda: os.getenv("DB_NAME", "meal_planner")
    )
    username: str = field(
        default_factory=lambda: os.getenv("DB_USER", "postgres")
    )
    password: str = field(
        default_factory=lambda: os.getenv("DB_PASSWORD", "postgres")
    )
    echo: bool = field(
        default_factory=lambda: os.getenv("DB_ECHO", "false").lower()
        == "true"
    )
    pool_size: int = field(
        default_factory=lambda: int(os.getenv("DB_POOL_SIZE", "10"))
    )
    max_overflow: int = field(
        default_factory=lambda: int(os.getenv("DB_MAX_OVERFLOW", "20"))
    )

    @property
    def async_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.username}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.database}"
        )

    @property
    def sync_url(self) -> str:
        return (
            f"postgresql://{self.username}:{quote_plus(self.password)}"
            f"@{self.host}:{self.port}/{self.database}"
        )


_config: DatabaseConfig | None = None


def get_config() -> DatabaseConfig:
    global _config
    if _config is None:
        url = os.getenv("DATABASE_URL")
        if url:
            parts = url.replace("postgresql+asyncpg://", "").split("@")
            user_pass = parts[0].split(":")
            host_port_db = parts[1].split("/")
            host_port = host_port_db[0].split(":")
            _config = DatabaseConfig(
                username=user_pass[0],
                password=user_pass[1],
                host=host_port[0],
                port=int(host_port[1]) if len(host_port) > 1 else 5432,
                database=host_port_db[1],
            )
        else:
            _config = DatabaseConfig()
    return _config
