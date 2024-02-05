from typing import Literal

from .languages.applescript import AppleScript
from .languages.javascript import JavaScript
from .languages.powershell import PowerShell
from .languages.python import Python
from .languages.r import R
from .languages.shell import Shell

LANGUAGES = [
    Shell,
    JavaScript,
    AppleScript,
    R,
    PowerShell,
    Python,
]


def get_language(language: str):
    for lang in LANGUAGES:
        if language.lower() == lang.name.lower() or (hasattr(lang, "aliases") and language in lang.aliases):
            return lang
    return None


def run_code(code: str, language: Literal["Shell", "Powershell", "Applescript", "Python", "R", "Javascript"]) -> str:
    """This function allows you to execute code **on the user's machine** and retrieve the terminal output. Notice the Python code is sent to a Jupyter kernel for execution.

    Args:
        language (str): The programming language
        code (str): The code to execute
    """
    active_languages = {}
    if language not in active_languages:
        active_languages[language] = get_language(language)()  # type: ignore

    output_messages = []
    for chunk in active_languages[language].run(code):
        if chunk.get("format") != "active_line":
            if (
                output_messages != []
                and output_messages[-1].get("type") == chunk["type"]
                and output_messages[-1].get("format") == chunk["format"]
            ):
                output_messages[-1]["content"] += chunk["content"]
            else:
                output_messages.append(chunk)

    return "\n".join(a["content"] for a in output_messages)
