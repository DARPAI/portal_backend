from typing import Self

from fastapi import Depends
from sqlalchemy import Select

from src.database import Report
from src.errors import NotAllowedError
from src.errors import NotFoundError
from src.reports.repository import ReportRepo
from src.reports.schemas import ReportCreateSchema
from src.reports.schemas import ReportUpdateSchema


class ReportService:
    def __init__(
        self,
        report_repo: ReportRepo,
    ) -> None:
        self.report_repo = report_repo

    async def create_report(self, data: ReportCreateSchema) -> Report:
        return await self.report_repo.create_report(data)

    async def delete_report(self, report_id: str, current_user_id: str) -> None:
        await self._ensure_report_exists(report_id, current_user_id)
        return await self.report_repo.delete_report(report_id)

    async def update_report(self, report_id: str, data: ReportUpdateSchema) -> Report:
        await self._ensure_report_exists(report_id, data.current_user_id)
        return await self.report_repo.update_report(
            report_id,
            data,
        )

    async def get_report(self, report_id: str, current_user_id: str) -> Report:
        report = await self._ensure_report_exists(report_id, current_user_id)
        return report

    async def get_reports(self, creator_id: str | None = None) -> Select:
        return await self.report_repo.get_reports(
            creator_id,
        )

    async def _ensure_report_exists(self, report_id: str, current_user_id: str) -> Report:
        report = await self.report_repo.get_report(report_id)

        if report is None:
            raise NotFoundError(f"Report with id = {report_id} not found")

        if report.creator_id != current_user_id:
            raise NotAllowedError("Only the creator of the report can access it")

        return report

    @classmethod
    def get_new_instance(cls, repo: ReportRepo = Depends(ReportRepo.get_new_instance)) -> Self:
        return cls(repo)
