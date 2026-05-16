import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from core.config import get_settings
from core.database import init_db


settings = get_settings()


def configure_logging() -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings.resolved_data_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    logging.getLogger(__name__).info(
        "Lorebait backend started with Ollama base_url=%s chat_model=%s embedding_model=%s",
        settings.ollama_base_url,
        settings.ollama_model,
        settings.ollama_embedding_model,
    )
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Local RAG backend for indexing folders and chatting with persona-guided context.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
