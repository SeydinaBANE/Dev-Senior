"""
Indexeur de codebase pour l'agent Dev Senior.

Usage :
    python -m memory.dev_senior.indexer --path /chemin/vers/repo
"""
import hashlib
from pathlib import Path
from typing import Iterator

import typer
from rich.console import Console
from rich.progress import track
from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    FilterSelector,
)

from memory.store import get_client, ensure_collection
from memory.embeddings import embed_batch, chunk_text

app = typer.Typer()
console = Console()

COLLECTION_NAME = "codebase"

SUPPORTED_EXTENSIONS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java",
    ".kt", ".swift", ".c", ".cpp", ".h", ".cs", ".rb", ".php",
    ".md", ".yaml", ".yml", ".toml", ".json", ".sql",
}

IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__",
    ".mypy_cache", ".ruff_cache", ".pytest_cache", "dist", "build",
    "memory/vector_store",
}


def iter_files(root: Path) -> Iterator[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in SUPPORTED_EXTENSIONS:
            if not any(ignored in path.parts for ignored in IGNORED_DIRS):
                yield path


def file_hash(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()


def _stable_id(rel_path: str, chunk_index: int) -> int:
    """Génère un ID entier stable à partir du chemin et du chunk."""
    key = f"{rel_path}::chunk{chunk_index}"
    return int(hashlib.md5(key.encode()).hexdigest(), 16) % (2**63)


def _source_filter(rel_path: str) -> Filter:
    return Filter(must=[FieldCondition(key="source", match=MatchValue(value=rel_path))])


@app.command()
def index(
    path: str = typer.Argument(".", help="Chemin du dépôt à indexer"),
    force: bool = typer.Option(False, "--force", help="Réindexer même les fichiers inchangés"),
) -> None:
    """Indexe une codebase dans Qdrant pour la mémoire de Dev Senior."""
    root = Path(path).resolve()
    if not root.exists():
        console.print(f"[red]Chemin introuvable : {root}[/]")
        raise typer.Exit(1)

    ensure_collection(COLLECTION_NAME)
    client = get_client()
    files = list(iter_files(root))
    console.print(f"[green]{len(files)} fichiers trouvés dans {root}[/]")

    indexed = 0
    skipped = 0

    for file_path in track(files, description="Indexation..."):
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if not content.strip():
                continue

            rel_path = str(file_path.relative_to(root))
            content_hash = file_hash(content)

            if not force:
                existing, _ = client.scroll(
                    collection_name=COLLECTION_NAME,
                    scroll_filter=_source_filter(rel_path),
                    limit=1,
                    with_payload=True,
                )
                if existing and existing[0].payload and existing[0].payload.get("hash") == content_hash:
                    skipped += 1
                    continue
                # Supprime l'ancienne version avant réindexation
                if existing:
                    client.delete(
                        collection_name=COLLECTION_NAME,
                        points_selector=FilterSelector(filter=_source_filter(rel_path)),
                    )

            chunks = chunk_text(content)
            embeddings = embed_batch(chunks)
            points = [
                PointStruct(
                    id=_stable_id(rel_path, i),
                    vector=emb,
                    payload={
                        "source": rel_path,
                        "hash": content_hash,
                        "chunk": i,
                        "ext": file_path.suffix,
                        "text": chunk,
                    },
                )
                for i, (chunk, emb) in enumerate(zip(chunks, embeddings))
            ]
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            indexed += 1

        except Exception as e:
            console.print(f"[yellow]Erreur sur {file_path}: {e}[/]")

    console.print(f"[bold green]✓ {indexed} fichiers indexés, {skipped} ignorés (inchangés)[/]")


if __name__ == "__main__":
    app()
