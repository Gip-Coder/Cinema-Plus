"""add_layout_status_and_version

Revision ID: a1b2c3d4e5f6
Revises: 771c787bba17
Create Date: 2026-06-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '771c787bba17'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('theatre_layouts', sa.Column('status', sa.String(length=20), nullable=True))
    op.add_column('theatre_layouts', sa.Column('version', sa.Integer(), nullable=True))

    # Backfill from existing is_published flag
    op.execute(
        sa.text(
            "UPDATE theatre_layouts SET status = CASE WHEN is_published = 1 THEN 'published' ELSE 'draft' END, "
            "version = 1 WHERE status IS NULL"
        )
    )

    op.alter_column('theatre_layouts', 'status', nullable=False, server_default='draft')
    op.alter_column('theatre_layouts', 'version', nullable=False, server_default='1')
    op.create_index(op.f('ix_theatre_layouts_status'), 'theatre_layouts', ['status'], unique=False)
    op.create_index(op.f('ix_theatre_layouts_version'), 'theatre_layouts', ['version'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_theatre_layouts_version'), table_name='theatre_layouts')
    op.drop_index(op.f('ix_theatre_layouts_status'), table_name='theatre_layouts')
    op.drop_column('theatre_layouts', 'version')
    op.drop_column('theatre_layouts', 'status')
