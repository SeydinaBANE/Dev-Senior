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
import os
from github import Github, GithubException
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("github")
_gh: Github | None = None


def _client() -> Github:
    global _gh
    if _gh is None:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN manquant dans .env")
        _gh = Github(token)
    return _gh


# ── Outils ───────────────────────────────────────────────────────────────────

@mcp.tool()
def list_prs(repo: str, state: str = "open") -> str:
    """Liste les pull requests d'un dépôt.

    Args:
        repo:  Nom du dépôt au format 'owner/repo'.
        state: 'open', 'closed' ou 'all'.
    """
    try:
        pulls = _client().get_repo(repo).get_pulls(state=state)
        lines = [f"#{pr.number} [{pr.state}] {pr.title} — {pr.user.login}" for pr in pulls]
        return "\n".join(lines) if lines else "Aucune PR trouvée."
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
        pr = _client().get_repo(repo).get_pull(pr_number)
        files = pr.get_files()
        parts = [f"PR #{pr_number} : {pr.title}\n"]
        for f in files:
            parts.append(f"--- {f.filename} (+{f.additions} -{f.deletions})")
            if f.patch:
                parts.append(f.patch)
        return "\n".join(parts)
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
        content = _client().get_repo(repo).get_contents(path, ref=ref)
        if isinstance(content, list):
            return "\n".join(f.path for f in content)
        return content.decoded_content.decode("utf-8")
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
        results = _client().search_code(f"{query} repo:{repo}")
        lines = [f"{r.path}:{r.name}" for r in results]
        return "\n".join(lines[:20]) if lines else "Aucun résultat."
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
            kwargs["labels"] = [l.strip() for l in labels.split(",")]
        issues = _client().get_repo(repo).get_issues(**kwargs)
        lines = [f"#{i.number} {i.title} — {i.user.login}" for i in issues if not i.pull_request]
        return "\n".join(lines) if lines else "Aucune issue trouvée."
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
            kwargs["labels"] = [l.strip() for l in labels.split(",")]
        issue = _client().get_repo(repo).create_issue(**kwargs)
        return f"Issue créée : #{issue.number} — {issue.html_url}"
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
        commits = _client().get_repo(repo).get_commits(sha=branch)
        lines = [
            f"{c.sha[:7]} {c.commit.message.splitlines()[0]} — {c.commit.author.name}"
            for c in list(commits)[: min(limit, 50)]
        ]
        return "\n".join(lines)
    except GithubException as e:
        return f"Erreur GitHub : {e.data.get('message', str(e))}"


if __name__ == "__main__":
    mcp.run()
