import base64
import binascii
import os
from urllib.parse import quote

import requests


class RepositoryNotFoundError(Exception):
    pass


class ReadmeTooShortError(Exception):
    pass


class GitHubUnavailableError(Exception):
    pass


def fetch_readme(owner, repo):
    url = (
        "https://api.github.com/repos/"
        f"{quote(owner, safe='')}/{quote(repo, safe='')}/readme"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as error:
        raise GitHubUnavailableError("GitHub could not be reached") from error

    if response.status_code == 404:
        raise RepositoryNotFoundError("Repository or README not found")
    if not response.ok:
        raise GitHubUnavailableError("GitHub could not fetch the repository README")

    try:
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("README response was not an object")
        if payload.get("encoding") != "base64" or not isinstance(
            payload.get("content"), str
        ):
            raise ValueError("README response did not contain base64 content")
        readme = base64.b64decode(payload["content"]).decode("utf-8", errors="replace")
    except (ValueError, TypeError, binascii.Error) as error:
        raise GitHubUnavailableError("GitHub returned an invalid README response") from error

    readme = readme[:4000]
    if len(readme.strip()) < 20:
        raise ReadmeTooShortError("The repository README must be at least 20 characters")

    return readme
