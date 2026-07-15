"""
MCP Server GitHub — outils pour l'agent Dev Senior.

Outils exposés :
- list_prs        : PRs ouvertes d'un dépôt
- get_pr_diff     : diff complet d'une PR
- read_file       : lire un fichier du dépôt
- search_code     : recherche dans le code
- list_issues     : issues ouvertes
- create_issue    : créer une issue
- recent_commits  : historique des commits
"""

from github import GithubException
from mcp.server.fastmcp import FastMCP

from mcp_servers.github.adapters.github_client import GithubClient

mcp = FastMCP("github")
_client_instance: GithubClient | None = None


def _client() -> GithubClient:
    global _client_instance
    if _client_instance is None:
        _client_instance = GithubClient()
    return _client_instance


# ── Outils ───────────────────────────────────────────────────────────────────


@mcp.tool()
def list_prs(repo: str, state: str = "open") -> str:
    """Liste les pull requests d'un dépôt.

    Args:
        repo:  Nom du dépôt au format 'owner/repo'.
        state: 'open', 'closed' ou 'all'.
    """
    try:
        pulls = _client().list_pulls(repo, state)
        lines = [f"#{pr.number} [{pr.state}] {pr.title} — {pr.user.login}" for pr in pulls]
        return "\n".join(lines) if lines else "Aucune PR trouvée."
    except RuntimeError as e:
        return str(e)
    except GithubException as e:
        return f"Erreur GitHub : {e.data.get('message', str(e))}"


@mcp.tool()
def get_pr_diff(repo: str, pr_number: int) -> str:
    """Retourne le diff complet d'une pull request.

    Args:
        repo:      Nom du dépôt au format 'owner/repo'.
        pr_number: Numéro de la PR.
    """
    try:
        pr = _client().get_pull(repo, pr_number)
        files = pr.get_files()
        parts = [f"PR #{pr_number} : {pr.title}\n"]
        for f in files:
            parts.append(f"--- {f.filename} (+{f.additions} -{f.deletions})")
            if f.patch:
                parts.append(f.patch)
        return "\n".join(parts)
    except RuntimeError as e:
        return str(e)
    except GithubException as e:
        return f"Erreur GitHub : {e.data.get('message', str(e))}"


@mcp.tool()
def read_file(repo: str, path: str, ref: str = "main") -> str:
    """Lit le contenu d'un fichier dans le dépôt.

    Args:
        repo: Nom du dépôt au format 'owner/repo'.
        path: Chemin du fichier (ex: 'src/main.py').
        ref:  Branche ou commit (défaut: 'main').
    """
    try:
        content = _client().read_file(repo, path, ref)
        if isinstance(content, list):
            return "\n".join(f.path for f in content)
        return content.decoded_content.decode("utf-8")
    except RuntimeError as e:
        return str(e)
    except GithubException as e:
        return f"Erreur GitHub : {e.data.get('message', str(e))}"


@mcp.tool()
def search_code(repo: str, query: str) -> str:
    """Recherche du code dans le dépôt via l'API GitHub.

    Args:
        repo:  Nom du dépôt au format 'owner/repo'.
        query: Termes de recherche (ex: 'def authenticate').
    """
    try:
        results = _client().search_code(repo, query)
        lines = [f"{r.path}:{r.name}" for r in results]
        return "\n".join(lines[:20]) if lines else "Aucun résultat."
    except RuntimeError as e:
        return str(e)
    except GithubException as e:
        return f"Erreur GitHub : {e.data.get('message', str(e))}"


@mcp.tool()
def list_issues(repo: str, state: str = "open", labels: str = "") -> str:
    """Liste les issues d'un dépôt.

    Args:
        repo:   Nom du dépôt au format 'owner/repo'.
        state:  'open', 'closed' ou 'all'.
        labels: Labels filtrés, séparés par des virgules (optionnel).
    """
    try:
        kwargs: dict = {"state": state}
        if labels:
            kwargs["labels"] = [lbl.strip() for lbl in labels.split(",")]
        issues = _client().list_issues(repo, **kwargs)
        lines = [f"#{i.number} {i.title} — {i.user.login}" for i in issues if not i.pull_request]
        return "\n".join(lines) if lines else "Aucune issue trouvée."
    except RuntimeError as e:
        return str(e)
    except GithubException as e:
        return f"Erreur GitHub : {e.data.get('message', str(e))}"


@mcp.tool()
def create_issue(repo: str, title: str, body: str, labels: str = "") -> str:
    """Crée une issue GitHub.

    Args:
        repo:   Nom du dépôt au format 'owner/repo'.
        title:  Titre de l'issue.
        body:   Description (markdown supporté).
        labels: Labels à appliquer, séparés par des virgules (optionnel).
    """
    try:
        kwargs: dict = {"title": title, "body": body}
        if labels:
            kwargs["labels"] = [lbl.strip() for lbl in labels.split(",")]
        issue = _client().create_issue(repo, **kwargs)
        return f"Issue créée : #{issue.number} — {issue.html_url}"
    except RuntimeError as e:
        return str(e)
    except GithubException as e:
        return f"Erreur GitHub : {e.data.get('message', str(e))}"


@mcp.tool()
def recent_commits(repo: str, branch: str = "main", limit: int = 10) -> str:
    """Retourne les derniers commits d'une branche.

    Args:
        repo:   Nom du dépôt au format 'owner/repo'.
        branch: Nom de la branche (défaut: 'main').
        limit:  Nombre de commits à retourner (max 50).
    """
    try:
        commits = _client().recent_commits(repo, branch)
        lines = [
            f"{c.sha[:7]} {c.commit.message.splitlines()[0]} — {c.commit.author.name}"
            for c in list(commits)[: min(limit, 50)]
        ]
        return "\n".join(lines)
    except RuntimeError as e:
        return str(e)
    except GithubException as e:
        return f"Erreur GitHub : {e.data.get('message', str(e))}"


if __name__ == "__main__":
    mcp.run()
