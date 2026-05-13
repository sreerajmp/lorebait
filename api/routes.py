import logging
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_session
from core.rag import stream_persona_answer
from models.db import ActiveSession, IndexedFolder
from models.persona import Persona
from models.schemas import (
    ChatRequest,
    IndexRequest,
    IndexResponse,
    SessionResponse,
    SessionUpdateRequest,
)
from services.indexer import run_indexing_job


logger = logging.getLogger(__name__)
router = APIRouter(tags=["lorebait"])


async def get_or_create_active_session(db: AsyncSession) -> ActiveSession:
    result = await db.execute(select(ActiveSession).where(ActiveSession.id == 1))
    active_session = result.scalar_one_or_none()
    if active_session is None:
        active_session = ActiveSession(id=1, active_persona=Persona.TUTOR.value)
        db.add(active_session)
        await db.commit()
        await db.refresh(active_session)
    return active_session


def resolve_directory(directory_path: str) -> Path:
    path = Path(directory_path).expanduser().resolve()
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Directory does not exist: {path}",
        )
    if not path.is_dir():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Path is not a directory: {path}",
        )
    return path


@router.post("/index", response_model=IndexResponse, status_code=status.HTTP_202_ACCEPTED)
async def index_directory(
    payload: IndexRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
) -> IndexResponse:
    directory = resolve_directory(payload.directory_path)
    directory_key = str(directory)

    active_session = await get_or_create_active_session(db)
    active_session.active_folder = directory_key

    folder_result = await db.execute(
        select(IndexedFolder).where(IndexedFolder.path == directory_key)
    )
    indexed_folder = folder_result.scalar_one_or_none()
    if indexed_folder is None:
        indexed_folder = IndexedFolder(path=directory_key)
        db.add(indexed_folder)

    indexed_folder.status = "queued"
    indexed_folder.last_error = None
    await db.commit()

    background_tasks.add_task(run_indexing_job, directory_key)
    logger.info("Queued indexing job for %s", directory_key)

    return IndexResponse(
        status="queued",
        directory_path=directory_key,
        message="Indexing has started in the background.",
    )


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_session),
) -> StreamingResponse:
    active_session = await get_or_create_active_session(db)

    persona = payload.persona or Persona(active_session.active_persona)
    folder_path = payload.folder_path or active_session.active_folder
    if folder_path is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active folder is set. Call /index first or pass folder_path.",
        )

    directory = resolve_directory(folder_path)

    if payload.persona is not None:
        active_session.active_persona = payload.persona.value
    if payload.folder_path is not None:
        active_session.active_folder = str(directory)
    await db.commit()

    logger.info("Starting chat stream for persona=%s folder=%s", persona.value, directory)
    stream = stream_persona_answer(
        question=payload.message,
        persona=persona,
        folder_path=str(directory),
        top_k=payload.top_k,
    )
    return StreamingResponse(stream, media_type="text/plain; charset=utf-8")


@router.get("/session", response_model=SessionResponse)
async def get_active_session(db: AsyncSession = Depends(get_session)) -> SessionResponse:
    active_session = await get_or_create_active_session(db)
    return SessionResponse(
        active_folder=active_session.active_folder,
        active_persona=Persona(active_session.active_persona),
    )


@router.patch("/session", response_model=SessionResponse)
async def update_active_session(
    payload: SessionUpdateRequest,
    db: AsyncSession = Depends(get_session),
) -> SessionResponse:
    active_session = await get_or_create_active_session(db)

    if payload.active_folder is not None:
        directory = resolve_directory(payload.active_folder)
        active_session.active_folder = str(directory)
    if payload.active_persona is not None:
        active_session.active_persona = payload.active_persona.value

    await db.commit()
    await db.refresh(active_session)
    return SessionResponse(
        active_folder=active_session.active_folder,
        active_persona=Persona(active_session.active_persona),
    )
