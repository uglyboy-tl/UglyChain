from __future__ import annotations

import pytest
from src.uglychain.config import config
from src.uglychain.prompt import SystemPrompt


@pytest.mark.parametrize(
    "role, objective, description, instructions, expected_language, expected_prompt",
    [
        (
            "Assistant",
            "Solve tasks",
            "Test description",
            [],
            config.default_language,
            (
                "You are Assistant to solve the task: Solve tasks"
                "\n\nTest description"
                f"\n## Instructions\n1. The response must be in {config.default_language}."
            ),
        ),
        (
            "Assistant",
            "Solve complex issues",
            "",
            ["Follow guidelines"],
            "Spanish",
            (
                "You are Assistant to solve the task: Solve complex issues"
                "\n## Instructions"
                "\n1. Follow guidelines"
                "\n2. The response must be in Spanish."
            ),
        ),
    ],
)
def test_system_prompt(role, objective, description, instructions, expected_language, expected_prompt):
    expected_prompt = expected_prompt
    prompt = SystemPrompt(
        role=role, objective=objective, description=description, instructions=instructions, language=expected_language
    )
    assert prompt.role == role
    assert prompt.objective == objective
    assert prompt.description == description
    assert prompt.language == expected_language
    assert prompt.prompt == expected_prompt
    assert repr(prompt) == expected_prompt
