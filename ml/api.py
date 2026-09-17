"""Optional standalone FastAPI service for the ML/NLP subsystem."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .pipeline import ContractPipeline

app = FastAPI(title="Contract NLP/ML Service", version="0.1.0")
pipeline = ContractPipeline()


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest):
    try:
        return pipeline.analyze(request.text)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/ask")
def ask(request: QuestionRequest):
    try:
        return pipeline.ask(request.question)
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
