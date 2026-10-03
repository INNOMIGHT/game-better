"""change timeline real timestamp to bigint

Revision ID: e6a61415751e
Revises: 1fc8f5c8693c
Create Date: 2026-10-02 14:39:39.576440

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e6a61415751e'
down_revision: Union[str, Sequence[str], None] = '1fc8f5c8693c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade():
    op.alter_column(
        "timeline_events",
        "real_timestamp_ms",
        existing_type=sa.Integer(),
        type_=sa.BigInteger(),
        existing_nullable=True,
        postgresql_using="real_timestamp_ms::bigint",
    )


def downgrade():
    op.alter_column(
        "timeline_events",
        "real_timestamp_ms",
        existing_type=sa.BigInteger(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="real_timestamp_ms::integer",
    )