"""Shared request counters, workspace quotas and resumable demo retention."""
from alembic import op
import sqlalchemy as sa

revision = "0003_demo_controls"
down_revision = "0002_sessions_storage"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("is_demo", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("cleanup_pending", sa.Boolean(), nullable=False, server_default=sa.false()))
        for name in ["assessment_count", "report_count", "review_count"]:
            batch.add_column(sa.Column(name, sa.Integer(), nullable=False, server_default="0"))
    # Prior public accounts used these roles; privileged/legacy accounts stay preserved.
    op.execute("UPDATE users SET is_demo = true WHERE role IN ('Doctor', 'Nurse')")
    op.execute("UPDATE users SET assessment_count = (SELECT COUNT(*) FROM assessments WHERE assessments.owner_id = users.id)")
    op.execute("UPDATE users SET report_count = (SELECT COUNT(*) FROM reports JOIN assessments ON reports.assessment_id = assessments.id WHERE assessments.owner_id = users.id)")
    op.execute("UPDATE users SET review_count = (SELECT COUNT(*) FROM clinician_reviews JOIN assessments ON clinician_reviews.assessment_id = assessments.id WHERE assessments.owner_id = users.id)")
    op.create_table("rate_buckets",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=False),
    )
    op.create_index("ix_rate_buckets_expires_at", "rate_buckets", ["expires_at"])


def downgrade():
    op.drop_table("rate_buckets")
    with op.batch_alter_table("users") as batch:
        for name in ["review_count", "report_count", "assessment_count", "cleanup_pending", "is_demo"]:
            batch.drop_column(name)
