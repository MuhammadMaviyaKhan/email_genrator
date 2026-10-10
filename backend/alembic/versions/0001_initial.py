"""initial migration

Revision ID: 0001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.create_table(
        'email_addresses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('local_part', sa.String(100), nullable=False),
        sa.Column('domain', sa.String(100), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=True),
        sa.Column('status', sa.Enum('active', 'expired', 'blocked', 'deleted', name='emailaddressstatus'), default='active', nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('emails_count', sa.Integer, default=0, nullable=False),
        sa.Column('max_emails', sa.Integer, default=100, nullable=False),
        sa.Column('is_custom', sa.Boolean, default=False, nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
    )
    op.create_index('ix_email_addresses_email', 'email_addresses', ['email'])
    op.create_index('ix_email_addresses_local_part', 'email_addresses', ['local_part'])
    op.create_index('ix_email_addresses_domain', 'email_addresses', ['domain'])
    op.create_index('ix_email_addresses_status', 'email_addresses', ['status'])

    op.create_table(
        'emails',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email_address_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('email_addresses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('message_id', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('from_address', sa.String(255), nullable=False),
        sa.Column('from_name', sa.String(255), nullable=True),
        sa.Column('to_addresses', postgresql.JSONB, nullable=True),
        sa.Column('cc_addresses', postgresql.JSONB, nullable=True),
        sa.Column('bcc_addresses', postgresql.JSONB, nullable=True),
        sa.Column('reply_to', sa.String(255), nullable=True),
        sa.Column('text_body', sa.Text, nullable=True),
        sa.Column('html_body', sa.Text, nullable=True),
        sa.Column('raw_source', sa.Text, nullable=True),
        sa.Column('headers', postgresql.JSONB, nullable=True),
        sa.Column('attachments', postgresql.JSONB, nullable=True),
        sa.Column('status', sa.Enum('received', 'read', 'deleted', 'expired', 'failed', name='emailstatus'), default='received', nullable=False),
        sa.Column('size_bytes', sa.Integer, default=0, nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('spam_score', sa.Integer, nullable=True),
        sa.Column('is_spam', sa.Boolean, default=False, nullable=False),
    )
    op.create_index('ix_emails_email_address_id', 'emails', ['email_address_id'])
    op.create_index('ix_emails_received_at', 'emails', ['received_at'])
    op.create_index('ix_emails_status', 'emails', ['status'])

    op.create_table(
        'sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email_address_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('email_addresses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('token', sa.String(255), unique=True, nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
    )
    op.create_index('ix_sessions_token', 'sessions', ['token'])
    op.create_index('ix_sessions_email_address_id', 'sessions', ['email_address_id'])

    op.create_table(
        'domains',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('domain', sa.String(255), unique=True, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_default', sa.Boolean, default=False, nullable=False),
        sa.Column('mx_record', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('emails_received', sa.Integer, default=0, nullable=False),
    )
    op.create_index('ix_domains_domain', 'domains', ['domain'])

    op.create_table(
        'rate_limits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('identifier', sa.String(255), nullable=False),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('count', sa.Integer, default=0, nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('window_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_rate_limits_identifier_endpoint', 'rate_limits', ['identifier', 'endpoint'])

    op.create_table(
        'audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('details', postgresql.JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_audit_logs_event_type', 'audit_logs', ['event_type'])
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('rate_limits')
    op.drop_table('domains')
    op.drop_table('sessions')
    op.drop_table('emails')
    op.drop_table('email_addresses')