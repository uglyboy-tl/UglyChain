from __future__ import annotations

from pathlib import Path

import pytest

from uglychain.tools.coder import Coder, _convert_path, _convert_to_unified_diff


@pytest.mark.parametrize(
    "path, read_text_return, expected",
    [("/fake/path", "file content", "file content"), ("/fake/path", Exception("read error"), "Error reading file")],
)
def test_read_file(mocker, path, read_text_return, expected):
    mocker.patch("uglychain.tools.coder._convert_path", return_value=Path(path))
    mocker.patch(
        "pathlib.Path.read_text",
        side_effect=read_text_return if isinstance(read_text_return, Exception) else None,
        return_value=None if isinstance(read_text_return, Exception) else read_text_return,
    )

    result = Coder.read_file(path=path)
    assert expected in result


@pytest.mark.parametrize(
    "path, content, write_text_side_effect, expected",
    [
        ("/fake/path", "new content", None, "Successfully wrote to file: /fake/path"),
        ("/fake/path", "new content", Exception("write error"), "Error writing to file"),
    ],
)
def test_write_file(mocker, path, content, write_text_side_effect, expected):
    mocker.patch("uglychain.tools.coder._convert_path", return_value=Path(path))
    mocker.patch("pathlib.Path.write_text", side_effect=write_text_side_effect)
    mocker.patch("pathlib.Path.mkdir", return_value=None)

    result = Coder.write_to_file(path=path, content=content)
    assert expected in result


@pytest.mark.parametrize(
    "path, read_text_return, diff, expected",
    [
        (
            "/fake/path",
            "original content",
            "<<<<<<< SEARCH\noriginal content\n=======\nnew content\n>>>>>>> REPLACE",
            "Successfully replaced content in file: /fake/path",
        ),
        (
            "/fake/path",
            Exception("read error"),
            "<<<<<<< SEARCH\noriginal content\n=======\nnew content\n>>>>>>> REPLACE",
            "Error replacing content in file",
        ),
    ],
)
def test_replace_file(mocker, path, read_text_return, diff, expected):
    mocker.patch("uglychain.tools.coder._convert_path", return_value=Path(path))
    mocker.patch(
        "pathlib.Path.read_text",
        return_value=read_text_return
        if not isinstance(read_text_return, Exception)
        else mocker.Mock(side_effect=read_text_return),
    )
    mocker.patch("pathlib.Path.write_text", return_value=None)
    mocker.patch("pathlib.Path.mkdir", return_value=None)
    mocker.patch(
        "uglychain.tools.coder._convert_to_unified_diff",
        return_value="--- a/file\n+++ b/file\n@@ -1,1 +1,1 @@\n-original content\n+new content\n",
    )

    result = Coder.replace_in_file(path=path, diff=diff)
    assert expected in result


def test_replace_file_error(mocker):
    mocker.patch("uglychain.tools.coder._convert_path", return_value=Path("/fake/path"))
    mocker.patch("pathlib.Path.read_text", side_effect=Exception("read error"))
    mocker.patch("pathlib.Path.write_text", return_value=None)
    mocker.patch("pathlib.Path.mkdir", return_value=None)

    result = Coder.replace_in_file(
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
