"""add_oauth_fields

Revision ID: 003_add_oauth_fields
Revises: 002_add_error_tracking
Create Date: 2025-01-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_add_oauth_fields'
down_revision: Union[str, None] = '002_add_error_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make hashed_password nullable for OAuth users
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(255),
                    nullable=True,
                    existing_comment='Bcrypt hashed password (nullable for OAuth users)')
    
    # Add Google OAuth fields
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True, unique=True, comment='Google user ID for OAuth authentication'))
    op.add_column('users', sa.Column('auth_provider', sa.String(50), nullable=False, server_default='password', comment="Authentication provider: 'password' or 'google'"))
    
    # Create index on google_id for faster lookups
    op.create_index('idx_users_google_id', 'users', ['google_id'], unique=True)


def downgrade() -> None:
    # Remove index
    op.drop_index('idx_users_google_id', table_name='users')
    
    # Remove OAuth columns
    op.drop_column('users', 'auth_provider')
    op.drop_column('users', 'google_id')
    
    # Make hashed_password non-nullable again (may fail if OAuth users exist)
    op.alter_column('users', 'hashed_password',
                    existing_type=sa.String(255),
                    nullable=False,
                    existing_comment='Bcrypt hashed password')

