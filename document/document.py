from datetime import datetime
from enum import Enum
from pydantic import UUID4, BaseModel
from botocore.exceptions import ClientError

class DocumentTitleError(Exception):
    def __init__(self, message="Document title is required"):
        self.message = message
        super().__init__(self.message)
        
class ObjectNameError(Exception):
    def __init__(self, message="Object name is required"):
        self.message = message
        super().__init__(self.message)
        
class DocumentTypeError(Exception):
    def __init__(self, message="Data Source Type is not valid"):
        self.message = message
        super().__init__(self.message)  

class DocumentPresignedURLError(Exception):
    def __init__(self, message="Failed to generate presigned URL"):
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
    access_level: int
    
    def validate(self):
      if self.type not in DocumentType._value2member_map_:
        raise DocumentTypeError
      if not self.title:
        raise DocumentTitleError
      if not self.object_name:
        raise ObjectNameError
        
    def generate_presigned_url(self, s3_client, bucket_name: str, expiration: int = 28800) -> str:
        '''
        Generates and returns a new presigned S3 URL.

        Parameters
        -----
        s3_client: boto3 S3 client instance
            The initialized S3 client to use for URL generation.

        bucket_name (str): Name of the S3 bucket where the object is stored.

        expiration (int): time until presigned URL expires, in seconds. default is 28800s (8 hours)

        Returns
        -----
        A presigned URL string for an S3 object, that does not require additional auth or API keys to access.

        '''
        try:
            response = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': self.object_name},
                ExpiresIn=expiration
            )
            return response
        except ClientError:
            raise DocumentPresignedURLError