from abc import ABC, abstractmethod
from fastapi import Form, HTTPException, UploadFile, File
from loguru import logger
from .service import DataSourceService  # Assuming DataSourceService is your abstract class
from .service import DataSourceServiceV1  # The actual implementation

class DataSourceController(ABC):
    @abstractmethod
    def upload_file(self, file_name: str, file_content: UploadFile = File(...)) -> dict:
        pass


class DataSourceControllerV1(DataSourceController):
    GENERAL_ERROR_MESSAGE = "Something went wrong during the file upload"

    def __init__(self, service: DataSourceService) -> None:
        super().__init__()
        self.service = service

    def upload_file(self, file_name: str= Form(...), file: UploadFile = File(...)) -> dict:
        try:
            file_url = self.service.upload_file_to_s3(file, file_name)
            return {"file_url": file_url}
        
        except ValueError as e:
            logger.error(f"Value error in file upload: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
        except Exception as e:
            logger.error(f"Unexpected error during file upload: {e}")
            raise HTTPException(status_code=500, detail=self.GENERAL_ERROR_MESSAGE)
