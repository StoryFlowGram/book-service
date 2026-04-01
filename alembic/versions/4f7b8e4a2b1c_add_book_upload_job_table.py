"""add book upload job table

Revision ID: 4f7b8e4a2b1c
Revises: b880d32d1e78
Create Date: 2026-04-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "4f7b8e4a2b1c"
down_revision: Union[str, Sequence[str], None] = "b880d32d1e78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "book_upload_job",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("upload_id", sa.String(length=36), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("object_name", sa.String(length=512), nullable=True),
        sa.Column("difficulty", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="initialized"),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("result_book_id", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("difficulty BETWEEN 1 AND 6", name="ck_upload_job_difficulty"),
        sa.CheckConstraint(
            "status IN ('initialized', 'processing', 'completed', 'failed')",
            name="ck_upload_job_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("upload_id"),
    )
    op.create_index("ix_upload_job_status", "book_upload_job", ["status"], unique=False)
    op.create_index(
        "ix_upload_job_created_by_user_id",
        "book_upload_job",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index("ix_upload_job_created_at", "book_upload_job", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_upload_job_created_at", table_name="book_upload_job")
    op.drop_index("ix_upload_job_created_by_user_id", table_name="book_upload_job")
    op.drop_index("ix_upload_job_status", table_name="book_upload_job")
    op.drop_table("book_upload_job")
