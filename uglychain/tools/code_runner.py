from enum import Enum, unique

from loguru import logger

from .languages.applescript import AppleScript
from .languages.javascript import JavaScript
from .languages.powershell import PowerShell
from .languages.python import Python
from .languages.r import R
from .languages.shell import Shell


@unique
class Language(Enum):
    Shell = "shell"
    PowerShell = "powershell"
    AppleScript = "applescript"
    Python = "python"
    R = "r"
    JavaScript = "javascript"
    # HTML = "html"


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


def run_code(language: str, code: str):
    """Executes code on the user's machine and returns the output

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
                logger.trace(chunk["content"])
            else:
                output_messages.append(chunk)
                logger.trace(chunk["content"])
    return output_messages
