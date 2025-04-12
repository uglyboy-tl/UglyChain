from __future__ import annotations

from uglychain.planner.prompt import INITIAL_PLAN, UPDATE_PLAN_SYSTEM, UPDATE_PLAN_USER


def test_initial_plan_prompt_exists():
    """Test that the INITIAL_PLAN prompt template exists and has expected content."""
    assert INITIAL_PLAN is not None
    assert isinstance(INITIAL_PLAN, str)
    assert "You are a world expert at analyzing a situation" in INITIAL_PLAN
    assert "## 1. Facts survey" in INITIAL_PLAN
    assert "## 2. Plan" in INITIAL_PLAN
    assert "{task}" in INITIAL_PLAN  # Template variable


def test_update_plan_system_prompt_exists():
    """Test that the UPDATE_PLAN_SYSTEM prompt template exists and has expected content."""
    assert UPDATE_PLAN_SYSTEM is not None
    assert isinstance(UPDATE_PLAN_SYSTEM, str)
    assert "You are a world expert at analyzing a situation" in UPDATE_PLAN_SYSTEM
    assert "{task}" in UPDATE_PLAN_SYSTEM  # Template variable


def test_update_plan_user_prompt_exists():
    """Test that the UPDATE_PLAN_USER prompt template exists and has expected content."""
    assert UPDATE_PLAN_USER is not None
    assert isinstance(UPDATE_PLAN_USER, str)
    assert "## 1. Updated facts survey" in UPDATE_PLAN_USER
    assert "## 2. Plan" in UPDATE_PLAN_USER
    assert "{remaining_steps}" in UPDATE_PLAN_USER  # Template variable


def test_initial_plan_template_variables():
    """Test that the INITIAL_PLAN template contains expected variables."""
    # Check for task variable
    assert "{task}" in INITIAL_PLAN
    # Check for managed_agents variable (in Jinja2 syntax)
    assert "managed_agents" in INITIAL_PLAN


def test_update_plan_system_template_variables():
    """Test that the UPDATE_PLAN_SYSTEM template contains expected variables."""
    template_vars = ["task"]
    for var in template_vars:
        assert "{" + var + "}" in UPDATE_PLAN_SYSTEM


def test_update_plan_user_template_variables():
    """Test that the UPDATE_PLAN_USER template contains expected variables."""
    # Check for remaining_steps variable
    assert "{remaining_steps}" in UPDATE_PLAN_USER
    # Check for managed_agents variable (in Jinja2 syntax)
    assert "managed_agents" in UPDATE_PLAN_USER
