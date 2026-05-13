from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from models.persona import Persona


class Base(DeclarativeBase):
    pass


class ActiveSession(Base):
    __tablename__ = "active_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    active_folder: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    active_persona: Mapped[str] = mapped_column(
        String(32),
        default=Persona.TUTOR.value,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class IndexedFolder(Base):
    __tablename__ = "indexed_folders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path: Mapped[str] = mapped_column(String(1024), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    documents_indexed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunks_indexed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
