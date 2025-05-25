from fastapi import HTTPException
from fastapi import status


class FastApiError(HTTPException):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    message: str = "Something went wrong"

    def __init__(self, message: str | None = None, **kwargs) -> None:
        if message:
            self.message = message
        self.detail = {"message": self.message, **kwargs}


class NotFoundError(FastApiError):
    error_code = status.HTTP_404_NOT_FOUND
    message = "Entity not found"


class AlreadyExistsError(FastApiError):
    error_code = status.HTTP_400_BAD_REQUEST
    message = "Entity already exists"


class NotAllowedError(FastApiError):
    error_code = status.HTTP_403_FORBIDDEN
    message = "Not allowed"


class InvalidData(FastApiError):
    error_code = status.HTTP_400_BAD_REQUEST
    message = "One or more invalid fields"


class InternalError(FastApiError):
    pass


class RemoteServerError(FastApiError):
    error_code = status.HTTP_503_SERVICE_UNAVAILABLE
    message = "Remote server error"


class FormatError(FastApiError):
    pass
