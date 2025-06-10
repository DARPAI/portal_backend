from pydantic import BaseModel


class ImageCreate(BaseModel):
    url: str


class FileURL(BaseModel):
    file_url: str


class UploadResponseSchema(BaseModel):
    src: str
    width: int
    height: int
