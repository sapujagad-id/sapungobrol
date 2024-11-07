from abc import ABC, abstractmethod
import io
from loguru import logger
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError, PartialCredentialsError

class DataSourceService(ABC):
    @abstractmethod
    def upload_file_to_s3(self, file_content: bytes, file_name: str) -> str:
        """Uploads a file to an S3 bucket and returns the file's URL."""
        pass


class DataSourceServiceV1(DataSourceService):
    def __init__(self, aws_access_key_id, aws_secret_access_key, bucket_name, aws_region_name):
        super().__init__()
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region_name
        )
        self.bucket_name = bucket_name
        self.logger = logger.bind(service="DataSourceService")

    def upload_file_to_s3(self, file_content: bytes, file_name: str) -> str:
        """Uploads a file to an S3 bucket and returns the file's URL."""
        try:
            # Upload file to S3
            file_content_bytes = file_content.file.read()
            file_like_object = io.BytesIO(file_content_bytes)

            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=file_like_object
            )
            # Generate file URL
            file_url = f"https://{self.bucket_name}.s3.amazonaws.com/{file_name}"
            self.logger.info(f"File '{file_name}' uploaded successfully to bucket '{self.bucket_name}'")
            return file_url
        except NoCredentialsError:
            self.logger.error("AWS credentials not found.")
            raise
        except PartialCredentialsError:
            self.logger.error("Incomplete AWS credentials.")
            raise
        except BotoCoreError as e:
            self.logger.error(f"Error uploading file to S3: {e}")
            raise
