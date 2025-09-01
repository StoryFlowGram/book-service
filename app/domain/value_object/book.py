from app.domain.enum.difficulty import Difficulty
from dataclasses import dataclass

@dataclass(frozen=True)
class BookVO:

    description: str
    title: str
    difficulty: Difficulty | None

    def __post_init__(self):
        if self.difficulty is not None:
            if not isinstance(self.difficulty, Difficulty):
                try:
                    self.difficulty = Difficulty(self.difficulty)
                except Exception:
                    raise ValueError(f"Неверное значение difficulty: {self.difficulty}")
        else:
            self.difficulty = None
        if self.title.strip() == "":
            raise ValueError("Заголовок(title) не может содержать только пробелы")
        if self.description.strip() == "":
            raise ValueError("Описание(description) не может содержать только пробелы")
        

    def __str__(self):
        return self.difficulty