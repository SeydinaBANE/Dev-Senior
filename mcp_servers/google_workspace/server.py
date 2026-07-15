"""
MCP Server Google Workspace — outils pour l'agent Business Manager.

Outils exposés :
- list_drive_files    : rechercher des fichiers Drive
- read_drive_file     : lire un document Google Docs/texte
- create_drive_doc    : créer un Google Doc
- list_emails         : rechercher des emails Gmail
- send_email          : envoyer un email
- list_events         : événements Calendar à venir
- create_event        : créer un événement Calendar

Auth : OAuth2 via credentials.json (à générer depuis Google Cloud Console).
Le token est mis en cache dans token.json (gitignore).
"""

import os

from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP

from mcp_servers.google_workspace.adapters.workspace_client import WorkspaceClient

mcp = FastMCP("google-workspace")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]

CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")

_client_instance: WorkspaceClient | None = None


def _client() -> WorkspaceClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = WorkspaceClient(SCOPES, CREDENTIALS_FILE, TOKEN_FILE)
    return _client_instance


# ── Google Drive ──────────────────────────────────────────────────────────────


@mcp.tool()
def list_drive_files(query: str = "", max_results: int = 20) -> str:
    """Recherche des fichiers dans Google Drive.

    Args:
        query:       Termes de recherche (ex: 'rapport mensuel'). Vide = fichiers récents.
        max_results: Nombre max de résultats (défaut: 20).
    """
    try:
        files = _client().list_drive_files(query, max_results)
        if not files:
            return "Aucun fichier trouvé."
        lines = [
            f"[{f['id']}] {f['name']} ({f['mimeType']}) — {f['modifiedTime'][:10]}" for f in files
        ]
        return "\n".join(lines)
    except HttpError as e:
        return f"Erreur Drive : {e}"


@mcp.tool()
def read_drive_file(file_id: str) -> str:
    """Lit le contenu texte d'un fichier Google Drive.

    Args:
        file_id: ID du fichier (visible avec list_drive_files).
    """
    try:
        return _client().read_drive_file(file_id)
    except HttpError as e:
        return f"Erreur Drive : {e}"


@mcp.tool()
def create_drive_doc(title: str, content: str) -> str:
    """Crée un Google Doc avec le contenu fourni.

    Args:
        title:   Titre du document.
        content: Contenu texte du document.
    """
    try:
        doc_id = _client().create_drive_doc(title, content)
        return f"Document créé : https://docs.google.com/document/d/{doc_id}"
    except HttpError as e:
        return f"Erreur Docs : {e}"


# ── Gmail ─────────────────────────────────────────────────────────────────────


@mcp.tool()
def list_emails(query: str = "is:unread", max_results: int = 10) -> str:
    """Recherche des emails dans Gmail.

    Args:
        query:       Requête Gmail (ex: 'from:john@example.com', 'is:unread').
        max_results: Nombre max d'emails retournés (défaut: 10).
    """
    try:
        details = _client().list_emails(query, max_results)
        if not details:
            return "Aucun email trouvé."
        lines = []
        for detail in details:
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            lines.append(
                f"[{detail['id']}] {headers.get('Date', '')[:16]} "
                f"De: {headers.get('From', '')} — {headers.get('Subject', '')}"
            )
        return "\n".join(lines)
    except HttpError as e:
        return f"Erreur Gmail : {e}"


@mcp.tool()
def send_email(to: str, subject: str, body: str) -> str:
    """Envoie un email via Gmail.

    Args:
        to:      Adresse email du destinataire.
        subject: Objet de l'email.
        body:    Corps du message (texte brut).
    """
    try:
        _client().send_email(to, subject, body)
        return f"Email envoyé à {to}."
    except HttpError as e:
        return f"Erreur Gmail : {e}"


# ── Google Calendar ───────────────────────────────────────────────────────────


@mcp.tool()
def list_events(days_ahead: int = 7, max_results: int = 20) -> str:
    """Retourne les événements Google Calendar à venir.

    Args:
        days_ahead:  Nombre de jours à afficher depuis maintenant (défaut: 7).
        max_results: Nombre max d'événements (défaut: 20).
    """
    try:
        events = _client().list_events(days_ahead, max_results)
        if not events:
            return f"Aucun événement dans les {days_ahead} prochains jours."
        lines = []
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date", ""))[:16]
            lines.append(f"{start} — {e['summary']}")
        return "\n".join(lines)
    except HttpError as e:
        return f"Erreur Calendar : {e}"


@mcp.tool()
def create_event(
    title: str,
    start: str,
    end: str,
    description: str = "",
    attendees: str = "",
) -> str:
    """Crée un événement dans Google Calendar.

    Args:
        title:       Titre de l'événement.
        start:       Date/heure de début ISO 8601 (ex: '2026-05-20T14:00:00').
        end:         Date/heure de fin ISO 8601.
        description: Description optionnelle.
        attendees:   Emails des participants, séparés par des virgules.
    """
    try:
        created = _client().create_event(title, start, end, description, attendees)
        return f"Événement créé : {created['htmlLink']}"
    except HttpError as e:
        return f"Erreur Calendar : {e}"


if __name__ == "__main__":
    mcp.run()
