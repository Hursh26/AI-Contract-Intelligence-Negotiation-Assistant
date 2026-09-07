"""Local filesystem storage for uploaded contract files.

Cross-platform notes (macOS / Linux / Windows all need to behave the same
here):
  - All paths go through pathlib.Path, never a hand-built string with '/'
    or '\\' — Path handles the OS-native separator automatically.
  - Stored filenames are UUID-based, never the client-supplied name, so we
    never have to worry about characters that are illegal in Windows
    filenames (: * ? " < > |) or Windows-reserved names (CON, PRN, NUL,
    COM1, LPT1, ...) — those are all legal in the *original* filename we
    keep as metadata, but never touch a real path.
  - Files are written with `write_bytes` (binary mode) — opening in text
    mode with '\n' in the content would get silently rewritten to '\r\n'
    on Windows, corrupting binary formats like PDF/DOCX.
"""

import uuid
from pathlib import Path

from app.core.config import settings

# Resolved relative to the backend/ package root, so this works no matter
# what working directory the process is launched from, on any OS.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
STORAGE_ROOT = (_BACKEND_ROOT / settings.STORAGE_DIR).resolve()


def save_upload(*, content: bytes, sanitized_filename: str) -> Path:
    """Write `content` to disk under a fresh UUID-based name; return the stored path."""
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    suffix = Path(sanitized_filename).suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    dest = STORAGE_ROOT / stored_name
    dest.write_bytes(content)
    return dest
