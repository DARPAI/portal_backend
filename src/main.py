from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agents.router import router as agents_router
from src.chats.router import router as chats_router
from src.images.router import router as images_router


@asynccontextmanager
async def lifespan(fastapi: FastAPI) -> AsyncGenerator:
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents_router)
app.include_router(chats_router)
app.include_router(images_router)


@app.get("/healthcheck")
async def healthcheck():
    return "Alive"
