from __future__ import annotations

from uglychain.react import final_answer


def test_final_answer():
    assert final_answer(answer="Test Answer") == "Test Answer"
