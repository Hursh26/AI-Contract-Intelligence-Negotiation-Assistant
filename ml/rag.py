"""Retrieval-augmented answering using a small Hugging Face text-to-text model."""

from typing import Any

from .semantic_search import SearchResult, SemanticRetriever


class SLMRAG:
    def __init__(self, retriever: SemanticRetriever, model_name: str = "google/flan-t5-small", max_context_chars: int = 6000) -> None:
        self.retriever = retriever
        self.model_name = model_name
        self.max_context_chars = max_context_chars
        self._generator = None

    def _get_generator(self):
        if self._generator is None:
            from transformers import pipeline
            self._generator = pipeline("text2text-generation", model=self.model_name, tokenizer=self.model_name)
        return self._generator

    def answer(self, question: str, top_k: int = 3) -> dict[str, Any]:
        results = self.retriever.search(question, top_k=top_k)
        context_parts: list[str] = []
        used: list[SearchResult] = []
        total = 0
        for result in results:
            part = f"[{result.id}] {result.text}"
            if total + len(part) > self.max_context_chars:
                break
            context_parts.append(part)
            used.append(result)
            total += len(part)

        context = "\n".join(context_parts)
        prompt = (
            "Answer the contract question using ONLY the provided context. "
            "If the answer is not stated in the context, say: 'The provided contract context does not contain this information.' "
            "Do not invent names, dates, amounts, rights, or obligations.\n\n"
            f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        )
        output = self._get_generator()(prompt, max_new_tokens=128, do_sample=False)[0]["generated_text"].strip()
        return {
            "answer": output,
            "sources": [{"id": r.id, "text": r.text, "score": round(r.score, 4)} for r in used],
        }
