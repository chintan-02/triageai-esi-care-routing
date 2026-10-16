"""Revocable sessions, private assessments, and durable report object metadata.

Unowned legacy assessments intentionally remain inaccessible to public sessions.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_sessions_storage"
down_revision = "2dc4cd53d258"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("password_hash", sa.String(), nullable=True))
    with op.batch_alter_table("assessments") as batch:
        batch.add_column(sa.Column("owner_id", sa.String(), nullable=True))
        batch.create_foreign_key("fk_assessments_owner", "users", ["owner_id"], ["id"])
        batch.create_index("ix_assessments_owner_id", ["owner_id"])
    with op.batch_alter_table("reports") as batch:
        batch.add_column(sa.Column("storage_key", sa.String(), nullable=True))
        batch.add_column(sa.Column("storage_backend", sa.String(), nullable=True))
    op.create_table("auth_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_auth_sessions_user_id", "auth_sessions", ["user_id"])
    op.create_index("ix_auth_sessions_expires_at", "auth_sessions", ["expires_at"])


def downgrade():
    op.drop_table("auth_sessions")
    with op.batch_alter_table("reports") as batch:
        batch.drop_column("storage_backend")
        batch.drop_column("storage_key")
    with op.batch_alter_table("assessments") as batch:
        batch.drop_index("ix_assessments_owner_id")
        batch.drop_constraint("fk_assessments_owner", type_="foreignkey")
        batch.drop_column("owner_id")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("password_hash")
