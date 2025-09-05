from sqlalchemy.orm import relationship, Mapped, mapped_column, validates
from sqlalchemy import ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.types import Integer, String, Text
from app.infrastructure.database.base import Base



class Chapter(Base):
    __tablename__ = 'chapter'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("book.id"))
    title: Mapped[str] = mapped_column(String(length=255), nullable=False)
    order_number: Mapped[int] = mapped_column(Integer, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    s3_url: Mapped[str] = mapped_column(String, nullable=False)

    book = relationship("Book", back_populates="chapters")


    __table_args__ = (
        UniqueConstraint('book_id', 'order_number', name='uq_chapter_book_title'),
        CheckConstraint("title <> ''",   name='ck_chapter_title_not_empty'),
        Index('ix_chapter_book_id', 'book_id'),
    )
