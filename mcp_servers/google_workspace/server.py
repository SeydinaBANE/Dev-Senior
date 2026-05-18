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
import base64
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("google-workspace")

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]

CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")


def _get_credentials() -> Credentials:
    creds: Credentials | None = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                raise RuntimeError(
                    f"{CREDENTIALS_FILE} introuvable. "
                    "Télécharge-le depuis Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


# ── Google Drive ──────────────────────────────────────────────────────────────

@mcp.tool()
def list_drive_files(query: str = "", max_results: int = 20) -> str:
    """Recherche des fichiers dans Google Drive.

    Args:
        query:       Termes de recherche (ex: 'rapport mensuel'). Vide = fichiers récents.
        max_results: Nombre max de résultats (défaut: 20).
    """
    try:
        service = build("drive", "v3", credentials=_get_credentials())
        q = f"name contains '{query}' and trashed=false" if query else "trashed=false"
        results = service.files().list(
            q=q,
            pageSize=max_results,
            fields="files(id, name, mimeType, modifiedTime)",
            orderBy="modifiedTime desc",
        ).execute()
        files = results.get("files", [])
        if not files:
            return "Aucun fichier trouvé."
        lines = [f"[{f['id']}] {f['name']} ({f['mimeType']}) — {f['modifiedTime'][:10]}" for f in files]
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
        service = build("drive", "v3", credentials=_get_credentials())
        meta = service.files().get(fileId=file_id, fields="mimeType,name").execute()
        mime = meta["mimeType"]

        if "google-apps.document" in mime:
            content = service.files().export(fileId=file_id, mimeType="text/plain").execute()
            return content.decode("utf-8")
        else:
            content = service.files().get_media(fileId=file_id).execute()
            return content.decode("utf-8", errors="replace")
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
        docs_service = build("docs", "v1", credentials=_get_credentials())
        doc = docs_service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]},
        ).execute()
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
        service = build("gmail", "v1", credentials=_get_credentials())
        results = service.users().messages().list(
            userId="me", q=query, maxResults=max_results
        ).execute()
        messages = results.get("messages", [])
        if not messages:
            return "Aucun email trouvé."

        lines = []
        for msg in messages:
            detail = service.users().messages().get(
                userId="me", id=msg["id"], format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            lines.append(
                f"[{msg['id']}] {headers.get('Date', '')[:16]} "
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
        service = build("gmail", "v1", credentials=_get_credentials())
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
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
        service = build("calendar", "v3", credentials=_get_credentials())
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])
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
        service = build("calendar", "v3", credentials=_get_credentials())
        event: dict = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start, "timeZone": "Europe/Paris"},
            "end": {"dateTime": end, "timeZone": "Europe/Paris"},
        }
        if attendees:
            event["attendees"] = [{"email": e.strip()} for e in attendees.split(",")]
        created = service.events().insert(calendarId="primary", body=event).execute()
        return f"Événement créé : {created['htmlLink']}"
    except HttpError as e:
        return f"Erreur Calendar : {e}"


if __name__ == "__main__":
    mcp.run()
