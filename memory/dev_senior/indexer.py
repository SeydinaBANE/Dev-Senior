"""
Indexeur de codebase pour l'agent Dev Senior.

Usage :
    python -m memory.dev_senior.indexer --path /chemin/vers/repo

Indexe tous les fichiers de code source dans ChromaDB pour que
l'agent puisse retrouver du contexte pertinent à chaque requête.
"""
import os
import hashlib
from pathlib import Path
from typing import Iterator

import typer
from rich.console import Console
from rich.progress import track

from memory.store import get_or_create_collection
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


@app.command()
def index(
    path: str = typer.Argument(".", help="Chemin du dépôt à indexer"),
    force: bool = typer.Option(False, "--force", help="Réindexer même les fichiers inchangés"),
) -> None:
    """Indexe une codebase dans ChromaDB pour la mémoire de Dev Senior."""
    root = Path(path).resolve()
    if not root.exists():
        console.print(f"[red]Chemin introuvable : {root}[/]")
        raise typer.Exit(1)

    collection = get_or_create_collection(COLLECTION_NAME)
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

            # Vérifie si déjà indexé et inchangé
            if not force:
                existing = collection.get(where={"source": rel_path})
                if existing["ids"] and existing["metadatas"]:
                    stored_hash = existing["metadatas"][0].get("hash", "")
                    if stored_hash == content_hash:
                        skipped += 1
                        continue
                # Supprime l'ancienne version avant réindexation
                if existing["ids"]:
                    collection.delete(ids=existing["ids"])

            chunks = chunk_text(content)
            embeddings = embed_batch(chunks)
            ids = [f"{rel_path}::chunk{i}" for i in range(len(chunks))]
            metadatas = [
                {"source": rel_path, "hash": content_hash, "chunk": i, "ext": file_path.suffix}
                for i in range(len(chunks))
            ]
            collection.add(ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas)
            indexed += 1

        except Exception as e:
            console.print(f"[yellow]Erreur sur {file_path}: {e}[/]")

    console.print(f"[bold green]✓ {indexed} fichiers indexés, {skipped} ignorés (inchangés)[/]")


if __name__ == "__main__":
    app()
