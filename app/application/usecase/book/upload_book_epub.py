import uuid
from fastapi import UploadFile
from loguru import logger

from app.application.interfaces.storage import AbstractStorage
from app.application.interfaces.task_broker import AbstractEpubProcessor

class UploadBookEpubUsecase:
    def __init__(
        self, 
        storage: AbstractStorage,      
        processor: AbstractEpubProcessor    
    ):
        self.storage = storage
        self.processor = processor

    async def __call__(self, file: UploadFile, difficulty: int | None, admin_email: str) -> dict:
        object_name = f"temp_epubs/{uuid.uuid4()}_{file.filename}"
        
        try:
            logger.info(f"Админ {admin_email} инициировал загрузку: {object_name}")
            
            file.file.seek(0)
            s3_url = await self.storage.upload_fileobj(file.file, object_name)
            logger.info(f"Загружено в хранилище: {s3_url}")
            
            await self.processor.send_to_process(object_name, difficulty)
            
            return {
                "status": "success", 
                "message": "Книга загружена и отправлена на обработку",
                "file_id": object_name
            }
            
        except Exception as e:
            logger.error(f"Ошибка в UploadBookEpubUsecase: {str(e)}")
            await self.storage.delete_object(object_name)
            raise e