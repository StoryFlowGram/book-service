import pytest
from app.application.usecase.book.delete_book import DeleteBookUsecase
from app.application.dto.book.book import BookDTO
from app.domain.protocols.book_protocol import AbstractBookProtocol


@pytest.mark.asyncio
async def test_delete_book_success(
    delete_book_usecase: DeleteBookUsecase, 
    sample_book_entity: BookDTO, 
    book_protocol_mock: AbstractBookProtocol
):
    book_protocol_mock.get.return_value = sample_book_entity
    book_protocol_mock.delete.return_value = True


    result = await delete_book_usecase(sample_book_entity.id)

    book_protocol_mock.get.assert_called_once_with(sample_book_entity.id)
    book_protocol_mock.delete.assert_called_once_with(sample_book_entity.id)
    assert result == True

    

@pytest.mark.asyncio
async def test_delete_book_not_found(
    delete_book_usecase: DeleteBookUsecase,
    sample_book_entity: BookDTO,  
    book_protocol_mock: AbstractBookProtocol
) -> None:
    book_protocol_mock.get.return_value = None

    with pytest.raises(Exception, match="Книга не найдена"):
        await delete_book_usecase(sample_book_entity.id)  

    book_protocol_mock.get.assert_called_once_with(sample_book_entity.id)
    book_protocol_mock.delete.assert_not_called()