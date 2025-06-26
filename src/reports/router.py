from fastapi import APIRouter
from fastapi import Depends
from fastapi import Path
from fastapi import Query
from fastapi import status
from fastapi_pagination import Page
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_session
from src.database import Report
from src.reports.schemas import ReportCreateSchema
from src.reports.schemas import ReportReadSchema
from src.reports.schemas import ReportUpdateSchema
from src.reports.service import ReportService

router = APIRouter(
    tags=["Reports"],
    prefix="/reports",
)


@router.get("/", response_model=Page[ReportReadSchema])
async def get_reports(
    params: Params = Depends(Params),
    creator_id: str | None = Query(
        title="Creator ID",
        default=None,
    ),
    service: ReportService = Depends(ReportService.get_new_instance),
    session: AsyncSession = Depends(get_session),
) -> Page[ReportReadSchema]:
    query: Select = await service.get_reports(creator_id=creator_id)
    return await paginate(
        session,
        query,
        params=params,
    )


@router.post("/", response_model=ReportReadSchema)
async def create_report(
    data: ReportCreateSchema,
    service: ReportService = Depends(ReportService.get_new_instance),
) -> Report:
    return await service.create_report(data)


@router.get("/{report_id}", response_model=ReportReadSchema)
async def get_report_by_id(
    report_id: str = Path(title="Report ID"),
    service: ReportService = Depends(ReportService.get_new_instance),
    current_user_id: str = Query(
        title="Current User ID",
    ),
) -> Report:
    return await service.get_report(report_id, current_user_id=current_user_id)


@router.put("/{report_id}", response_model=ReportReadSchema)
async def update_report(
    data: ReportUpdateSchema,
    report_id: str = Path(title="Report ID"),
    service: ReportService = Depends(ReportService.get_new_instance),
) -> Report:
    return await service.update_report(report_id, data)


@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
async def delete_report(
    report_id: str = Path(title="Report ID"),
    current_user_id: str = Query(title="Current User ID"),
    service: ReportService = Depends(ReportService.get_new_instance),
) -> None:
    await service.delete_report(report_id, current_user_id=current_user_id)
