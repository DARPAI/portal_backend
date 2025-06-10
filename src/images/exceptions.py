from fastapi import status

from src.errors import FastApiError


class IncorrectDataError(FastApiError):
    status_code: int = status.HTTP_400_BAD_REQUEST
    message: str


class S3Error(FastApiError):
    status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE
    message: str = "It looks like S3 is not available"
