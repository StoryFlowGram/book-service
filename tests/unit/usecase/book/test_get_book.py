import pytest
from app.application.usecase.book.get_book import GetBookUsecase
from app.application.dto.book.book import BookDTO
from app.domain.protocols.book_protocol import AbstractBookProtocol

@pytest.mark.asyncio
async def test_get_book_success(
    get_book_usecase: GetBookUsecase, 
    sample_book_entity: BookDTO, 
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.get.return_value = sample_book_entity
    
    result = await get_book_usecase(sample_book_entity.id)
    
    book_protocol_mock.get.assert_called_once_with(sample_book_entity.id)
    assert isinstance(result, BookDTO)
    assert result.title == sample_book_entity.title

@pytest.mark.asyncio
async def test_get_book_not_found(
    get_book_usecase: GetBookUsecase, 
    sample_book_entity: BookDTO, 
    book_protocol_mock: AbstractBookProtocol
    ) -> None:
    book_protocol_mock.get.return_value = None
    with pytest.raises(Exception, match="Книга не найдена"):
        await get_book_usecase(sample_book_entity.id)