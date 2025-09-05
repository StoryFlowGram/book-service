from sqlalchemy.orm import Mapped, mapped_column, relationship, validates
from sqlalchemy.types import Integer, String, Text
from sqlalchemy import CheckConstraint, UniqueConstraint, Index
from app.infrastructure.database.base import Base
from app.domain.enum.difficulty import Difficulty

class Book(Base):
    __tablename__ = 'book'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String, nullable=False) 
    author: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    pic_url: Mapped[str] = mapped_column(String, nullable=True)
    difficulty: Mapped[Difficulty] = mapped_column(Integer, nullable=True)
    
    chapters = relationship("Chapter", back_populates="book")

    @validates("title")
    def title_validates(self, key, title: str):
        max_lenth = 255
        if title is None:
            raise ValueError("title пустой")
        elif len(title) >= max_lenth:
            raise ValueError(f"title не может содержать {max_lenth} длинный")
        elif not title.strip():
            raise ValueError("title содержит только пробелы")
        return title
    
    @validates("author")
    def validate_author(self, key, author: str):
        max_lenth = 255
        if author is None:
            raise ValueError("author пустой")
        elif len(author) > max_lenth:
            raise ValueError(f"author не может содержать {max_lenth} длинный")
        elif not author.strip():
            raise ValueError("author содержит только пробелы")
        return author
        

    @validates("difficulty")
    def validate_difficulty(self, key, value):
        if value is None:
            return None
        
        if isinstance(value, Difficulty):
            return value.value

        if isinstance(value, int):
            try:
                return Difficulty(value)
            except ValueError:
                raise ValueError(f"Неверное значение для diffculty: {value}. \n"
                                "ожидалось тип int и число от 1 до 6")
            
        else:
            raise ValueError(f"Неверный тип для difficulty")
        
    __table_args__ = (
        UniqueConstraint("title", "author", name="uq_book_title_author"),
        CheckConstraint("title <> ''",   name='ck_book_title_not_empty'),
        CheckConstraint("author <> ''", name='ck_book_author_not_empty'),
        CheckConstraint("difficulty BETWEEN 1 AND 6", name='ck_book_difficulty'),
        Index('ix_book_difficulty', 'difficulty'),
    )

    def __repr__(self):
        return f"Book(id={self.id}, title={self.title}, author={self.author}, difficulty={self.difficulty})"