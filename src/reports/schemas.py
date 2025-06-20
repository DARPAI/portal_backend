from datetime import datetime

from src.base_schema import BaseSchema


class ReportData(BaseSchema):
    title: str
    text: str
    message_id: str


class ReportCreateSchema(BaseSchema):
    data: ReportData
    current_user_id: str


class ReportUpdateData(BaseSchema):
    title: str | None = None
    text: str | None = None


class ReportUpdateSchema(BaseSchema):
    data: ReportUpdateData
    current_user_id: str


class ReportReadSchema(BaseSchema):
    id: str
    message_id: str
    title: str
    text: str
    creator_id: str
    created_at: datetime
    updated_at: datetime
