from document.document import Document


def generate_presigned_url(doc_model, s3_client, bucket_name: str, expiration: int = 28800) -> str:
    """
    Generates and returns a new presigned S3 URL.

    Parameters
    -----
    doc_model: Document Model.
    s3_client: boto3 S3 client instance
        The initialized S3 client to use for URL generation.
    bucket_name (str): Name of the S3 bucket where the object is stored.
    expiration (int): Time until presigned URL expires, in seconds. Default is 28800s (8 hours).

    Returns
    -----
    A presigned URL string for an S3 object that does not require additional auth or API keys to access.

    Raises
    -----
    DocumentPresignedURLError: If generating the presigned URL fails.
    """
    document_obj = Document(**doc_model.__dict__)
    return document_obj.generate_presigned_url(s3_client, bucket_name, expiration)