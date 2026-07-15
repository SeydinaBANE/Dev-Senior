"""
Adapter Google Workspace — wrappe googleapiclient (Drive, Docs, Gmail, Calendar).
mcp_servers/google_workspace/server.py garde le formatage de réponse pour le LLM.

Les credentials sont récupérées à CHAQUE appel (pas de cache sur l'instance) —
comportement historique à préserver, un token expiré doit se rafraîchir à
chaque invocation d'un outil.
"""

import base64
from datetime import UTC, datetime, timedelta
from email.mime.text import MIMEText
from typing import Any

from googleapiclient.discovery import build

from mcp_servers.common.google_auth import get_credentials


class WorkspaceClient:
    def __init__(self, scopes: list[str], credentials_file: str, token_file: str) -> None:
        self._scopes = scopes
        self._credentials_file = credentials_file
        self._token_file = token_file

    def _service(self, name: str, version: str) -> Any:
        creds = get_credentials(self._scopes, self._credentials_file, self._token_file)
        return build(name, version, credentials=creds)

    # ── Drive ────────────────────────────────────────────────────────────────

    def list_drive_files(self, query: str, max_results: int) -> list[dict]:
        service = self._service("drive", "v3")
        q = f"name contains '{query}' and trashed=false" if query else "trashed=false"
        results = (
            service.files()
            .list(
                q=q,
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime)",
                orderBy="modifiedTime desc",
            )
            .execute()
        )
        return results.get("files", [])

    def read_drive_file(self, file_id: str) -> str:
        service = self._service("drive", "v3")
        meta = service.files().get(fileId=file_id, fields="mimeType,name").execute()
        mime = meta["mimeType"]

        if "google-apps.document" in mime:
            content = service.files().export(fileId=file_id, mimeType="text/plain").execute()
            return content.decode("utf-8")
        else:
            content = service.files().get_media(fileId=file_id).execute()
            return content.decode("utf-8", errors="replace")

    def create_drive_doc(self, title: str, content: str) -> str:
        docs_service = self._service("docs", "v1")
        doc = docs_service.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
        docs_service.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]},
        ).execute()
        return doc_id

    # ── Gmail ────────────────────────────────────────────────────────────────

    def list_emails(self, query: str, max_results: int) -> list[dict]:
        service = self._service("gmail", "v1")
        results = (
            service.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
        )
        messages = results.get("messages", [])
        details = []
        for msg in messages:
            detail = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )
            # L'id affiché vient de l'appel list() (msg["id"]), pas du détail —
            # comportement historique, le détail metadata ne garantit pas "id".
            detail["id"] = msg["id"]
            details.append(detail)
        return details

    def send_email(self, to: str, subject: str, body: str) -> None:
        service = self._service("gmail", "v1")
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()

    # ── Calendar ─────────────────────────────────────────────────────────────

    def list_events(self, days_ahead: int, max_results: int) -> list[dict]:
        service = self._service("calendar", "v3")
        now = datetime.now(UTC)
        end = now + timedelta(days=days_ahead)
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        return events_result.get("items", [])

    def create_event(
        self, title: str, start: str, end: str, description: str, attendees: str
    ) -> dict:
        service = self._service("calendar", "v3")
        event: dict = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start, "timeZone": "Europe/Paris"},
            "end": {"dateTime": end, "timeZone": "Europe/Paris"},
        }
        if attendees:
            event["attendees"] = [{"email": e.strip()} for e in attendees.split(",")]
        return service.events().insert(calendarId="primary", body=event).execute()
