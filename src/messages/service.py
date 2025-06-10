import json
from collections.abc import AsyncGenerator
from typing import Any
from typing import Self

from fastapi import Depends
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat import ChatCompletionMessageToolCall
from sqlalchemy import Select

from ..darp_servers.registry_client import RegistryClient
from .constants import provider_to_client
from .repository import MessageRepository
from .schemas import AssistantMessage
from .schemas import Event
from .schemas import MessageCreate
from .schemas import MessageCreateData
from .schemas import MessageRead
from .schemas import ToolCallData
from .types import EventType
from .types import MessageSource
from src.agents.repository import AgentRepository
from src.chats.repository import ChatRepository
from src.darp_servers.manager import ToolManager
from src.darp_servers.repository import DARPServerRepository
from src.database import Agent
from src.database import Message
from src.errors import InvalidData
from src.errors import NotFoundError
from src.llm_clients import OpenAIClient
from src.llm_clients import TextChunkData
from src.logger import logger


class MessageService:
    def __init__(
        self,
        repo: MessageRepository,
        chat_repo: ChatRepository,
        agent_repo: AgentRepository,
        server_repo: DARPServerRepository,
        registry_client: RegistryClient,
    ) -> None:
        self.repo = repo
        self.chat_repo = chat_repo
        self.agent_repo = agent_repo
        self.server_repo = server_repo
        self.registry_client = registry_client

    async def get_messages(self, chat_id: str, user_id: str) -> Select:
        existing_chat = await self.chat_repo.chat_exists(chat_id=chat_id, user_id=user_id)
        if not existing_chat:
            raise NotFoundError("Chat with this id does not exist")
        return await self.repo.get_messages(chat_id=chat_id)

    async def new_message_agent(self, chat_id: str, current_user_id: str) -> Agent:
        chat = await self.chat_repo.get_chat(chat_id=chat_id, user_id=current_user_id)
        if not chat:
            raise NotFoundError("Chat with this id does not exist")
        agent = await self.agent_repo.get_agent_by_chat_id(chat_id=chat_id)
        return agent

    async def create_user_message(self, chat_id: str, creation_data: MessageCreate, agent: Agent) -> Message:
        if not creation_data.data.text:
            raise InvalidData("User message must contain text")
        message = await self.repo.create_user_message(chat_id=chat_id, creation_data=creation_data, agent=agent)
        return message

    async def get_previous_messages(self, chat_id: str) -> list[Message]:
        messages_query = await self.repo.get_messages(chat_id, order="asc")
        messages = (await self.repo.session.execute(messages_query)).scalars().all()
        return list(messages)

    def get_formatted_messages(self, messages: list[Message]) -> list[ChatCompletionMessageParam]:
        formatted_messages: list[ChatCompletionMessageParam] = []
        for message in messages:
            formatted_messages += self.format_message_for_llm(message)
        return formatted_messages

    @staticmethod
    def format_message_for_llm(message: Message) -> list[ChatCompletionMessageParam]:
        llm_messages: list[ChatCompletionMessageParam] = []
        if message.source != MessageSource.llm:
            return message.content  # type: ignore
        for content in message.content:
            assistant_message = AssistantMessage.model_validate(content).model_dump()
            llm_messages.append(assistant_message)  # type: ignore
        return llm_messages

    async def create_llm_message(
        self,
        agent: Agent,
        chat_id: str,
        current_user_id: str,
        previous_messages: list[Message],
        tool_manager: ToolManager,
    ) -> AsyncGenerator[str, Any]:
        last_message = previous_messages[-1]
        if last_message.source == MessageSource.user:
            message_data = MessageRead.model_validate(last_message)
            yield Event(event_type=EventType.message_creation, data=message_data).model_dump_json()
        # Initial LLM message
        llm_client: OpenAIClient = provider_to_client[agent.provider]
        conversation = self.get_formatted_messages(previous_messages)
        llm_stream = await llm_client.stream(
            model=agent.model, conversation=conversation, tools=tool_manager.tools, system_prompt=agent.system_prompt
        )
        collected_text_message = []
        tool_calls = []
        db_tool_calls: list[ToolCallData] = []
        async for chunk in llm_stream:
            if isinstance(chunk, TextChunkData):
                collected_text_message.append(chunk.content)
                data = TextChunkData(content=chunk.content)
                yield Event(event_type=EventType.text_chunk, data=data).model_dump_json()
                continue
            for tool_call in chunk:
                logger.info(tool_call)
                tool_call_data = tool_manager.format_tool_call(tool_call)
                yield Event(event_type=EventType.tool_call, data=tool_call_data).model_dump_json()
                tool_calls.append(tool_call)
                db_tool_calls.append(tool_call_data)
        llm_message_text = "".join(collected_text_message) if collected_text_message else None
        llm_message = await self.repo.create_llm_message(
            chat_id=chat_id,
            agent=agent,
            tool_calls=tool_manager.rename_tool_calls(db_tool_calls),
            creation_data=MessageCreate(current_user_id=current_user_id, data=MessageCreateData(text=llm_message_text)),
        )
        llm_message_data = MessageRead.model_validate(llm_message)
        yield Event(event_type=EventType.message_creation, data=llm_message_data).model_dump_json()
        if tool_calls:
            stream = self.handle_tool_calls(
                agent=agent,
                tool_calls=tool_calls,
                tool_manager=tool_manager,
                chat_id=chat_id,
                current_user_id=current_user_id,
                conversation=previous_messages + [llm_message],
            )
            async for new_chunk in stream:
                yield new_chunk

    async def handle_tool_calls(
        self,
        agent: Agent,
        tool_calls: list[ChatCompletionMessageToolCall],
        tool_manager: ToolManager,
        chat_id: str,
        current_user_id: str,
        conversation: list[Message],
    ) -> AsyncGenerator[str, Any]:
        call_result_messages = []
        for tool_call in tool_calls:
            tool_call_result = await tool_manager.handle_tool_call(tool_call)
            yield Event(event_type=EventType.tool_call_result, data=tool_call_result).model_dump_json()
            tool_result_message = await self.repo.create_tool_message(
                chat_id=chat_id,
                agent=agent,
                tool_call_id=tool_call.id,
                tool_call_result=json.dumps(tool_call_result.result),
                current_user_id=current_user_id,
            )
            call_result_messages.append(tool_result_message)
            message_data = MessageRead.model_validate(tool_result_message)
            yield Event(event_type=EventType.message_creation, data=message_data).model_dump_json()
        # Follow up llm message
        new_event_stream = self.create_llm_message(
            agent=agent,
            chat_id=chat_id,
            current_user_id=current_user_id,
            previous_messages=conversation + call_result_messages,
            tool_manager=tool_manager,
        )
        async for new_chunk in new_event_stream:
            yield new_chunk

    async def get_tool_manager(self, query: str, routing: bool, agent: Agent) -> ToolManager:
        if routing:
            registry_servers = await self.registry_client.get_fitting_servers(query=query)
            await self.server_repo.upsert_servers(servers=registry_servers)
            string_ids = [str(server.id) for server in registry_servers]
            servers = await self.server_repo.get_servers_by_ids(server_ids=string_ids)
        else:
            servers = await self.server_repo.get_servers_by_agent(agent_id=agent.id)
        return ToolManager(darp_servers=servers)

    @classmethod
    def get_new_instance(
        cls,
        repo: MessageRepository = Depends(MessageRepository.get_new_instance),
        chat_repo: ChatRepository = Depends(ChatRepository.get_new_instance),
        agent_repo: AgentRepository = Depends(AgentRepository.get_new_instance),
        server_repo: DARPServerRepository = Depends(DARPServerRepository.get_new_instance),
        registry_client: RegistryClient = Depends(RegistryClient.get_new_instance),
    ) -> Self:
        return cls(
            repo=repo,
            chat_repo=chat_repo,
            agent_repo=agent_repo,
            server_repo=server_repo,
            registry_client=registry_client,
        )
