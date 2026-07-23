"""Add evaluation_cases table for golden dataset.

Revision ID: 0002_evaluation_cases
Revises: 0001_initial_schema
Create Date: 2026-07-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0002_evaluation_cases'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'evaluation_cases',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('query', sa.Text(), nullable=False),
        sa.Column('expected_answer', sa.Text(), nullable=False),
        sa.Column('expected_chunk_ids_json', sa.Text(), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('tags_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('evaluation_cases')
