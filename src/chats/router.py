from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from fastapi_pagination import add_pagination
from fastapi_pagination import Page
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette import EventSourceResponse

from .schemas import ChatCreate
from .schemas import ChatRead
from .schemas import ChatUpdate
from .service import ChatService
from src.database import Chat
from src.database import get_session
from src.database import manage_stream_session
from src.database import Message
from src.errors import InvalidData
from src.messages.schemas import MessageCreate
from src.messages.schemas import MessageRead
from src.messages.service import MessageService
from src.users.dependencies import valid_current_user_id

router = APIRouter(prefix="/chats")

add_pagination(router)


@router.get("/{chat_id}", response_model=ChatRead)
async def get_single_chat(
    chat_id: str,
    current_user_id: str = Depends(valid_current_user_id),
    service: ChatService = Depends(ChatService.get_new_instance),
) -> Chat:
    return await service.get_single_chat(chat_id=chat_id, current_user_id=current_user_id)


@router.put("/{chat_id}", response_model=ChatRead)
async def update_chat(
    chat_id: str, data: ChatUpdate, service: ChatService = Depends(ChatService.get_new_instance)
) -> Chat:
    return await service.update_chat(chat_id=chat_id, data=data)


@router.get("/", response_model=Page[ChatRead])
async def list_chats(
    current_user_id: str = Depends(valid_current_user_id),
    params: Params = Depends(),
    session: AsyncSession = Depends(get_session),
    service: ChatService = Depends(ChatService.get_new_instance),
) -> Page[Chat]:
    chats: Select = await service.get_chats(user_id=current_user_id)
    return await paginate(session, chats, params)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ChatRead)
async def create_chat(data: ChatCreate, service: ChatService = Depends(ChatService.get_new_instance)) -> Chat:
    return await service.create_chat(creation_data=data)


@router.delete("/{chat_id}")
async def delete_chat(
    chat_id: str,
    current_user_id: str = Depends(valid_current_user_id),
    service: ChatService = Depends(ChatService.get_new_instance),
) -> None:
    return await service.delete_chat(chat_id=chat_id, current_user_id=current_user_id)


@router.get("/{chat_id}/messages", response_model=Page[MessageRead])
async def get_chat_messages(
    chat_id: str,
    current_user_id: str = Depends(valid_current_user_id),
    params: Params = Depends(),
    session: AsyncSession = Depends(get_session),
    service: MessageService = Depends(MessageService.get_new_instance),
) -> Page[Message]:
    agents: Select = await service.get_messages(chat_id=chat_id, user_id=current_user_id)
    return await paginate(session, agents, params)


@router.post("/{chat_id}/messages")
async def create_message(
    chat_id: str, data: MessageCreate, service: MessageService = Depends(MessageService.get_new_instance)
) -> EventSourceResponse:
    if not data.data.text:
        raise InvalidData("Text must be present")
    agent = await service.new_message_agent(chat_id=chat_id, current_user_id=data.current_user_id)
    previous_messages = await service.get_previous_messages(chat_id=chat_id)
    message = await service.create_user_message(chat_id=chat_id, creation_data=data, agent=agent)
    tool_manager = await service.get_tool_manager(query=data.data.text, routing=data.routing, agent=agent)
    stream_generator = service.create_llm_message(
        agent=agent,
        tool_manager=tool_manager,
        previous_messages=previous_messages + [message],
        chat_id=chat_id,
        current_user_id=data.current_user_id,
    )
    return EventSourceResponse(manage_stream_session(stream_generator, service.repo.session))
