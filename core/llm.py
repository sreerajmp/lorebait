import logging

from core.config import Settings, get_settings


logger = logging.getLogger(__name__)


def build_embeddings(settings: Settings | None = None):
    settings = settings or get_settings()
    logger.info(
        "Using Ollama embeddings model=%s base_url=%s",
        settings.ollama_embedding_model,
        settings.ollama_base_url,
    )

    try:
        from langchain_ollama import OllamaEmbeddings
    except ImportError:
        try:
            from langchain_community.embeddings import OllamaEmbeddings
        except ImportError as exc:
            raise RuntimeError("Install langchain-ollama to use Ollama embeddings") from exc

    return OllamaEmbeddings(
        model=settings.ollama_embedding_model,
        base_url=settings.ollama_base_url,
    )


def build_chat_model(settings: Settings | None = None):
    settings = settings or get_settings()
    logger.info(
        "Using Ollama chat model=%s base_url=%s",
        settings.ollama_model,
        settings.ollama_base_url,
    )

    try:
        from langchain_ollama import ChatOllama
    except ImportError:
        try:
            from langchain_community.chat_models import ChatOllama
        except ImportError as exc:
            raise RuntimeError("Install langchain-ollama to use Ollama chat models") from exc

    return ChatOllama(
        model=settings.ollama_model,
        base_url=settings.ollama_base_url,
        temperature=0.2,
    )
