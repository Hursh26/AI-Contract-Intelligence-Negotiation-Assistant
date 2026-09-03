# Backend AI Service

FastAPI backend for the AI Contract Intelligence & Negotiation Assistant. Owned by the Backend AI team (Saurabh Jha, Viraj Mhadgut).

## Stack

Python · FastAPI · PostgreSQL · SQLAlchemy · JWT · Pydantic · OpenAPI/Swagger — see `/documents/Backend_AI_Technology_Stack (1).pdf` for the full rationale.

## Local setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env             # then fill in real values, esp. DATABASE_URL
```

## Run

```bash
uvicorn app.main:app --reload
```

- API base: http://localhost:8000
- Interactive docs (Swagger UI): http://localhost:8000/docs
- OpenAPI schema: http://localhost:8000/api/v1/openapi.json

## Test

```bash
pytest
```

## Structure

```
app/
├── main.py              # FastAPI app instance, middleware, router mount
├── core/
│   └── config.py        # Settings (env vars / .env)
├── db/
│   ├── base.py           # SQLAlchemy declarative Base
│   └── session.py        # Engine, SessionLocal, get_db dependency
├── models/               # SQLAlchemy ORM models
├── schemas/               # Pydantic request/response schemas
└── api/
    ├── deps.py            # Shared FastAPI dependencies
    └── v1/
        ├── router.py       # Aggregates endpoint routers
        └── endpoints/      # One module per resource
tests/                      # Backend unit tests (pytest)
```

## Endpoints (current)

| Method | Path | Task | Notes |
|---|---|---|---|
| GET | `/api/v1/health` | — | Liveness check (hidden from Swagger docs, still works) |
| POST | `/api/v1/contracts/upload` | Create upload API / Validate uploaded file | Accepts `multipart/form-data`, field `file`. PDF/DOCX/TXT only, ≤10MB (`MAX_UPLOAD_SIZE_MB`), rejects empty files and content that doesn't match its extension |
| GET | `/api/v1/contracts/{id}` | — | Read back a stored contract, incl. extraction results once processed |
| POST | `/api/v1/contracts/{id}/extract` | Store extracted information (raw text) | Pulls raw text straight out of the stored file ourselves (PyMuPDF for PDF, python-docx for DOCX, plain decode for TXT) and persists it. **No clause identification** — that's still NLP/ML's "Identify basic clauses" task. This exists so the pipeline works end-to-end without waiting on their pipeline; 422 if the file can't be parsed |
| PATCH | `/api/v1/contracts/{id}/extraction` | Store extracted information (clauses) | Body: `{"extracted_text": str, "clauses": ...}` — for the NLP/ML pipeline to submit identified clauses (and optionally override the raw text) once it exists; marks it `processed` |

No auth yet (JWT task not scoped). `contracts.owner_id` is nullable until that lands.

**Division of labor, to be explicit:** `/extract` does *text extraction* (backend, mechanical — just reads bytes out of a file format). `/extraction` (PATCH) is where *clause identification* — actual NLP — gets stored, and that step stays owned by the NLP/ML team even though backend built a text-only stand-in so the demo isn't blocked on their pipeline.

### Upload validation rules

- Allowed types: `.pdf`, `.docx`, `.txt` (checked by extension **and** a raw magic-byte signature — `%PDF-` for PDF, `PK\x03\x04` for DOCX — so a mislabeled/corrupted file is rejected even if the extension looks right)
- Rejects empty files
- Rejects files over `MAX_UPLOAD_SIZE_MB` (default 10MB)
- Filenames are sanitized (path components stripped) before being stored as metadata; the file on disk is always named with a fresh UUID, never the client-supplied name

Try it:
```bash
curl -X POST http://localhost:8000/api/v1/contracts/upload \
  -F "file=@/path/to/sample.pdf;type=application/pdf"
```

## Cross-platform compatibility (macOS / Linux / Windows)

The team develops on a mix of Mac and Windows machines, so this was audited and tested for platform independence rather than assumed:

**What was changed to be portable:**
- All filesystem paths go through `pathlib.Path` (`app/utils/storage.py`) — no hardcoded `/` or `\`, no `os.path` string concatenation. The storage root is resolved relative to the package location, so it's correct regardless of the OS or the directory the process is launched from.
- Uploaded files are written with `Path.write_bytes` (binary mode) — text-mode writes on Windows silently rewrite `\n` → `\r\n`, which would corrupt binary formats like PDF/DOCX.
- Files are stored on disk under a generated UUID name, never the client's original filename — sidesteps Windows-illegal filename characters (`: * ? " < > |`) and reserved names (`CON`, `PRN`, `NUL`, `COM1`, …) entirely; the original name is kept only as DB metadata.
- Filename sanitization strips **both** `/` and `\` path separators unconditionally (`app/utils/file_validation.py`), regardless of which OS the server happens to run on — a malicious filename could contain either separator no matter the host.
- No `python-magic`/libmagic dependency for file-type sniffing — that library needs a separately-installed native DLL on Windows and is a common source of "works on my machine" setup pain. Signature checks are done directly against raw bytes instead, with zero OS-specific setup.
- `psycopg[binary]` (psycopg 3) instead of `psycopg2-binary` — the latter has no prebuilt wheel yet for newer Python releases and fails to compile from source without system Postgres dev headers (`pg_config`), which is a much bigger ask on Windows than on Mac/Linux.
- SQLAlchemy's dialect-portable `Uuid` and `JSON().with_variant(JSONB, "postgresql")` column types instead of the Postgres-only `postgresql.UUID` / `postgresql.JSONB` — renders as native UUID/JSONB on Postgres in production, but the exact same model code also works against SQLite, which is what makes the automated test suite below possible without installing/running Postgres at all.
- Root `.gitattributes` normalizes line endings to LF across the repo, so a Windows checkout doesn't silently convert source files to CRLF and produce noisy whole-file diffs against Mac/Linux contributors' work.

**Proof of work:**
1. **Local run (macOS, this session):** full suite green —
   ```
   11 passed in 0.06s
   ```
   (`pytest -v` output: all upload/validation/extraction/health tests passing.)
2. **Real Postgres, not just the test double (macOS, this session):** installed PostgreSQL 16 locally, ran `python -m app.db.init_db` to create the actual `users`/`contracts` tables, then drove the full flow through `curl` against the running app — upload → reject bad extension → reject empty file → reject signature mismatch → store extraction → read back → 404 on unknown id — and confirmed the row directly via `psql` (`SELECT ... FROM contracts` showing the persisted `status`/`clauses`). This is what rules out "only works against the SQLite test stub."
3. **CI matrix (`.github/workflows/ci.yml`) — the actual Mac/Windows/Linux proof:** `backend-tests` runs the identical `pytest` suite on `ubuntu-latest`, `windows-latest`, and `macos-latest` GitHub-hosted runners on every push/PR to `develop`/`main`. This is real execution on real Windows and Linux machines, not a claim — check the **Actions** tab on the PR for this scaffold once it's pushed; each OS shows its own pass/fail.

**What's *not* independently verified:** nobody on the team has yet run this by hand on an actual Windows machine outside of CI — worth a quick manual smoke test from Saurabh (or anyone on Windows) once this is pushed, on top of the CI matrix.
