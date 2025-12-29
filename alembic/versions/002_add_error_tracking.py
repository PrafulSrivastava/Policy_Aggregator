"""add_error_tracking

Revision ID: 002_add_error_tracking
Revises: 001_initial_schema
Create Date: 2025-01-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_error_tracking'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add error tracking columns to sources table
    op.add_column('sources', sa.Column('consecutive_fetch_failures', sa.Integer(), nullable=False, server_default='0', comment='Number of consecutive fetch failures'))
    op.add_column('sources', sa.Column('consecutive_email_failures', sa.Integer(), nullable=False, server_default='0', comment='Number of consecutive email delivery failures'))
    op.add_column('sources', sa.Column('last_fetch_error', sa.String(), nullable=True, comment='Last fetch error message'))
    op.add_column('sources', sa.Column('last_email_error', sa.String(), nullable=True, comment='Last email delivery error message'))


def downgrade() -> None:
    # Remove error tracking columns from sources table
    op.drop_column('sources', 'last_email_error')
    op.drop_column('sources', 'last_fetch_error')
    op.drop_column('sources', 'consecutive_email_failures')
    op.drop_column('sources', 'consecutive_fetch_failures')

