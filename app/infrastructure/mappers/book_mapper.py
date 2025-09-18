from app.domain.entity.book import Book as BookDomain
from app.infrastructure.models.book_model import Book as BookModel


def orm_to_domain(orm: BookModel) -> BookDomain:
    return BookModel(
        id=orm.id,
        title=orm.title,
        author=orm.author,
        description=orm.description,
        pic_url=orm.pic_url,
        difficulty=orm.difficulty
    )


def domain_to_orm(domain: BookDomain):
    return BookModel(
        title=domain.title,
        author=domain.author,
        description=domain.description,
        pic_url=domain.pic_url,
        difficulty=domain.difficulty
    )