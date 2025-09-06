from app.domain.entity.chapter import Chapter as ChapterDomain
from app.infrastructure.models.chapter_model import Chapter as ChapterModel

def orm_to_domain(orm: ChapterModel) -> ChapterDomain:
    return ChapterModel(
        id=orm.id,
        book_id = orm.book_id,
        title = orm.title,
        order_number = orm.order_number,
        word_count = orm.word_count,
        s3_url = orm.s3_url
    )


def domain_to_orm(domain: ChapterDomain) -> ChapterModel:
    return ChapterModel(
        id=domain.id,
        book_id = domain.book_id,
        title = domain.title,
        order_number = domain.order_number,
        word_count = domain.word_count,
        s3_url = domain.s3_url
    )