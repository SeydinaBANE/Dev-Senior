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

import os

import httpx
from googleapiclient.errors import HttpError
from mcp.server.fastmcp import FastMCP

from mcp_servers.seo.adapters.dataforseo_client import DataForSeoClient
from mcp_servers.seo.adapters.search_console_client import SearchConsoleClient

mcp = FastMCP("seo")

SITE_URL = os.getenv("SEARCH_CONSOLE_SITE_URL", "")
CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
TOKEN_FILE = os.getenv("GOOGLE_TOKEN_FILE", "token.json")
DATAFORSEO_LOGIN = os.getenv("DATAFORSEO_LOGIN", "")
DATAFORSEO_PASSWORD = os.getenv("DATAFORSEO_PASSWORD", "")

SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

_search_console: SearchConsoleClient | None = None
_dataforseo: DataForSeoClient | None = None


def _search_console_client() -> SearchConsoleClient:
    global _search_console
    if _search_console is None:
        _search_console = SearchConsoleClient(SCOPES, CREDENTIALS_FILE, TOKEN_FILE)
    return _search_console


def _dataforseo_client() -> DataForSeoClient:
    global _dataforseo
    if _dataforseo is None:
        _dataforseo = DataForSeoClient(DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD)
    return _dataforseo


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
        rows = _search_console_client().top_queries(SITE_URL, start_date, end_date, limit, country)
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
        rows = _search_console_client().page_performance(SITE_URL, url, start_date, end_date)
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
        data = _dataforseo_client().keyword_ideas(keyword, language, location)
        tasks = data.get("tasks", [])
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
        data = _dataforseo_client().serp_analysis(keyword, language, location)
        tasks = data.get("tasks", [])
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
