import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sqlalchemy import select

from core.config import Settings, get_settings
from core.database import async_session_factory
from core.vector_store import LanceVectorStore
from models.db import IndexedFolder

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

try:
    from langchain_community.document_loaders import (
        TextLoader,
        UnstructuredMarkdownLoader,
        UnstructuredPDFLoader,
    )
except ImportError as exc:
    raise RuntimeError(
        "Install langchain-community and unstructured to parse local documents"
    ) from exc


logger = logging.getLogger(__name__)

SUPPORTED_SUFFIXES = {".pdf", ".md", ".markdown", ".txt"}
SKIP_DIRS = {".git", ".lorebait_data", "__pycache__", "node_modules", ".venv", "venv"}


@dataclass(frozen=True)
class IndexingResult:
    documents_indexed: int
    chunks_indexed: int


class Indexer:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.vector_store = LanceVectorStore(self.settings)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.chunk_size,
            chunk_overlap=self.settings.chunk_overlap,
        )

    async def index_directory(self, directory_path: str) -> IndexingResult:
        return await asyncio.to_thread(self._index_directory_sync, directory_path)

    def _index_directory_sync(self, directory_path: str) -> IndexingResult:
        directory = Path(directory_path).expanduser().resolve()
        if not directory.exists():
            raise FileNotFoundError(f"Directory does not exist: {directory}")
        if not directory.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {directory}")

        logger.info("Scanning %s for supported documents", directory)
        documents = list(self._load_documents(directory))
        logger.info("Loaded %s documents from %s", len(documents), directory)

        chunks = self._chunk_documents(documents)
        chunks_indexed = self.vector_store.replace_documents(str(directory), chunks)
        return IndexingResult(
            documents_indexed=len(documents),
            chunks_indexed=chunks_indexed,
        )

    def _iter_supported_files(self, directory: Path) -> Iterable[Path]:
        for path in directory.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES:
                yield path

    def _load_documents(self, directory: Path) -> Iterable[Document]:
        for file_path in self._iter_supported_files(directory):
            try:
                for document in self._load_file(file_path):
                    document.metadata.update(
                        {
                            "source": str(file_path),
                            "filename": file_path.name,
                            "relative_path": str(file_path.relative_to(directory)),
                            "folder_path": str(directory),
                        }
                    )
                    yield document
            except Exception:
                logger.exception("Failed to load %s; skipping file", file_path)

    def _load_file(self, file_path: Path) -> list[Document]:
        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            loader = UnstructuredPDFLoader(str(file_path))
        elif suffix in {".md", ".markdown"}:
            loader = UnstructuredMarkdownLoader(str(file_path))
        else:
            loader = TextLoader(str(file_path), encoding="utf-8", autodetect_encoding=True)
        return loader.load()

    def _chunk_documents(self, documents: list[Document]) -> list[Document]:
        chunks = self.splitter.split_documents(documents)
        for index, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = index
        return chunks


async def run_indexing_job(directory_path: str) -> None:
    logger.info("Indexing job started for %s", directory_path)
    async with async_session_factory() as db:
        result = await db.execute(select(IndexedFolder).where(IndexedFolder.path == directory_path))
        indexed_folder = result.scalar_one_or_none()
        if indexed_folder is None:
            indexed_folder = IndexedFolder(path=directory_path)
            db.add(indexed_folder)

        indexed_folder.status = "indexing"
        indexed_folder.last_error = None
        await db.commit()

        try:
            result = await Indexer().index_directory(directory_path)
        except Exception as exc:
            logger.exception("Indexing job failed for %s", directory_path)
            indexed_folder.status = "failed"
            indexed_folder.last_error = str(exc)
            await db.commit()
            return

        indexed_folder.status = "completed"
        indexed_folder.documents_indexed = result.documents_indexed
        indexed_folder.chunks_indexed = result.chunks_indexed
        indexed_folder.last_error = None
        await db.commit()
        logger.info(
            "Indexing job completed for %s: documents=%s chunks=%s",
            directory_path,
            result.documents_indexed,
            result.chunks_indexed,
        )
