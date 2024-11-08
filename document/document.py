from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import UUID4, BaseModel

class DocumentTitleError(Exception):
    def __init__(self, message="Document title is required"):
        self.message = message
        super().__init__(self.message)
        
class ObjectNameError(Exception):
    def __init__(self, message="Object name is required to identify the file"):
        self.message = message
        super().__init__(self.message)
        
class DocumentTypeError(Exception):
    def __init__(self, message="Data Source Type is not valid"):
        self.message = message
        super().__init__(self.message)  

class DocumentType(str, Enum):
    CSV = "csv"
    PDF = "pdf"
    TXT = "txt"

class Document(BaseModel):
    id: UUID4
    type: DocumentType
    title: str
    object_name: str
    created_at: datetime
    updated_at: datetime
    
    def validate(self):
      if self.type not in DocumentType._value2member_map_:
        raise DocumentTypeError
      if not self.title:
        raise DocumentTitleError
      if not self.object_name:
        raise ObjectNameError
        
    def generate_presigned_url(self, object_name: str, expiration: int = 28800) -> str:
      '''
      Generates and returns a new presigned S3 URL.
      
      Parameters
      -----
      object_name (str): the object name, key identifier for the file. this is stored in the DB
      
      expiration (int): time until presigned URL expires, in seconds. default is 28800s (8 hours)
      
      Returns
      -----
      A presigned URL string for an S3 object, that does not require additional auth or API keys to access.
      
      Notes
      -----
      This method is not implemented yet.
      
      '''
      raise NotImplementedError