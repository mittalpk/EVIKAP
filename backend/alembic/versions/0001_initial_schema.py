"""Initial database schema migration creating sources, chunks, and permission_cache tables.

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-07-23

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create sources table
    op.create_table(
        'sources',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=50), nullable=False),
        sa.Column('endpoint_url', sa.Text(), nullable=False),
        sa.Column('secret_reference', sa.String(length=255), nullable=False),
        sa.Column('owner_email', sa.String(length=255), nullable=False),
        sa.Column('sensitivity_level', sa.String(length=50), nullable=False),
        sa.Column('sensitivity_signed_off', sa.Boolean(), nullable=False),
        sa.Column('refresh_cadence_minutes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 2. Create chunks table
    op.create_table(
        'chunks',
        sa.Column('id', sa.String(length=100), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('document_id', sa.String(length=255), nullable=False),
        sa.Column('parent_doc_id', sa.String(length=255), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('permissions_ref', sa.String(length=255), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column('references_json', sa.Text(), nullable=True),
        sa.Column('embedding_vector_str', sa.Text(), nullable=True),
        sa.Column('last_indexed_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_chunks_source_id', 'chunks', ['source_id'])
    op.create_index('idx_chunks_permissions_ref', 'chunks', ['permissions_ref'])
    op.create_index('idx_chunks_parent_doc_id', 'chunks', ['parent_doc_id'])

    # 3. Create permission_cache table
    op.create_table(
        'permission_cache',
        sa.Column('cache_id', sa.String(length=100), nullable=False),
        sa.Column('requester_identity', sa.String(length=255), nullable=False),
        sa.Column('source_id', sa.String(length=100), nullable=False),
        sa.Column('access_level', sa.String(length=50), nullable=False),
        sa.Column('granted_acl_refs_json', sa.Text(), nullable=False),
        sa.Column('cached_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('ttl_seconds', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('cache_id')
    )
    op.create_index('idx_perm_cache_identity_source', 'permission_cache', ['requester_identity', 'source_id'])


def downgrade() -> None:
    op.drop_index('idx_perm_cache_identity_source', table_name='permission_cache')
    op.drop_table('permission_cache')
    op.drop_index('idx_chunks_parent_doc_id', table_name='chunks')
    op.drop_index('idx_chunks_permissions_ref', table_name='chunks')
    op.drop_index('idx_chunks_source_id', table_name='chunks')
    op.drop_table('chunks')
    op.drop_table('sources')
