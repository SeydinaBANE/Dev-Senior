"""
MCP Server SEO — outils pour l'agent Business Manager.

Sources :
- Google Search Console (performances, pages, requêtes)
- DataForSEO API (analyse de mots-clés, SERP, backlinks)

Configurer dans .env :
- SEARCH_CONSOLE_SITE_URL
- GOOGLE_CREDENTIALS_FILE  (même credentials que Google Workspace)
- DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD  (optionnel)

Outils exposés :
- top_queries       : requêtes de recherche les plus performantes
- page_performance  : performances d'une URL dans Search Console
- keyword_ideas     : idées de mots-clés (DataForSEO)
- serp_analysis     : analyse des résultats pour un mot-clé
"""

import base64
import os

import httpx
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("seo")

SITE_URL = os.getenv("SEARCH_CONSOLE_SITE_URL", "")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN", "")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD", "")

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]


def _get_credentials() -> Credentials:
    creds: Credentials | None = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def _dataforseo_headers() -> dict:
    encoded = base64.b64encode(f"{DATAFORSEO_LOGIN}:{DATAFORSEO_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {encoded}", "Content-Type": "application/json"}


# ── Google Search Console ─────────────────────────────────────────────────────


@mcp.tool()
def top_queries(
    start_date: str,
    end_date: str,
    limit: int = 20,
    country: str = "fra",
) -> str:
    """Retourne les requêtes de recherche les plus performantes.

    Args:
        start_date: Date de début au format 'YYYY-MM-DD'.
        end_date:   Date de fin au format 'YYYY-MM-DD'.
        limit:      Nombre de requêtes retournées (défaut: 20).
        country:    Code pays ISO 3166-1 alpha-3 (défaut: 'fra').
    """
    if not SITE_URL:
        return "SEARCH_CONSOLE_SITE_URL manquant dans .env"
    try:
        service = build("searchconsole", "v1", credentials=_get_credentials())
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query"],
            "dimensionFilterGroups": [
                {"filters": [{"dimension": "country", "expression": country}]}
            ],
            "rowLimit": limit,
        }
        response = service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()
        rows = response.get("rows", [])
        if not rows:
            return "Aucune donnée disponible pour cette période."
        lines = ["Requête | Clics | Impressions | CTR | Position"]
        for r in rows:
            lines.append(
                f"{r['keys'][0]} | {r['clicks']} | {r['impressions']} | "
                f"{r['ctr']:.1%} | {r['position']:.1f}"
            )
        return "\n".join(lines)
    except HttpError as e:
        return f"Erreur Search Console : {e}"


@mcp.tool()
def page_performance(
    url: str,
    start_date: str,
    end_date: str,
) -> str:
    """Performances SEO d'une URL spécifique.

    Args:
        url:        URL complète de la page (doit être dans la propriété Search Console).
        start_date: Date de début au format 'YYYY-MM-DD'.
        end_date:   Date de fin au format 'YYYY-MM-DD'.
    """
    if not SITE_URL:
        return "SEARCH_CONSOLE_SITE_URL manquant dans .env"
    try:
        service = build("searchconsole", "v1", credentials=_get_credentials())
        body = {
            "startDate": start_date,
            "endDate": end_date,
            "dimensions": ["query"],
            "dimensionFilterGroups": [{"filters": [{"dimension": "page", "expression": url}]}],
            "rowLimit": 10,
        }
        response = service.searchanalytics().query(siteUrl=SITE_URL, body=body).execute()
        rows = response.get("rows", [])
        if not rows:
            return f"Aucune donnée pour {url}."
        lines = [f"Performances de {url}", "Requête | Clics | Impressions | CTR | Position"]
        for r in rows:
            lines.append(
                f"{r['keys'][0]} | {r['clicks']} | {r['impressions']} | "
                f"{r['ctr']:.1%} | {r['position']:.1f}"
            )
        return "\n".join(lines)
    except HttpError as e:
        return f"Erreur Search Console : {e}"


# ── DataForSEO ────────────────────────────────────────────────────────────────


@mcp.tool()
def keyword_ideas(keyword: str, language: str = "fr", location: int = 2250) -> str:
    """Génère des idées de mots-clés similaires.

    Args:
        keyword:  Mot-clé de départ.
        language: Code langue (défaut: 'fr').
        location: Code localisation DataForSEO (défaut: 2250 = France).
    """
    if not DATAFORSEO_LOGIN:
        return "DATAFORSEO_LOGIN/PASSWORD manquants dans .env"
    try:
        payload = [
            {"keyword": keyword, "language_code": language, "location_code": location, "limit": 20}
        ]
        r = httpx.post(
            "https://api.dataforseo.com/v3/dataforseo_labs/google/keyword_ideas/live",
            json=payload,
            headers=_dataforseo_headers(),
            timeout=30,
        )
        r.raise_for_status()
        tasks = r.json().get("tasks", [])
        if not tasks or tasks[0]["status_code"] != 20000:
            return f"Erreur DataForSEO : {tasks[0].get('status_message', 'Inconnue')}"
        items = tasks[0]["result"][0].get("items", [])
        lines = ["Mot-clé | Volume mensuel | Difficulté"]
        for item in items[:20]:
            kd = item.get("keyword_info", {})
            lines.append(
                f"{item['keyword']} | {kd.get('search_volume', '?')} | "
                f"{item.get('keyword_difficulty', '?')}"
            )
        return "\n".join(lines)
    except httpx.HTTPError as e:
        return f"Erreur DataForSEO : {e}"


@mcp.tool()
def serp_analysis(keyword: str, language: str = "fr", location: int = 2250) -> str:
    """Analyse les 10 premiers résultats Google pour un mot-clé.

    Args:
        keyword:  Mot-clé à analyser.
        language: Code langue (défaut: 'fr').
        location: Code localisation DataForSEO (défaut: 2250 = France).
    """
    if not DATAFORSEO_LOGIN:
        return "DATAFORSEO_LOGIN/PASSWORD manquants dans .env"
    try:
        payload = [{"keyword": keyword, "language_code": language, "location_code": location}]
        r = httpx.post(
            "https://api.dataforseo.com/v3/serp/google/organic/live/regular",
            json=payload,
            headers=_dataforseo_headers(),
            timeout=30,
        )
        r.raise_for_status()
        tasks = r.json().get("tasks", [])
        if not tasks or tasks[0]["status_code"] != 20000:
            return f"Erreur DataForSEO : {tasks[0].get('status_message', 'Inconnue')}"
        items = tasks[0]["result"][0].get("items", [])
        lines = [f"SERP pour '{keyword}'", "Pos | Titre | URL"]
        for item in items[:10]:
            if item.get("type") == "organic":
                lines.append(f"{item['rank_absolute']} | {item['title']} | {item['url']}")
        return "\n".join(lines)
    except httpx.HTTPError as e:
        return f"Erreur DataForSEO : {e}"


if __name__ == "__main__":
    mcp.run()
