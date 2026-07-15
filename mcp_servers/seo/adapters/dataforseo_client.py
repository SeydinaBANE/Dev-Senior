"""
Adapter DataForSEO — appels HTTP bruts (Basic auth) vers l'API DataForSEO.
mcp_servers/seo/server.py garde les guard-clauses et le formatage de réponse.
"""

import base64

import httpx


class DataForSeoClient:
    def __init__(self, login: str, password: str) -> None:
        self._login = login
        self._password = password

    def _headers(self) -> dict:
        encoded = base64.b64encode(f"{self._login}:{self._password}".encode()).decode()
        return {"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}

    def keyword_ideas(self, keyword: str, language: str, location: int) -> dict:
        payload = [
            {"keyword": keyword, "language_code": language, "location_code": location, "limit": 20}
        ]
        r = httpx.post(
            "https://api.dataforseo.com/v3/dataforseo_labs/google/keyword_ideas/live",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        r.raise_for_status()
        return r.json()

    def serp_analysis(self, keyword: str, language: str, location: int) -> dict:
        payload = [{"keyword": keyword, "language_code": language, "location_code": location}]
        r = httpx.post(
            "https://api.dataforseo.com/v3/serp/google/organic/live/regular",
            json=payload,
            headers=self._headers(),
            timeout=30,
        )
        r.raise_for_status()
        return r.json()
