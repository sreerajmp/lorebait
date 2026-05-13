import logging

from core.config import Settings, get_settings


logger = logging.getLogger(__name__)


def build_embeddings(settings: Settings | None = None):
    settings = settings or get_settings()
    provider = settings.resolved_embedding_provider

    if provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai")
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError as exc:
            raise RuntimeError("Install langchain-openai to use OpenAI embeddings") from exc

        return OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            api_key=settings.openai_api_key,
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

    if settings.llm_provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise RuntimeError("Install langchain-openai to use OpenAI chat models") from exc

        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.2,
            streaming=True,
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
