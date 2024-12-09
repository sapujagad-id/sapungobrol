from typing import Optional
from pydantic import BaseModel
from typing_extensions import TypedDict

from document.document import Document, DocumentTitleError, DocumentType, DocumentTypeError, ObjectNameError

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
      if not self._validate_title():
        raise DocumentTitleError
      if not self._validate_object_name():
        raise ObjectNameError
      
  def _validate_title(self):
      return bool(self.title and self.title.strip())
  
  def _validate_object_name(self):
      stripped_object_name = self.object_name.strip()
      return bool(stripped_object_name) and ' ' not in self.object_name
    
    
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