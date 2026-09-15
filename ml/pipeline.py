"""End-to-end contract analysis orchestration."""

from typing import Any

from .clause_ner import analyze_clause
from .config import Settings
from .preprocessing import normalize_text, tokenize_and_lemmatize, split_into_clauses
from .rag import SLMRAG
from .semantic_search import SemanticRetriever


class ContractPipeline:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self.retriever = SemanticRetriever(self.settings.embedding_model)
        self.rag = SLMRAG(self.retriever, self.settings.slm_model, self.settings.max_context_chars)

    def analyze(self, text: str) -> dict[str, Any]:
        normalized = normalize_text(text)
        clauses = split_into_clauses(normalized)
        analyzed = [analyze_clause(c, self.settings.spacy_model) for c in clauses]
        self.retriever.build(analyzed)
        return {
            "extracted_text": normalized,
            "clauses": analyzed,
            "clause_count": len(analyzed),
        }

    def ask(self, question: str) -> dict[str, Any]:
        return self.rag.answer(question, top_k=self.settings.top_k)

    def preprocess(self, text: str) -> dict[str, Any]:
        return {"normalized_text": normalize_text(text), "tokens": tokenize_and_lemmatize(text, self.settings.spacy_model)}
