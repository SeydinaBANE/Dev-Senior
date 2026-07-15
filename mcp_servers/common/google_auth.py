"""
Authentification OAuth2 Google partagée entre mcp_servers/seo et
mcp_servers/google_workspace — unifie les deux implémentations quasi
identiques de _get_credentials() qui existaient dans chaque server.py.

Le token est rafraîchi/revalidé à CHAQUE appel (pas de cache) : c'est le
comportement historique des deux serveurs, à préserver — un process
long-vivant doit pouvoir rafraîchir un token expiré à chaque invocation.
"""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow


def get_credentials(scopes: list[str], credentials_file: str, token_file: str) -> Credentials:
    creds: Credentials | None = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_file):
                raise RuntimeError(
                    f"{credentials_file} introuvable. Télécharge-le depuis Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, scopes)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())
    return creds
