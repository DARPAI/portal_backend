from datetime import datetime

from src.base_schema import BaseSchema
from src.darp_servers.schemas import DARPServerRead
from src.prompts.default import default_prompt
from src.settings import settings
from src.types import LLMModel
from src.types import LLMProvider


class AgentData(BaseSchema):
    name: str
    description: str | None = None
    avatar_url: str | None = None
    system_prompt: str = default_prompt
    model: LLMModel = settings.DEFAULT_LLM_MODEL


class AgentCreate(BaseSchema):
    agent_data: AgentData
    current_user_id: str
    server_ids: list[int] = settings.DEFAULT_AGENT_SERVER_IDS


class AgentRead(BaseSchema):
    id: str
    user_id: str
    name: str
    description: str | None = None
    avatar_url: str | None = None
    model: LLMModel
    provider: LLMProvider
    created_at: datetime


class AgentWithServers(AgentRead):
    darp_servers: list[DARPServerRead]


class AgentUpdateData(BaseSchema):
    name: str | None = None
    description: str | None = None
    avatar_url: str | None = None
    system_prompt: str | None = None
    model: LLMModel | None = None


class AgentUpdate(BaseSchema):
    current_user_id: str
    agent_data: AgentUpdateData | None = None
    server_ids: list[int] | None = None
