import os
from pathlib import Path

from dotenv import load_dotenv
from openai import APIConnectionError, APIStatusError, OpenAI
from pydantic import BaseModel

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


class ProjectExtraction(BaseModel):
    title: str
    summary: str
    technologies: list[str]


class ProviderRefusalError(Exception):
    pass


class ProviderUnavailableError(Exception):
    pass


openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or "missing-api-key")


def extract_project(notes):
    try:
        completion = openai_client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
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
            response_format=ProjectExtraction,
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
