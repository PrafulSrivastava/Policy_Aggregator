"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create sources table
    op.create_table(
        'sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('country', sa.String(length=2), nullable=False, comment='ISO country code (2 characters)'),
        sa.Column('visa_type', sa.String(length=50), nullable=False, comment="Type of visa (e.g., 'Student', 'Work')"),
        sa.Column('url', sa.String(), nullable=False, comment='Source URL to fetch from'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Human-readable name for the source'),
        sa.Column('fetch_type', sa.String(length=10), nullable=False, comment="How to fetch content: 'html' or 'pdf'"),
        sa.Column('check_frequency', sa.String(length=20), nullable=False, comment="How often to check: 'daily', 'weekly', or 'custom'"),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'), comment='Whether source is currently being monitored'),
        sa.Column('last_checked_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp of last successful fetch'),
        sa.Column('last_change_detected_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp of last change detected'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb"), comment='Additional configuration (JSONB for flexibility)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='When source was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='When source was last modified'),
        sa.CheckConstraint("fetch_type IN ('html', 'pdf')", name='sources_fetch_type_check'),
        sa.CheckConstraint("check_frequency IN ('daily', 'weekly', 'custom')", name='sources_check_frequency_check'),
        sa.UniqueConstraint('url', 'country', 'visa_type', name='sources_url_unique'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for sources
    op.create_index('idx_sources_country_visa', 'sources', ['country', 'visa_type'], unique=False)
    op.create_index('idx_sources_is_active', 'sources', ['is_active'], unique=False)
    op.create_index('idx_sources_last_checked', 'sources', ['last_checked_at'], unique=False)
    op.create_index('idx_sources_metadata', 'sources', ['metadata'], unique=False, postgresql_using='gin')
    
    # Create policy_versions table
    op.create_table(
        'policy_versions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Foreign key to Source'),
        sa.Column('content_hash', sa.String(length=64), nullable=False, comment='SHA256 hash of normalized content (64 hex characters)'),
        sa.Column('raw_text', sa.String(), nullable=False, comment='Full text content after normalization'),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when content was fetched'),
        sa.Column('normalized_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when normalization was applied'),
        sa.Column('content_length', sa.Integer(), nullable=False, comment='Character count of raw text'),
        sa.Column('fetch_duration', sa.Integer(), nullable=False, comment='Time taken to fetch in milliseconds'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='When this version was created'),
        sa.CheckConstraint("char_length(content_hash) = 64", name='policy_versions_hash_length_check'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for policy_versions
    op.create_index('idx_policy_versions_source_id', 'policy_versions', ['source_id'], unique=False)
    op.create_index('idx_policy_versions_content_hash', 'policy_versions', ['content_hash'], unique=False)
    op.create_index('idx_policy_versions_fetched_at', 'policy_versions', ['fetched_at'], unique=False, postgresql_ops={'fetched_at': 'DESC'})
    op.create_index('idx_policy_versions_source_fetched', 'policy_versions', ['source_id', 'fetched_at'], unique=False, postgresql_ops={'fetched_at': 'DESC'})
    
    # Create policy_changes table
    op.create_table(
        'policy_changes',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Foreign key to Source'),
        sa.Column('old_version_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Foreign key to previous PolicyVersion'),
        sa.Column('new_version_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Foreign key to new PolicyVersion'),
        sa.Column('old_hash', sa.String(length=64), nullable=False, comment='SHA256 hash of previous version'),
        sa.Column('new_hash', sa.String(length=64), nullable=False, comment='SHA256 hash of new version'),
        sa.Column('diff', sa.String(), nullable=False, comment='Text diff showing what changed'),
        sa.Column('diff_length', sa.Integer(), nullable=False, comment='Character count of diff text'),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, comment='Timestamp when change was detected'),
        sa.Column('alert_sent_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp when email alert was sent'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='When this change record was created'),
        sa.CheckConstraint("char_length(old_hash) = 64 AND char_length(new_hash) = 64", name='policy_changes_hash_length_check'),
        sa.CheckConstraint('old_hash != new_hash', name='policy_changes_hash_different_check'),
        sa.ForeignKeyConstraint(['source_id'], ['sources.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['old_version_id'], ['policy_versions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['new_version_id'], ['policy_versions.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for policy_changes
    op.create_index('idx_policy_changes_source_id', 'policy_changes', ['source_id'], unique=False)
    op.create_index('idx_policy_changes_detected_at', 'policy_changes', ['detected_at'], unique=False, postgresql_ops={'detected_at': 'DESC'})
    op.create_index('idx_policy_changes_old_hash', 'policy_changes', ['old_hash'], unique=False)
    op.create_index('idx_policy_changes_new_hash', 'policy_changes', ['new_hash'], unique=False)
    op.create_index('idx_policy_changes_source_detected', 'policy_changes', ['source_id', 'detected_at'], unique=False, postgresql_ops={'detected_at': 'DESC'})
    
    # Create route_subscriptions table
    op.create_table(
        'route_subscriptions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('origin_country', sa.String(length=2), nullable=False, comment="Origin country code (e.g., 'IN' for India)"),
        sa.Column('destination_country', sa.String(length=2), nullable=False, comment="Destination country code (e.g., 'DE' for Germany)"),
        sa.Column('visa_type', sa.String(length=50), nullable=False, comment="Type of visa (e.g., 'Student', 'Work')"),
        sa.Column('email', sa.String(length=255), nullable=False, comment='Email address to send alerts to'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'), comment='Whether subscription is active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='When subscription was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='When subscription was last modified'),
        sa.CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name='route_subscriptions_email_format_check'),
        sa.UniqueConstraint('origin_country', 'destination_country', 'visa_type', 'email', name='route_subscriptions_unique'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for route_subscriptions
    op.create_index('idx_route_subscriptions_destination_visa', 'route_subscriptions', ['destination_country', 'visa_type'], unique=False)
    op.create_index('idx_route_subscriptions_is_active', 'route_subscriptions', ['is_active'], unique=False)
    op.create_index('idx_route_subscriptions_origin_destination_visa', 'route_subscriptions', ['origin_country', 'destination_country', 'visa_type'], unique=False)
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False, comment='Unique username'),
        sa.Column('hashed_password', sa.String(length=255), nullable=False, comment='Bcrypt hashed password'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true'), comment='Whether user account is active'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='When user was created'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False, comment='When user was last modified'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True, comment='Timestamp of last login'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    
    # Create indexes for users
    op.create_index('idx_users_username', 'users', ['username'], unique=False)
    op.create_index('idx_users_is_active', 'users', ['is_active'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_users_is_active', table_name='users')
    op.drop_index('idx_users_username', table_name='users')
    op.drop_index('idx_route_subscriptions_origin_destination_visa', table_name='route_subscriptions')
    op.drop_index('idx_route_subscriptions_is_active', table_name='route_subscriptions')
    op.drop_index('idx_route_subscriptions_destination_visa', table_name='route_subscriptions')
    op.drop_index('idx_policy_changes_source_detected', table_name='policy_changes')
    op.drop_index('idx_policy_changes_new_hash', table_name='policy_changes')
    op.drop_index('idx_policy_changes_old_hash', table_name='policy_changes')
    op.drop_index('idx_policy_changes_detected_at', table_name='policy_changes')
    op.drop_index('idx_policy_changes_source_id', table_name='policy_changes')
    op.drop_index('idx_policy_versions_source_fetched', table_name='policy_versions')
    op.drop_index('idx_policy_versions_fetched_at', table_name='policy_versions')
    op.drop_index('idx_policy_versions_content_hash', table_name='policy_versions')
    op.drop_index('idx_policy_versions_source_id', table_name='policy_versions')
    op.drop_index('idx_sources_metadata', table_name='sources')
    op.drop_index('idx_sources_last_checked', table_name='sources')
    op.drop_index('idx_sources_is_active', table_name='sources')
    op.drop_index('idx_sources_country_visa', table_name='sources')
    
    # Drop tables (in reverse order of dependencies)
    op.drop_table('users')
    op.drop_table('route_subscriptions')
    op.drop_table('policy_changes')
    op.drop_table('policy_versions')
    op.drop_table('sources')

