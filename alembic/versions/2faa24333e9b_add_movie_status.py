"""add_movie_status

Revision ID: 2faa24333e9b
Revises: a1b2c3d4e5f6
Create Date: 2026-06-27 21:32:48.542126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '2faa24333e9b'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    movie_cols = [c['name'] for c in inspector.get_columns('movies')]
    if 'status' not in movie_cols:
        op.add_column('movies', sa.Column('status', sa.String(length=50), nullable=False, server_default='NOW_SHOWING'))

    seat_cols = [c['name'] for c in inspector.get_columns('seat_definitions')]
    if 'is_active' in seat_cols:
        op.alter_column('seat_definitions', 'is_active',
                   existing_type=mysql.TINYINT(display_width=1),
                   nullable=True)
    if 'is_couple' in seat_cols:
        op.drop_column('seat_definitions', 'is_couple')
    if 'is_wheelchair' in seat_cols:
        op.drop_column('seat_definitions', 'is_wheelchair')
    if 'is_blocked' in seat_cols:
        op.drop_column('seat_definitions', 'is_blocked')

    layout_cols = [c['name'] for c in inspector.get_columns('theatre_layouts')]
    if 'status' not in layout_cols:
        op.add_column('theatre_layouts', sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'))
    if 'version' not in layout_cols:
        op.add_column('theatre_layouts', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    if 'is_published' in layout_cols:
        op.alter_column('theatre_layouts', 'is_published',
                   existing_type=mysql.TINYINT(display_width=1),
                   nullable=True)

    layout_indexes = [idx['name'] for idx in inspector.get_indexes('theatre_layouts')]
    if 'ix_theatre_layouts_status' not in layout_indexes:
        op.create_index(op.f('ix_theatre_layouts_status'), 'theatre_layouts', ['status'], unique=False)
    if 'ix_theatre_layouts_version' not in layout_indexes:
        op.create_index(op.f('ix_theatre_layouts_version'), 'theatre_layouts', ['version'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    layout_indexes = [idx['name'] for idx in inspector.get_indexes('theatre_layouts')]
    if 'ix_theatre_layouts_version' in layout_indexes:
        op.drop_index(op.f('ix_theatre_layouts_version'), table_name='theatre_layouts')
    if 'ix_theatre_layouts_status' in layout_indexes:
        op.drop_index(op.f('ix_theatre_layouts_status'), table_name='theatre_layouts')

    layout_cols = [c['name'] for c in inspector.get_columns('theatre_layouts')]
    if 'is_published' in layout_cols:
        op.alter_column('theatre_layouts', 'is_published',
                   existing_type=mysql.TINYINT(display_width=1),
                   nullable=False)
    if 'version' in layout_cols:
        op.drop_column('theatre_layouts', 'version')
    if 'status' in layout_cols:
        op.drop_column('theatre_layouts', 'status')

    movie_cols = [c['name'] for c in inspector.get_columns('movies')]
    if 'status' in movie_cols:
        op.drop_column('movies', 'status')

