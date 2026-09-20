"""add structured experiment runs

Revision ID: 002_add_experiment_runs
Revises: 001_initial_schema
"""

from alembic import op
import sqlalchemy as sa


revision = "002_add_experiment_runs"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "experiment_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("experiment_id", sa.String(length=36), sa.ForeignKey("experiments.id"), nullable=False),
        sa.Column("run_id", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=True),
        sa.Column("dataset_version", sa.String(length=255), nullable=True),
        sa.Column("random_seed", sa.Integer(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("result_metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_experiment_runs_experiment_id", "experiment_runs", ["experiment_id"])
    op.create_index("ix_experiment_runs_run_id", "experiment_runs", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_experiment_runs_run_id", table_name="experiment_runs")
    op.drop_index("ix_experiment_runs_experiment_id", table_name="experiment_runs")
    op.drop_table("experiment_runs")
