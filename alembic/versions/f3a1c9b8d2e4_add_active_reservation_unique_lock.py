"""add_active_reservation_unique_lock

Revision ID: f3a1c9b8d2e4
Revises: 079cd5453dce
Create Date: 2026-08-29 00:00:00.000000

Prevents two concurrent requests from both holding an "active" reservation
on the same (show_id, seat_id). MySQL has no partial/filtered unique index,
so a plain UNIQUE(show_id, seat_id) would permanently block a seat after its
first-ever reservation, even once that reservation expires/is released.

Instead, a stored generated column collapses the key to NULL for any row
that isn't currently "active":

    active_lock_key = IF(status = 'active', CONCAT(show_id, ':', seat_id), NULL)

MySQL unique indexes treat multiple NULLs as distinct, so expired/cancelled/
converted rows (NULL key) never collide with each other or with a later
active reservation for the same seat — only two simultaneously-active rows
for the same seat collide, which is exactly the race we need to prevent.
Historical rows are never deleted or altered by this migration.

Mirrors the same defense-in-depth pattern already used for booked_seats
(see 079cd5453dce) applied to seat_reservations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3a1c9b8d2e4'
down_revision: Union[str, Sequence[str], None] = '079cd5453dce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('seat_reservations')]

    # Guard against pre-existing duplicate active holds for the same seat
    # (should not occur in practice, but makes this migration safe to run
    # against an existing database with data). Keep the most recently
    # created hold active and expire the older duplicates rather than
    # deleting them, preserving history.
    op.execute("""
        UPDATE seat_reservations sr1
        INNER JOIN (
            SELECT show_id, seat_id, MAX(id) AS keep_id
            FROM seat_reservations
            WHERE status = 'active'
            GROUP BY show_id, seat_id
            HAVING COUNT(*) > 1
        ) dupes
        ON sr1.show_id = dupes.show_id
           AND sr1.seat_id = dupes.seat_id
           AND sr1.id != dupes.keep_id
        SET sr1.status = 'expired'
        WHERE sr1.status = 'active'
    """)

    if 'active_lock_key' not in columns:
        op.execute("""
            ALTER TABLE seat_reservations
            ADD COLUMN active_lock_key VARCHAR(30)
            GENERATED ALWAYS AS (
                IF(status = 'active', CONCAT(show_id, ':', seat_id), NULL)
            ) STORED
        """)

    indexes = [idx['name'] for idx in inspector.get_indexes('seat_reservations')]
    if 'uq_seat_reservations_active_lock' not in indexes:
        op.create_unique_constraint(
            'uq_seat_reservations_active_lock',
            'seat_reservations',
            ['active_lock_key'],
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = [idx['name'] for idx in inspector.get_indexes('seat_reservations')]
    if 'uq_seat_reservations_active_lock' in indexes:
        op.drop_constraint(
            'uq_seat_reservations_active_lock',
            'seat_reservations',
            type_='unique',
        )

    columns = [col['name'] for col in inspector.get_columns('seat_reservations')]
    if 'active_lock_key' in columns:
        op.drop_column('seat_reservations', 'active_lock_key')
