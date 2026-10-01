# Contract NLP/ML Pipeline

Lightweight student-project pipeline for the `/ml` subsystem:

1. Text normalization + NLTK sentence splitting
2. spaCy tokenization/lemmatization + NER
3. Rule-based clause identification and transparent risk signals
4. Sentence-Transformers embeddings
5. FAISS cosine semantic search
6. RAG with a small Hugging Face text-to-text model (`google/flan-t5-small`)
7. FastAPI service for integration

## Setup

From repository root:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r ml/requirements.txt
python -m spacy download en_core_web_sm
```

The SLM and embedding model are downloaded by Hugging Face on first use. No API key or Ollama is required.

## Run

```bash
uvicorn ml.api:app --reload --port 8001
```

Endpoints:

- `GET /health`
- `POST /analyze` → extracted text + clause analysis
- `POST /ask` → semantic retrieval + SLM answer with source clauses

## Backend integration contract

`POST /analyze` returns a stable, simple shape:

```json
{
  "extracted_text": "...",
  "clause_count": 2,
  "clauses": [
    {
      "id": "1",
      "text": "...",
      "type": "termination",
      "entities": [],
      "risk": {
        "level": "medium",
        "score": 0.6,
        "reasons": ["termination"]
      }
    }
  ]
}
```

This `clauses` array can be sent directly to the existing backend `PATCH /api/v1/contracts/{id}/extraction` endpoint, which currently accepts `clauses` as JSON.
