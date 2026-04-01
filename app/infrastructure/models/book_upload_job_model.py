from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.enum.upload_job_status import UploadJobStatus
from app.infrastructure.database.base import Base


class BookUploadJob(Base):
    __tablename__ = "book_upload_job"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_id: Mapped[str] = mapped_column(String(length=36), unique=True, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(length=255), nullable=False)
    object_name: Mapped[Optional[str]] = mapped_column(String(length=512), nullable=True)
    difficulty: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(length=32),
        nullable=False,
        default=UploadJobStatus.INITIALIZED.value,
        server_default=UploadJobStatus.INITIALIZED.value,
    )
    created_by_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    result_book_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        CheckConstraint("difficulty BETWEEN 1 AND 6", name="ck_upload_job_difficulty"),
        CheckConstraint(
            "status IN ('initialized', 'processing', 'completed', 'failed')",
            name="ck_upload_job_status",
        ),
        Index("ix_upload_job_status", "status"),
        Index("ix_upload_job_created_by_user_id", "created_by_user_id"),
        Index("ix_upload_job_created_at", "created_at"),
    )
