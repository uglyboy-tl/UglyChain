from __future__ import annotations

from pathlib import Path

import pytest

from uglychain.tools.coder import _convert_path, _convert_to_unified_diff, read_file, replace_file, write_file


def test_read_file(mocker):
    mocker.patch("uglychain.tools.coder._convert_path", return_value=Path("/fake/path"))
    mocker.patch("pathlib.Path.read_text", return_value="file content")

    result = read_file(path="/fake/path")
    assert result == "file content"


def test_read_file_error(mocker):
    mocker.patch("uglychain.tools.coder._convert_path", return_value=Path("/fake/path"))
    mocker.patch("pathlib.Path.read_text", side_effect=Exception("read error"))

    result = read_file(path="/fake/path")
    assert "Error reading file" in result


def test_write_file(mocker):
    mocker.patch("uglychain.tools.coder._convert_path", return_value=Path("/fake/path"))
    mocker.patch("pathlib.Path.write_text", return_value=None)
    mocker.patch("pathlib.Path.mkdir", return_value=None)

    result = write_file(path="/fake/path", content="new content")
    assert result == "Successfully wrote to file: /fake/path"


def test_write_file_error(mocker):
    mocker.patch("uglychain.tools.coder._convert_path", return_value=Path("/fake/path"))
    mocker.patch("pathlib.Path.write_text", side_effect=Exception("write error"))
    mocker.patch("pathlib.Path.mkdir", return_value=None)

    result = write_file(path="/fake/path", content="new content")
    assert "Error writing to file" in result


def test_replace_file(mocker):
    mocker.patch("uglychain.tools.coder._convert_path", return_value=Path("/fake/path"))
    mocker.patch("pathlib.Path.read_text", return_value="original content")
    mocker.patch("pathlib.Path.write_text", return_value=None)
    mocker.patch("pathlib.Path.mkdir", return_value=None)
    mocker.patch(
        "uglychain.tools.coder._convert_to_unified_diff",
        return_value="--- a/file\n+++ b/file\n@@ -1,1 +1,1 @@\n-original content\n+new content\n",
    )

    result = replace_file(
        path="/fake/path", diff="<<<<<<< SEARCH\noriginal content\n=======\nnew content\n>>>>>>> REPLACE"
    )
    assert result == "Successfully replaced content in file: /fake/path"


def test_replace_file_error(mocker):
    mocker.patch("uglychain.tools.coder._convert_path", return_value=Path("/fake/path"))
    mocker.patch("pathlib.Path.read_text", side_effect=Exception("read error"))
    mocker.patch("pathlib.Path.write_text", return_value=None)
    mocker.patch("pathlib.Path.mkdir", return_value=None)

    result = replace_file(
        path="/fake/path", diff="<<<<<<< SEARCH\noriginal content\n=======\nnew content\n>>>>>>> REPLACE"
    )
    assert "Error replacing content in file" in result


def test_convert_path():
    assert _convert_path("~/test") == Path.home() / "test"
    assert _convert_path("/test") == Path("/test")


def test_convert_to_unified_diff():
    original_content = "line1\nline2\nline3"
    search_replace_diff = "<<<<<<< SEARCH\nline2\n=======\nnew_line2\n>>>>>>> REPLACE"
    expected_diff = "--- a/file\n+++ b/file\n@@ -1,1 +1,1 @@\n-line2\n+new_line2\n"
    assert _convert_to_unified_diff(original_content, search_replace_diff) == expected_diff
