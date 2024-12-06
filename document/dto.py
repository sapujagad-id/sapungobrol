from typing import Optional

from pydantic import BaseModel
from typing_extensions import TypedDict

from document.document import (Document, DocumentTitleError, DocumentType,
                               DocumentTypeError, ObjectNameError)


class DocumentFilter(TypedDict):
  id: Optional[str]
  object_name: Optional[str]
  created_after: Optional[str] # YYYY-MM-DDThh:mm:ss or YYYY-MM-DD
  created_before: Optional[str]
  updated_after: Optional[str] 
  updated_before: Optional[str] 
  access_level: Optional[int]
  
class DocumentCreate(BaseModel):
  type: str
  title: str
  object_name: str
  access_level: int
  
  def validate(self):
    if self.type not in DocumentType._value2member_map_:
      raise DocumentTypeError
    if not self.title:
      raise DocumentTitleError
    if not self.object_name:
      raise ObjectNameError
    
    
class DocumentUpdate(TypedDict):
  id: str
  type: DocumentType
  title: str
  object_name: str
  

class DocumentResponse(Document):
  ''' '''

class AWSConfig(BaseModel):
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_public_bucket_name: str
    aws_region: str
    aws_endpoint_url: str