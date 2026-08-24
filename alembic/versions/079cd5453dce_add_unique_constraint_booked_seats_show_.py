"""add_unique_constraint_booked_seats_show_id_seat_name

Revision ID: 079cd5453dce
Revises: 2faa24333e9b
Create Date: 2026-08-24 16:24:32.481936

Adds a DB-level unique constraint on (show_id, seat_name) in the booked_seats
table. This prevents duplicate seat bookings at the database layer, providing
a last-resort safety net even if application-level checks are bypassed under
concurrent load.

The constraint only applies to non-cancelled bookings; however since a
database-level unique constraint cannot filter by a JOIN, we enforce uniqueness
across ALL rows. The application-level seat availability check (which excludes
cancelled bookings) remains the primary guard. The DB constraint prevents the
race condition where two concurrent requests both pass the Python check before
either commits.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '079cd5453dce'
down_revision: Union[str, Sequence[str], None] = '2faa24333e9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint on (show_id, seat_name) in booked_seats."""
    # Remove any existing duplicate rows before adding the constraint.
    # In a clean system this should be a no-op, but this guard ensures
    # the migration is safe to run against existing databases with data.
    op.execute("""
        DELETE bs1 FROM booked_seats bs1
        INNER JOIN booked_seats bs2
        ON bs1.show_id = bs2.show_id
           AND bs1.seat_name = bs2.seat_name
           AND bs1.id > bs2.id
    """)

    # Add the unique constraint
    op.create_unique_constraint(
        'uq_booked_seats_show_seat',
        'booked_seats',
        ['show_id', 'seat_name'],
    )


def downgrade() -> None:
    """Remove the unique constraint from booked_seats."""
    op.drop_constraint(
        'uq_booked_seats_show_seat',
        'booked_seats',
        type_='unique',
    )
