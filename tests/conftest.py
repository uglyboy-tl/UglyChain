from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from uglychain.console import Console


@pytest.fixture
def console():
    console = Console()
    console.log = MagicMock()
    console._live = MagicMock()  # Initialize _live attribute
    return console
