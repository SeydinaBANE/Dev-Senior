"""
Adapter Google Search Console — wrappe googleapiclient. mcp_servers/seo/server.py
garde SITE_URL/guard-clauses et le formatage de réponse pour le LLM.

Les credentials sont récupérées à CHAQUE appel (pas de cache sur l'instance) —
comportement historique à préserver, un token expiré doit se rafraîchir à
chaque invocation d'un outil.
"""

from typing import Any

from googleapiclient.discovery import build

from mcp_servers.common.google_auth import get_credentials


class SearchConsoleClient:
    def __init__(self, scopes: list[str], credentials_file: str, token_file: str) -> None:
        self._scopes = scopes
        self._credentials_file = credentials_file
        self._token_file = token_file

    def _service(self) -> Any:
        creds = get_credentials(self._scopes, self._credentials_file, self._token_file)
        return build("searchconsole", "v1", credentials=creds)

    def top_queries(
        self, site_url: str, start_date: str, end_date: str, limit: int, country: str
    ) -> list[dict]:
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query"],
            "dimensionFilterGroups": [
                {"filters": [{"dimension": "country", "expression": country}]}
            ],
            "rowLimit": limit,
        }
        response = self._service().searchanalytics().query(siteUrl=site_url, body=body).execute()
        return response.get("rows", [])

    def page_performance(
        self, site_url: str, url: str, start_date: str, end_date: str
    ) -> list[dict]:
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query"],
            "dimensionFilterGroups": [{"filters": [{"dimension": "page", "expression": url}]}],
            "rowLimit": 10,
        }
        response = self._service().searchanalytics().query(siteUrl=site_url, body=body).execute()
        return response.get("rows", [])
