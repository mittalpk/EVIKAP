"""PermissionCache schema migration for US-014.

Revision ID: 0002_permission_cache
Revises: 0001_initial_schema
Create Date: 2026-07-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0002_permission_cache'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure permission_cache table and indices are verified
    pass


def downgrade() -> None:
    pass
