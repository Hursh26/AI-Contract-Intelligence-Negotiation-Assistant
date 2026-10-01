"""Contract text normalization, sentence splitting and tokenization."""

from functools import lru_cache
import re
import unicodedata

import nltk
from nltk.tokenize import PunktSentenceTokenizer
import spacy


@lru_cache(maxsize=2)
def load_spacy(model_name: str = "en_core_web_sm"):
    """Load the shared spaCy pipeline once per model name."""
    try:
        return spacy.load(model_name)
    except OSError as exc:
        raise RuntimeError(
            f"spaCy model '{model_name}' is not installed. "
            f"Run: python -m spacy download {model_name}"
        ) from exc


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace without destroying legal punctuation."""
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    """Split text with NLTK's Punkt tokenizer without requiring a download."""
    return [s.strip() for s in PunktSentenceTokenizer().tokenize(normalize_text(text)) if s.strip()]


def tokenize_and_lemmatize(text: str, model_name: str = "en_core_web_sm", remove_stopwords: bool = True) -> list[str]:
    """Tokenize and lemmatize with spaCy; NLTK remains the sentence-tokenization layer."""
    doc = load_spacy(model_name)(normalize_text(text))
    tokens: list[str] = []
    for token in doc:
        if token.is_space or token.is_punct:
            continue
        lemma = (token.lemma_ or token.text).lower().strip()
        if not lemma:
            continue
        if remove_stopwords and (token.is_stop or lemma in nltk_stopwords()):
            continue
        tokens.append(lemma)
    return tokens


@lru_cache(maxsize=1)
def nltk_stopwords() -> frozenset[str]:
    """Use NLTK stopwords when installed; fall back to spaCy's built-in list."""
    try:
        from nltk.corpus import stopwords

        return frozenset(stopwords.words("english"))
    except LookupError:
        return frozenset(spacy.lang.en.stop_words.STOP_WORDS)


def _looks_like_clause_header(line: str) -> bool:
    return bool(
        re.match(
            r"^\s*(?:(?:article|section|clause)\s+\d+(?:\.\d+)*|\d+(?:\.\d+)*[.)]?)[\s.)\-:]*",
            line,
            flags=re.IGNORECASE,
        )
    )


def split_into_clauses(text: str, min_length: int = 30) -> list[dict[str, object]]:
    """Extract clause-like blocks while preserving headings and clause IDs when present.

    Strategy: use explicit numbered/article/section headings when available; otherwise
    use paragraphs; if the document has no paragraph structure, fall back to sentences.
    """
    text = normalize_text(text)
    lines = text.split("\n")
    clauses: list[dict[str, object]] = []
    current: list[str] = []
    current_id: str | None = None

    def flush() -> None:
        nonlocal current, current_id
        body = " ".join(part.strip() for part in current if part.strip()).strip()
        if len(body) >= min_length:
            clauses.append({"id": current_id or f"clause_{len(clauses) + 1}", "text": body})
        current = []
        current_id = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if _looks_like_clause_header(stripped) and current:
            flush()
        if _looks_like_clause_header(stripped):
            match = re.match(
                r"^\s*((?:(?:article|section|clause)\s+\d+(?:\.\d+)*)|(?:\d+(?:\.\d+)*))",
                stripped,
                flags=re.IGNORECASE,
            )
            current_id = match.group(1) if match else None
        current.append(stripped)
    flush()

    if clauses:
        return clauses

    paragraphs = [p.strip().replace("\n", " ") for p in re.split(r"\n\s*\n", text) if p.strip()]
    paragraphs = [p for p in paragraphs if len(p) >= min_length]
    if paragraphs:
        return [{"id": f"clause_{i}", "text": p} for i, p in enumerate(paragraphs, 1)]

    sentences = [s for s in split_sentences(text) if len(s) >= min_length]
    return [{"id": f"clause_{i}", "text": s} for i, s in enumerate(sentences, 1)]
