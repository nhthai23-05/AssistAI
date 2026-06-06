"""Add actions_json to message

Revision ID: a1b2c3d4e5f6
Revises: fd8d56109def
Create Date: 2026-06-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'fd8d56109def'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('message', sa.Column('actions_json', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('message', 'actions_json')
