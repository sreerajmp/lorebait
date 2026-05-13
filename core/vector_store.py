import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Any
from uuid import uuid4

import lancedb

from core.config import Settings, get_settings
from core.llm import build_embeddings


logger = logging.getLogger(__name__)


class LanceVectorStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.uri = self.settings.lancedb_uri
        Path(self.uri).mkdir(parents=True, exist_ok=True)
        self._db = lancedb.connect(self.uri)
        self._embeddings = build_embeddings(self.settings)

    @staticmethod
    def folder_id(folder_path: str) -> str:
        resolved = str(Path(folder_path).expanduser().resolve())
        return hashlib.sha256(resolved.encode("utf-8")).hexdigest()

    @property
    def table_names(self) -> set[str]:
        return set(self._db.table_names())

    def _open_table(self):
        if self.settings.lancedb_table not in self.table_names:
            return None
        return self._db.open_table(self.settings.lancedb_table)

    async def areplace_documents(self, folder_path: str, chunks: list[Any]) -> int:
        return await asyncio.to_thread(self.replace_documents, folder_path, chunks)

    async def asimilarity_search(
        self,
        folder_path: str,
        query: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        return await asyncio.to_thread(self.similarity_search, folder_path, query, limit)

    def replace_documents(self, folder_path: str, chunks: list[Any]) -> int:
        folder_key = self.folder_id(folder_path)
        table = self._open_table()

        if table is not None:
            table.delete(f"folder_id = '{folder_key}'")

        if not chunks:
            logger.warning("No chunks produced for %s; existing vectors were removed", folder_path)
            return 0

        texts = [chunk.page_content for chunk in chunks]
        vectors = self._embeddings.embed_documents(texts)
        rows = [
            {
                "id": str(uuid4()),
                "folder_id": folder_key,
                "folder_path": str(Path(folder_path).expanduser().resolve()),
                "source": str(chunk.metadata.get("source", "")),
                "filename": str(chunk.metadata.get("filename", "")),
                "relative_path": str(chunk.metadata.get("relative_path", "")),
                "chunk_index": int(chunk.metadata.get("chunk_index", index)),
                "text": chunk.page_content,
                "vector": vector,
            }
            for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
        ]

        if table is None:
            self._db.create_table(self.settings.lancedb_table, data=rows)
        else:
            table.add(rows)

        logger.info("Stored %s chunks for %s in LanceDB", len(rows), folder_path)
        return len(rows)

    def similarity_search(
        self,
        folder_path: str,
        query: str,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        table = self._open_table()
        if table is None:
            logger.warning("LanceDB table %s does not exist yet", self.settings.lancedb_table)
            return []

        folder_key = self.folder_id(folder_path)
        vector = self._embeddings.embed_query(query)
        max_results = limit or self.settings.retrieval_k

        results = (
            table.search(vector)
            .where(f"folder_id = '{folder_key}'", prefilter=True)
            .limit(max_results)
            .to_list()
        )
        return [dict(result) for result in results]
