from asyncio import Queue

from mcp.types import LoggingMessageNotificationParams
from pydantic import ValidationError

from src.logger import logger
from src.messages.schemas import DeepResearchLogData
from src.messages.schemas import GenericLogData
from src.messages.schemas import ToolCallResult


class LogCollector:
    def __init__(self, queue: Queue[ToolCallResult | DeepResearchLogData | GenericLogData]) -> None:
        self.queue = queue

    async def __call__(self, params: LoggingMessageNotificationParams) -> None:
        data = params.data
        logger.debug(f"Incoming log data = {data}")
        if isinstance(data, dict):
            try:
                log_data = DeepResearchLogData.model_validate(data)
                await self.queue.put(log_data)
                return
            except ValidationError:
                pass
        await self.queue.put(GenericLogData(data=data))
