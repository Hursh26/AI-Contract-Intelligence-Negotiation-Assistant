from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    spacy_model: str = os.getenv("SPACY_MODEL", "en_core_web_sm")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    slm_model: str = os.getenv("SLM_MODEL", "google/flan-t5-small")
    top_k: int = int(os.getenv("RAG_TOP_K", "3"))
    max_context_chars: int = int(os.getenv("RAG_MAX_CONTEXT_CHARS", "6000"))
