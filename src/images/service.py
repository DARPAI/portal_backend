import asyncio
import hashlib
import io
from collections.abc import Buffer
from pathlib import Path
from typing import Any
from typing import Self

from fastapi import Depends
from fastapi import status
from fastapi import UploadFile
from fastapi.responses import RedirectResponse
from httpx import AsyncClient
from PIL import Image as PILImage
from PIL import ImageOps

from src.images.dependencies import get_s3_client
from src.images.exceptions import IncorrectDataError
from src.images.exceptions import S3Error
from src.images.repository import ImageRepository
from src.images.schemas import UploadResponseSchema
from src.images.types import Names
from src.logger import logger
from src.settings import settings

IMAGE_DEFAULT_FORMAT = "PNG"


class ImageService:
    def __init__(self, image_repository: ImageRepository, s3_client):
        self.image_repository = image_repository
        self.s3_client = s3_client
        self.httpx_client = AsyncClient(trust_env=False)

    async def get_image(self, filename: str, width: int | None = None, height: int | None = None) -> RedirectResponse:
        if width is None and height is None:
            url = self._build_image_url(filename)
            return RedirectResponse(url, status.HTTP_303_SEE_OTHER)

        if not width or not height:
            raise IncorrectDataError("Invalid dimensions")

        assert width and height  # Just only for mypy

        existing_image = await self.get_existing_image_url(filename=filename, width=width, height=height)

        if existing_image is not None:
            logger.debug("Found existing image for %s and %dx%d", filename, width, height)
            return existing_image

        return await self.create_resized_image(filename=filename, width=width, height=height)

    async def get_existing_image_url(
        self,
        filename: str,
        width: int,
        height: int,
    ) -> RedirectResponse | None:
        names = self.get_names(filename=filename, width=width, height=height)
        resized_image = await self.image_repository.get_image_by_url(names.resized_image_url)

        if resized_image is not None:
            logger.debug("Found image in db: %dx%d", width, height)
            return RedirectResponse(names.resized_image_url, status.HTTP_303_SEE_OTHER)

        return None

    async def create_resized_image(self, filename: str, width: int, height: int) -> RedirectResponse:
        logger.debug("Creating resized image for %s and %dx%d", filename, width, height)
        names: Names = self.get_names(filename, width, height)
        image: io.BytesIO = await self._load_image(filename)
        resized_image: io.BytesIO = await self._resize_image(image, width, height)

        image.close()

        image_bytes = resized_image.getvalue()
        await self._upload_to_s3(body=image_bytes, key=names.resized_image_name)
        resized_image.close()

        await self.image_repository.insert_image(
            url=names.resized_image_url,
            original_url=names.original_url,
            width=width,
            height=height,
            image_hash=None,
            size=len(image_bytes),
        )

        return RedirectResponse(names.resized_image_url, status.HTTP_303_SEE_OTHER)

    async def upload_image_as_file(self, file: UploadFile) -> UploadResponseSchema:
        image_bytes = await file.read()
        image_hash = await self._compute_image_hash(image_bytes)
        image_name = self._build_image_name_by_file(image_hash, file)

        return await self.upload_image(
            filename=image_name, contents=image_bytes, image_hash=image_hash, size=len(image_bytes)
        )

    async def upload_image_by_url(self, file_url: str) -> UploadResponseSchema:
        response = await self.httpx_client.get(file_url)
        image_hash = await self._compute_image_hash(response.content)
        image_name = self._build_image_name_by_url(image_hash, file_url)

        return await self.upload_image(
            filename=image_name,
            contents=response.content,
            image_hash=image_hash,
            size=len(response.content),
        )

    async def upload_image(
        self,
        filename: str,
        contents: bytes,
        image_hash: str,
        size: int,
    ) -> UploadResponseSchema:
        existed_image = await self.image_repository.get_image(image_hash, size)

        if existed_image:
            logger.debug("Found existing image")
            return UploadResponseSchema(
                src=existed_image.url,
                width=existed_image.width,
                height=existed_image.height,
            )

        image = PILImage.open(io.BytesIO(contents))
        width, height = image.size

        logger.debug("Uploading %s to S3", filename)
        await self._upload_to_s3(
            body=contents,
            key=filename,
        )

        url = self._build_image_url(filename)

        await self.image_repository.insert_image(
            url=url, original_url=url, image_hash=image_hash, width=width, height=height, size=size
        )

        return UploadResponseSchema(src=url, width=width, height=height)

    def get_names(self, filename: str, width: int, height: int) -> Names:
        resized_image_name = self.get_resized_image_name(filename, width, height)
        resized_image_url = self._build_image_url(resized_image_name)
        original_image_url = self._build_image_url(filename)

        return Names(
            resized_image_url=resized_image_url,
            original_url=original_image_url,
            resized_image_name=resized_image_name,
        )

    @staticmethod
    async def _resize_image(image: io.BytesIO, width: int, height: int) -> io.BytesIO:
        resized_image = io.BytesIO()
        with PILImage.open(image) as input_image:
            await asyncio.to_thread(ImageOps.exif_transpose, image=input_image, in_place=True)
            await asyncio.to_thread(input_image.thumbnail, (width, height), PILImage.Resampling.LANCZOS)
            input_image.save(resized_image, format=IMAGE_DEFAULT_FORMAT)
        image.close()

        return resized_image

    async def _upload_to_s3(self, body: bytes, key: str) -> None:
        await asyncio.to_thread(
            self.s3_client.put_object,
            Body=body,
            Bucket=settings.S3_BUCKET,
            Key=key,
        )

    @staticmethod
    def get_resized_image_name(name: str, width: int, height: int) -> str:
        return f"{name}_w{width}_h{height}"

    @staticmethod
    def _build_image_url(filename: str) -> str:
        return f"{settings.CDN_BASE_URL}/{filename}"

    @staticmethod
    def _build_image_name_by_file(image_hash: str, file: UploadFile) -> str:
        return f"{image_hash}{Path(file.filename).suffix}"

    @staticmethod
    def _build_image_name_by_url(image_hash: str, url: str) -> str:
        return f"{image_hash}{Path(url).suffix}"

    async def _load_image(self, filename: str) -> io.BytesIO:
        image = io.BytesIO()

        try:
            await asyncio.to_thread(self.s3_client.download_fileobj, settings.S3_BUCKET, filename, image)
        except Exception as error:
            logger.error("Download file error", exc_info=error)
            raise S3Error()

        return image

    @staticmethod
    async def _compute_image_hash(string: Buffer) -> str:
        sha1 = await asyncio.to_thread(hashlib.sha1, string)
        return sha1.hexdigest()

    @classmethod
    def get_new_instance(
        cls,
        image_repository: Any = Depends(ImageRepository.get_new_instance),
        s3_client: Any = Depends(get_s3_client),
    ) -> Self:
        return cls(image_repository=image_repository, s3_client=s3_client)
