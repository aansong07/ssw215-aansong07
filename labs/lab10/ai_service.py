import os
import uuid
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI
from pydantic import BaseModel

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


class ProjectExtraction(BaseModel):
    title: str
    summary: str
    technologies: list[str]


class GitHubProjectDraft(BaseModel):
    title: str
    summary: str
    technologies: list[str]
    difficulty: Literal["Beginner", "Intermediate", "Advanced"]


class ProviderRefusalError(Exception):
    pass


class ProviderUnavailableError(Exception):
    pass


github_sessions = {}
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "missing-api-key")


def _request_project(messages, response_format):
    try:
        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=messages,
            response_format=response_format,
            temperature=0.1,
        )
    except (APIConnectionError, APIStatusError) as error:
        raise ProviderUnavailableError("The AI provider could not be reached") from error
    except Exception as error:
        raise ProviderUnavailableError("The AI provider could not be reached") from error

    message = completion.choices[0].message
    if getattr(message, "refusal", None):
        raise ProviderRefusalError(message.refusal)

    if message.parsed is None:
        raise ProviderRefusalError("The provider did not return a structured project")

    return message.parsed


def extract_project(notes):
    return _request_project(
        [
            {
                "role": "system",
                "content": (
                    "Extract a concise portfolio project from the notes. "
                    "Return a short title, a summary of one or two sentences, "
                    "and a list of technologies."
                ),
            },
            {"role": "user", "content": notes},
        ],
        ProjectExtraction,
    )


def start_github_session(readme):
    messages = [
        {
            "role": "system",
            "content": (
                "Create a concise portfolio project draft from the repository README. "
                "Return a short title, a summary of one or two sentences, a list of "
                "technologies, and difficulty exactly Beginner, Intermediate, or "
                "Advanced. Do not claim technologies that are not supported by the README."
            ),
        },
        {"role": "user", "content": readme},
    ]
    draft = _request_project(messages, GitHubProjectDraft)
    session_id = str(uuid.uuid4())
    messages.append({"role": "assistant", "content": draft.model_dump_json()})
    github_sessions[session_id] = {"draft": draft, "messages": messages}
    return session_id, draft.model_dump()


def refine_github_session(session_id, feedback):
    session = github_sessions.get(session_id)
    if session is None:
        return None

    messages = session["messages"] + [{"role": "user", "content": feedback}]
    draft = _request_project(messages, GitHubProjectDraft)
    messages.append({"role": "assistant", "content": draft.model_dump_json()})
    session["draft"] = draft
    session["messages"] = messages
    return draft.model_dump()


def refine_github_session_blind(session_id, feedback):
    if session_id not in github_sessions:
        return None

    draft = _request_project(
        [{"role": "user", "content": feedback}],
        GitHubProjectDraft,
    )
    return draft.model_dump()


def get_github_session(session_id):
    return github_sessions.get(session_id)


def remove_github_session(session_id):
    github_sessions.pop(session_id, None)
