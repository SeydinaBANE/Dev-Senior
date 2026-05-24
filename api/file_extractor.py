"""Text extraction from uploaded files (plain text/code, PDF, DOCX)."""

from __future__ import annotations

import io
from pathlib import Path

MAX_CHARS = 20_000

_TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".mjs",
    ".json",
    ".csv",
    ".yaml",
    ".yml",
    ".toml",
    ".html",
    ".css",
    ".sh",
    ".bash",
    ".zsh",
    ".sql",
    ".xml",
    ".rst",
    ".ini",
    ".cfg",
}


def extract_text(filename: str, content: bytes) -> str:
    """Return plain text from file bytes. Raises ValueError for unsupported formats."""
    ext = Path(filename).suffix.lower()

    if ext in _TEXT_EXTENSIONS or ext == "":
        text = _decode(content)
    elif ext == ".pdf":
        text = _pdf(content)
    elif ext == ".docx":
        text = _docx(content)
    else:
        raise ValueError(
            f"Format « {ext} » non supporté. "
            "Formats acceptés : texte/code (.py, .js, .ts, .md, .csv, .json…), .pdf, .docx"
        )

    text = text.strip()
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + f"\n\n[… document tronqué à {MAX_CHARS:,} caractères]"
    return text


def _decode(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        return content.decode("latin-1", errors="replace")


def _pdf(content: bytes) -> str:
    import pypdf

    reader = pypdf.PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(p for p in pages if p.strip())


def _docx(content: bytes) -> str:
    import docx

    doc = docx.Document(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
