"""add scraper job progress columns"""

from alembic import op
import sqlalchemy as sa


revision = "0002_job_progress_fields"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jobs", sa.Column("progress", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("jobs", sa.Column("pages_processed", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("jobs", sa.Column("records_found", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("jobs", sa.Column("output_paths", sa.JSON(), nullable=True))

    op.alter_column("jobs", "progress", server_default=None)
    op.alter_column("jobs", "pages_processed", server_default=None)
    op.alter_column("jobs", "records_found", server_default=None)


def downgrade() -> None:
    op.drop_column("jobs", "output_paths")
    op.drop_column("jobs", "records_found")
    op.drop_column("jobs", "pages_processed")
    op.drop_column("jobs", "progress")
