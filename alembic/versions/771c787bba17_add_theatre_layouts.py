"""add_theatre_layouts

Revision ID: 771c787bba17
Revises: e3a447ad0bf6
Create Date: 2026-06-18 22:03:25.620614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '771c787bba17'
down_revision: Union[str, Sequence[str], None] = 'e3a447ad0bf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create theatre_layouts table
    op.create_table(
        'theatre_layouts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('theatre_id', sa.Integer(), nullable=False),
        sa.Column('screen_id', sa.Integer(), nullable=False),
        sa.Column('layout_name', sa.String(length=100), nullable=False),
        sa.Column('layout_type', sa.String(length=50), nullable=False),
        sa.Column('total_seats', sa.Integer(), nullable=False),
        sa.Column('rows', sa.Integer(), nullable=False),
        sa.Column('cols', sa.Integer(), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['screen_id'], ['screens.id'], ),
        sa.ForeignKeyConstraint(['theatre_id'], ['theatres.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_theatre_layouts_id'), 'theatre_layouts', ['id'], unique=False)
    op.create_index(op.f('ix_theatre_layouts_is_published'), 'theatre_layouts', ['is_published'], unique=False)
    op.create_index(op.f('ix_theatre_layouts_screen_id'), 'theatre_layouts', ['screen_id'], unique=False)
    op.create_index(op.f('ix_theatre_layouts_theatre_id'), 'theatre_layouts', ['theatre_id'], unique=False)

    # 2. Create seat_definitions table
    op.create_table(
        'seat_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('layout_id', sa.Integer(), nullable=False),
        sa.Column('seat_code', sa.String(length=10), nullable=False),
        sa.Column('row_label', sa.String(length=5), nullable=False),
        sa.Column('seat_number', sa.Integer(), nullable=False),
        sa.Column('seat_type', sa.String(length=20), nullable=False),
        sa.Column('category', sa.String(length=20), nullable=False),
        sa.Column('position_x', sa.Integer(), nullable=False),
        sa.Column('position_y', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['layout_id'], ['theatre_layouts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('layout_id', 'position_x', 'position_y', name='uq_layout_position'),
        sa.UniqueConstraint('layout_id', 'seat_code', name='uq_layout_seat_code')
    )
    op.create_index(op.f('ix_seat_definitions_id'), 'seat_definitions', ['id'], unique=False)
    op.create_index(op.f('ix_seat_definitions_layout_id'), 'seat_definitions', ['layout_id'], unique=False)
    op.create_index(op.f('ix_seat_definitions_seat_code'), 'seat_definitions', ['seat_code'], unique=False)

    # 3. Data Migration: auto-generate layouts for existing screens
    bind = op.get_bind()
    result = bind.execute(sa.text("SELECT id, theatre_id, total_seats FROM screens"))
    screens = result.fetchall()

    from backend.utils.layout_generator import generate_layout
    
    for screen_id, theatre_id, total_seats in screens:
        layout_data = generate_layout(total_seats=total_seats, template="STANDARD")
        
        bind.execute(
            sa.text(
                "INSERT INTO theatre_layouts (theatre_id, screen_id, layout_name, layout_type, total_seats, `rows`, `cols`, is_published, created_at, updated_at) "
                "VALUES (:theatre_id, :screen_id, :layout_name, :layout_type, :total_seats, :rows, :cols, :is_published, NOW(), NOW())"
            ),
            {
                "theatre_id": theatre_id,
                "screen_id": screen_id,
                "layout_name": "Default Layout",
                "layout_type": "STANDARD",
                "total_seats": layout_data.total_seats,
                "rows": layout_data.rows,
                "cols": layout_data.cols,
                "is_published": True
            }
        )
        
        # Safely fetch the newly inserted layout ID
        layout_id = bind.execute(
            sa.text("SELECT id FROM theatre_layouts WHERE screen_id = :screen_id AND is_published = 1"),
            {"screen_id": screen_id}
        ).scalar()
        
        for s in layout_data.seats:
            bind.execute(
                sa.text(
                    "INSERT INTO seat_definitions (layout_id, seat_code, row_label, seat_number, seat_type, category, position_x, position_y, is_active) "
                    "VALUES (:layout_id, :seat_code, :row_label, :seat_number, :seat_type, :category, :position_x, :position_y, :is_active)"
                ),
                {
                    "layout_id": layout_id,
                    "seat_code": s.seat_code,
                    "row_label": s.row_label,
                    "seat_number": s.seat_number,
                    "seat_type": s.seat_type,
                    "category": s.category,
                    "position_x": s.position_x,
                    "position_y": s.position_y,
                    "is_active": s.is_active
                }
            )


def downgrade() -> None:
    op.drop_index(op.f('ix_seat_definitions_seat_code'), table_name='seat_definitions')
    op.drop_index(op.f('ix_seat_definitions_layout_id'), table_name='seat_definitions')
    op.drop_index(op.f('ix_seat_definitions_id'), table_name='seat_definitions')
    op.drop_table('seat_definitions')
    op.drop_index(op.f('ix_theatre_layouts_theatre_id'), table_name='theatre_layouts')
    op.drop_index(op.f('ix_theatre_layouts_screen_id'), table_name='theatre_layouts')
    op.drop_index(op.f('ix_theatre_layouts_is_published'), table_name='theatre_layouts')
    op.drop_index(op.f('ix_theatre_layouts_id'), table_name='theatre_layouts')
    op.drop_table('theatre_layouts')

