from typing import Self

from fastapi import Depends
from sqlalchemy import delete
from sqlalchemy import Select
from sqlalchemy import select
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.database import Report
from src.reports.schemas import ReportCreateSchema
from src.reports.schemas import ReportUpdateSchema


class ReportRepo:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session

    async def create_report(self, data: ReportCreateSchema) -> Report:
        report_obj = Report(**data.data.model_dump(), creator_id=data.current_user_id)

        self.session.add(report_obj)
        await self.session.flush()

        return report_obj

    async def get_report(self, report_id: str) -> Report | None:
        stmt = select(
            Report,
        ).where(
            Report.id == report_id,
        )

        results = await self.session.execute(stmt)
        first_one = results.scalars().first()
        return first_one

    async def delete_report(self, report_id: str) -> None:
        await self.session.execute(
            delete(Report).where(
                Report.id == report_id,
            )
        )
        await self.session.flush()

    async def get_reports(
        self,
        creator_id: str | None = None,
    ) -> Select:
        stmt = select(Report)

        if creator_id is not None:

            stmt = stmt.where(
                Report.creator_id == creator_id,
            )

        return stmt

    async def update_report(self, report_id: str, data: ReportUpdateSchema) -> Report:
        stmt = update(Report).where(
            Report.id == report_id,
        )

        if data.data.text is not None:
            stmt = stmt.values(
                text=data.data.text,
            )

        if data.data.title is not None:
            stmt = stmt.values(
                title=data.data.title,
            )

        await self.session.execute(stmt)
        await self.session.flush()

        report = await self.get_report(report_id)
        assert report is not None
        return report

    @classmethod
    def get_new_instance(cls, session: AsyncSession = Depends(get_session)) -> Self:
        return cls(session)
