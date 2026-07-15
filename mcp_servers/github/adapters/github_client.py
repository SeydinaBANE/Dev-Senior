"""
Adapter GitHub — wrappe PyGithub. Seul fichier autorisé à importer `github`
(le SDK) ; mcp_servers/github/server.py passe par cette classe pour tout
appel réseau et garde le formatage de réponse pour le LLM.
"""

import os
from collections.abc import Iterable

from github import Commit, ContentFile, Github, Issue, PullRequest
from github.ContentFile import ContentFile as ContentFileType


class GithubClient:
    def __init__(self, token: str | None = None) -> None:
        token = token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise RuntimeError("GITHUB_TOKEN manquant dans .env")
        self._gh = Github(token)

    def list_pulls(self, repo: str, state: str) -> Iterable[PullRequest.PullRequest]:
        return self._gh.get_repo(repo).get_pulls(state=state)

    def get_pull(self, repo: str, pr_number: int) -> PullRequest.PullRequest:
        return self._gh.get_repo(repo).get_pull(pr_number)

    def read_file(self, repo: str, path: str, ref: str) -> ContentFileType | list[ContentFileType]:
        return self._gh.get_repo(repo).get_contents(path, ref=ref)

    def search_code(self, repo: str, query: str) -> Iterable[ContentFile.ContentFile]:
        return self._gh.search_code(f"{query} repo:{repo}")

    def list_issues(self, repo: str, **kwargs: object) -> Iterable[Issue.Issue]:
        return self._gh.get_repo(repo).get_issues(**kwargs)

    def create_issue(self, repo: str, **kwargs: object) -> Issue.Issue:
        return self._gh.get_repo(repo).create_issue(**kwargs)

    def recent_commits(self, repo: str, branch: str) -> Iterable[Commit.Commit]:
        return self._gh.get_repo(repo).get_commits(sha=branch)
