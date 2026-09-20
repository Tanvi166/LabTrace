"""Initial Schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-19 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='RESEARCHER'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='CREATED'),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('framework', sa.String(length=100), nullable=True),
        sa.Column('python_version', sa.String(length=50), nullable=True),
        sa.Column('reproducibility_score', sa.Float(), nullable=True),
        sa.Column('user_id', sa.String(length=36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # ExperimentFiles table
    op.create_table(
        'experiment_files',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('experiment_id', sa.String(length=36), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('safe_filename', sa.String(length=255), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=50), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=True),
        sa.Column('file_extension', sa.String(length=20), nullable=True),
        sa.Column('storage_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('sha256_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # AnalysisRuns table
    op.create_table(
        'analysis_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('experiment_id', sa.String(length=36), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('extracted_metadata', sa.JSON(), nullable=True),
        sa.Column('findings', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('experiment_id', sa.String(length=36), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('analysis_run_id', sa.String(length=36), sa.ForeignKey('analysis_runs.id'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('content_markdown', sa.Text(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=True),
        sa.Column('structured_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )

    # AgentLogs table
    op.create_table(
        'agent_logs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('analysis_run_id', sa.String(length=36), sa.ForeignKey('analysis_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('execution_time_seconds', sa.Float(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('structured_output', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )

def downgrade() -> None:
    op.drop_table('agent_logs')
    op.drop_table('reports')
    op.drop_table('analysis_runs')
    op.drop_table('experiment_files')
    op.drop_table('experiments')
    op.drop_table('users')
