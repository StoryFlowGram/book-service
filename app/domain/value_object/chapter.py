from dataclasses import dataclass


@dataclass(frozen=True)
class ChapterVO():
    title: str | None
    content: str | None
    

    def __post_init__(self):
        if self.title is None:
            raise ValueError("Заголовок(title) не может быть пустой")
        if self.title.strip() == "":
            raise ValueError("Заголовок(title) не может содержать только пробелы")
        if self.content.strip() == "":
            raise ValueError("Содержимое(content) не может содержать только пробелы")
        if self.content is None:
            raise ValueError("Содержимое(content) не может быть пустой")
    def __str__(self):
        return f"{self.title}: {self.content[:30]}..."