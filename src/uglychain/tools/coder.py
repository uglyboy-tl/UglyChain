from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from unidiff import PatchSet

from uglychain import Tool


@Tool.tool
@dataclass
class Coder:
    @staticmethod
    def read_file(path: str) -> str:
        """Request to read the contents of a file at the specified path. Use this when you need to examine the contents of an existing file you do not know the contents of, for example to analyze code, review text files, or extract information from configuration files. Automatically extracts raw text from PDF and DOCX files. May not be suitable for other types of binary files, as it returns the raw content as a string."""
        _path = _convert_path(path)
        try:
            return _path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Error reading file: {path}. Error: {str(e)}"

    @staticmethod
    def write_to_file(path: str, content: str) -> str:
        """Request to write content to a file at the specified path. If the file exists, it will be overwritten with the provided content. If the file doesn't exist, it will be created. This tool will automatically create any directories needed to write the file.
        Usage:
        <path>File path here</path>
        <content>
        Your file content here
        </content>"""
        _path = _convert_path(path)
        try:
            _path.parent.mkdir(parents=True, exist_ok=True)
            _path.write_text(content, encoding="utf-8")
            return f"Successfully wrote to file: {path}"
        except Exception as e:
            return f"Error writing to file: {path}. Error: {str(e)}"

    @staticmethod
    def replace_in_file(path: str, diff: str) -> str:
        """
        Description: Request to replace sections of content in an existing file using SEARCH/REPLACE blocks that define exact changes to specific parts of the file. This tool should be used when you need to make targeted changes to specific parts of a file.

        Parameters:
        - path: (required) The path of the file to modify
        - diff: (required) One or more SEARCH/REPLACE blocks following this format:
        ```
        <<<<<<< SEARCH
        [exact content to find]
        =======
        [new content to replace with]
        >>>>>>> REPLACE
        ```

        Critical rules:
        1. SEARCH content must match the associated file section to find EXACTLY:
            * Match character-for-character including whitespace, indentation, line endings
            * Include all comments, docstrings, etc.
        2. SEARCH/REPLACE blocks will ONLY replace the first match occurrence.
            * Including multiple unique SEARCH/REPLACE blocks if you need to make multiple changes.
            * Include *just* enough lines in each SEARCH section to uniquely match each set of lines that need to change.
        3. Keep SEARCH/REPLACE blocks concise:
            * Break large SEARCH/REPLACE blocks into a series of smaller blocks that each change a small portion of the file.
            * Include just the changing lines, and a few surrounding lines if needed for uniqueness.
            * Do not include long runs of unchanging lines in SEARCH/REPLACE blocks.
        4. Special operations:
            * To move code: Use two SEARCH/REPLACE blocks (one to delete from original + one to insert at new location)
            * To delete code: Use empty REPLACE section

        Usage:
        <path>File path here</path>
        <diff>
        Search and replace blocks here
        </diff>
        """
        _path = _convert_path(path)
        try:
            original_content = _path.read_text(encoding="utf-8")

            # Convert search/replace format to unified diff
            unified_diff = _convert_to_unified_diff(original_content, diff)

            # Parse the unified diff
            patch_set = PatchSet(io.StringIO(unified_diff))

            for patch in patch_set:
                for hunk in patch:
                    # Find the matching section in the content
                    source_lines = [line.value for line in hunk if line.is_removed or line.is_context]
                    source_text = "\n".join(line.rstrip() for line in source_lines)

                    if source_text in original_content:
                        target_lines = [line.value for line in hunk if line.is_added or line.is_context]
                        target_text = "\n".join(line.rstrip() for line in target_lines)

                        # Replace the content
                        start_pos = original_content.index(source_text)
                        end_pos = start_pos + len(source_text)
                        original_content = original_content[:start_pos] + target_text + original_content[end_pos:]
            _path.parent.mkdir(parents=True, exist_ok=True)
            _path.write_text(original_content, encoding="utf-8")
            return f"Successfully replaced content in file: {path}"
        except Exception as e:
            return f"Error replacing content in file: {path}. Error: {str(e)}"


def _convert_path(path: str) -> Path:
    if "~/" in path:
        return Path(path).expanduser()
    return Path(path)


def _convert_to_unified_diff(original_content: str, search_replace_diff: str) -> str:
    """Convert search/replace diff format to unified diff format."""
    # Parse the search/replace blocks
    lines = search_replace_diff.split("\n")
    diff_lines = []
    search_content: list[str] = []
    replace_content: list[str] = []
    in_search = False
    in_replace = False

    for line in lines:
        if "<<<<<<< SEARCH" in line:
            in_search = True
        elif "=======" in line:
            in_search = False
            in_replace = True
        elif ">>>>>>> REPLACE" in line:
            # Convert accumulated search/replace block to unified diff format
            if search_content and replace_content:
                diff_lines.extend(
                    [
                        "--- a/file",
                        "+++ b/file",
                        f"@@ -1,{len(search_content)} +1,{len(replace_content)} @@",
                    ]
                )
                diff_lines.extend("-" + line for line in search_content)
                diff_lines.extend("+" + line for line in replace_content)
                diff_lines.append("")  # Empty line between hunks
            search_content = []
            replace_content = []
            in_replace = False
        elif in_search:
            search_content.append(line)
        elif in_replace:
            replace_content.append(line)

    return "\n".join(diff_lines)
