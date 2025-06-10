import boto3

from src.settings import settings


def get_s3_client():
    session = boto3.session.Session()
    yield session.client(
        service_name="s3",
        endpoint_url=settings.S3_HOST,
        aws_access_key_id=settings.S3_ACCESS,
        aws_secret_access_key=settings.S3_SECRET,
    )
