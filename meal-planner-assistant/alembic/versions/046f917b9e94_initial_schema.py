"""initial_schema

Revision ID: 046f917b9e94
Revises:
Create Date: 2026-07-02 00:19:44.949142
"""

from collections.abc import Sequence

from sqlalchemy import inspect

from alembic import op
from app.database.models import Base

revision: str = "046f917b9e94"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    target_tables = set(Base.metadata.tables.keys())
    tables_to_create = target_tables - existing_tables

    if tables_to_create:
        Base.metadata.create_all(
            bind,
            tables=[
                Base.metadata.tables[name]
                for name in Base.metadata.sorted_tables
                if name in tables_to_create
            ],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = set(inspector.get_table_names())
    target_tables = set(Base.metadata.tables.keys())
    tables_to_drop = existing_tables & target_tables

    for table_name in reversed(Base.metadata.sorted_tables):
        if table_name.name in tables_to_drop:
            op.drop_table(table_name.name)
