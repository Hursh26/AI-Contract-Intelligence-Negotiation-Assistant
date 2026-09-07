"""Upload validation: filename sanitization + extension/signature/size checks.

Deliberately has zero OS-level dependencies. In particular this does NOT use
python-magic/libmagic for content-sniffing — that library needs a separate
native shared library that is genuinely painful to install on Windows (it
needs a bundled DLL via python-magic-bin, which is unmaintained). Instead we
check a handful of raw magic-byte signatures ourselves, which works
identically on macOS, Linux, and Windows with no setup.
"""

from dataclasses import dataclass

from app.core.config import settings


class FileValidationError(ValueError):
    """Raised when an uploaded file fails validation; the endpoint turns this into an HTTP 400."""


@dataclass(frozen=True)
class _AllowedFileType:
    extension: str
    magic_bytes: tuple[bytes, ...] | None  # None = no signature check (e.g. plain text)


ALLOWED_FILE_TYPES: tuple[_AllowedFileType, ...] = (
    _AllowedFileType(".pdf", (b"%PDF-",)),
    # .docx is a zip container (OOXML) — PK\x03\x04 is the standard zip signature.
    _AllowedFileType(".docx", (b"PK\x03\x04",)),
    _AllowedFileType(".txt", None),
)

_EXTENSION_MAP = {t.extension: t for t in ALLOWED_FILE_TYPES}


def sanitize_filename(filename: str) -> str:
    """Strip any directory components and cap length.

    Strips BOTH '/' and '\\' regardless of the host OS: a malicious filename
    could contain either separator no matter which OS the server itself runs
    on, so checking only `os.sep` would miss half the cases. This is what
    guards against path traversal (e.g. "../../etc/passwd") — the sanitized
    result is only ever used for display/metadata; the file on disk is
    always named with a fresh UUID (see storage.py), so this filename never
    touches a real filesystem path anyway.
    """
    name = filename.replace("\\", "/").rsplit("/", 1)[-1].strip()
    return (name or "upload")[:255]


def validate_upload(*, filename: str, content: bytes) -> None:
    """Raise FileValidationError on the first failing check.

    Order: empty -> size -> extension -> signature. Content-Type headers are
    deliberately not checked — they're client-supplied and unreliable
    (browsers/HTTP clients are inconsistent about what they send); the
    magic-byte signature check below is the actual security-relevant check
    that catches a mislabeled/corrupted file.
    """
    if len(content) == 0:
        raise FileValidationError("Uploaded file is empty.")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise FileValidationError(f"File exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit.")

    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    file_type = _EXTENSION_MAP.get(suffix)
    if file_type is None:
        allowed = ", ".join(sorted(_EXTENSION_MAP))
        raise FileValidationError(f"Unsupported file type '{suffix or '(none)'}'. Allowed: {allowed}")

    if file_type.magic_bytes is not None and not content.startswith(file_type.magic_bytes):
        raise FileValidationError(
            f"File content does not match its extension ({suffix}) — possibly corrupted or mislabeled."
        )
