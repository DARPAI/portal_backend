from typing import Self

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.database import Image


class ImageRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_image(self, image_hash: str, size: int) -> Image | None:
        result = await self.session.execute(
            select(
                Image,
            ).where(Image.hash == image_hash, Image.size == size)
        )

        image = result.scalars().first()

        return image

    async def get_image_by_url(self, url: str) -> Image | None:
        result = await self.session.execute(
            select(
                Image,
            ).where(Image.url == url)
        )

        image = result.scalars().first()
        return image

    async def insert_image(
        self, url: str, original_url: str, image_hash: str | None, width: int, height: int, size: int
    ) -> Image:
        image = Image(
            url=url,
            original_url=original_url,
            hash=image_hash,
            size=size,
            width=width,
            height=height,
        )
        self.session.add(image)
        await self.session.flush()
        await self.session.refresh(image)
        await self.session.commit()

        return image

    @classmethod
    def get_new_instance(cls, session: AsyncSession = Depends(get_session)) -> Self:
        return cls(session)
