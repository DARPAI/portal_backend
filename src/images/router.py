from fastapi import APIRouter
from fastapi import Depends
from fastapi import File
from fastapi import Query
from fastapi import status
from fastapi import UploadFile
from fastapi.responses import RedirectResponse

from src.images.schemas import FileURL
from src.images.schemas import UploadResponseSchema
from src.images.service import ImageService


router = APIRouter(prefix="/images", tags=["Images"])


@router.get("/{filename}")
async def get_image(
    filename: str,
    width: int | None = Query(gt=0, default=None),
    height: int | None = Query(gt=0, default=None),
    service: ImageService = Depends(ImageService.get_new_instance),
) -> RedirectResponse:
    return await service.get_image(filename=filename, width=width, height=height)


@router.post("/upload_image", status_code=status.HTTP_201_CREATED, response_model=UploadResponseSchema)
async def create_upload_image(
    data: UploadFile = File(...), service: ImageService = Depends(ImageService.get_new_instance)
) -> UploadResponseSchema:
    schema = await service.upload_image_as_file(data)

    return schema


@router.post("/upload_image_by_url", status_code=status.HTTP_201_CREATED, response_model=UploadResponseSchema)
async def upload_image_by_url(
    data: FileURL, service: ImageService = Depends(ImageService.get_new_instance)
) -> UploadResponseSchema:
    schema = await service.upload_image_by_url(data.file_url)

    return schema
