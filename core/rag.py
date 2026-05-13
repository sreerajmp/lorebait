import logging
from collections.abc import AsyncIterator

from core.llm import build_chat_model
from core.vector_store import LanceVectorStore
from models.persona import Persona


logger = logging.getLogger(__name__)


PERSONA_PROMPTS: dict[Persona, str] = {
    Persona.TUTOR: (
        "You are Lorebait's Tutor persona. Explain concepts clearly and patiently, "
        "ground every claim in the provided context, and end with exactly one quiz "
        "question that tests the user's understanding."
    ),
    Persona.RESEARCHER: (
        "You are Lorebait's Researcher persona. Produce a concise synthesis with "
        "citations from the provided filenames. Cite sources inline using filenames "
        "in square brackets, such as [notes.md]."
    ),
    Persona.LEARNER: (
        "You are Lorebait's Learner persona. Help the user learn actively by asking "
        "probing questions. Keep answers brief, use the context, and ask the user "
        "what they think before revealing too much."
    ),
}


def format_context(matches: list[dict]) -> str:
    if not matches:
        return "No indexed context was retrieved for this question."

    blocks: list[str] = []
    for index, match in enumerate(matches, start=1):
        filename = match.get("filename") or "unknown"
        relative_path = match.get("relative_path") or filename
        text = (match.get("text") or "").strip()
        blocks.append(f"[{index}] Source: {filename} ({relative_path})\n{text}")
    return "\n\n".join(blocks)


def build_prompt(question: str, persona: Persona, context: str) -> str:
    return f"""
{PERSONA_PROMPTS[persona]}

Use only the context below. If the answer is not supported by the indexed files,
say that the indexed context does not contain enough information.

Context:
{context}

User question:
{question}
""".strip()


async def stream_persona_answer(
    question: str,
    persona: Persona,
    folder_path: str,
    top_k: int,
) -> AsyncIterator[str]:
    try:
        vector_store = LanceVectorStore()
        matches = await vector_store.asimilarity_search(
            folder_path=folder_path,
            query=question,
            limit=top_k,
        )
        prompt = build_prompt(
            question=question,
            persona=persona,
            context=format_context(matches),
        )
        llm = build_chat_model()

        async for chunk in llm.astream(prompt):
            content = getattr(chunk, "content", None)
            if content:
                yield content
    except Exception:
        logger.exception("Chat streaming failed")
        yield "\n\nLorebait could not complete this response. Check server logs for details."
