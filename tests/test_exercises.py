"""Checks for the optional workshop exercises (docs/EXERCISES.md).

They fail until each exercise is solved, so they are excluded from the
default run. Run one exercise:  uv run pytest -m exercise -k ex2
Run them all:                    uv run pytest -m exercise
"""

import pathlib

import pytest

pytestmark = pytest.mark.exercise

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLE_PLAN = (ROOT / "examples/sample_plan.md").read_text()


# --- Exercise 1: give safety more weight ------------------------------------

def test_ex1_safety_weighs_more_in_hot_climates():
    from src.planner_agent.evaluator.config import CRITERION_WEIGHTS

    assert CRITERION_WEIGHTS["safety_compliance"] == pytest.approx(0.25)
    assert CRITERION_WEIGHTS["community_impact"] == pytest.approx(0.10)
    assert sum(CRITERION_WEIGHTS.values()) == pytest.approx(1.0)


# --- Exercise 2: require a heat protocol -------------------------------------

async def test_ex2_checklist_requires_heat_protocol():
    from src.simulator_agent.agent.tools import check_plan_readiness

    without_heat = SAMPLE_PLAN.replace("Heat protocol", "Weather note").replace("heat", "weather")
    result = await check_plan_readiness(without_heat)
    assert "heat_protocol" in result["checklist"], "Add a 'heat_protocol' key to the checklist"
    assert "heat_protocol" in result["missing_elements"]
    assert "heat_protocol" in result["blockers"], "Add 'heat_protocol' to BLOCKING_CHECKS"
    assert result["total_checks"] == 9


async def test_ex2_sample_plan_still_ready():
    from src.simulator_agent.agent.tools import check_plan_readiness

    result = await check_plan_readiness(SAMPLE_PLAN)
    assert result["checklist"].get("heat_protocol") is True
    assert result["readiness_score"] == 1.0


# --- Exercise 3: write a new tool --------------------------------------------

def test_ex3_estimate_budget_math():
    from src.planner_agent.agent.tools import estimate_budget

    result = estimate_budget(10_000)
    assert result["participants"] == 10_000
    assert result["cost_per_runner_usd"] == pytest.approx(130.0)
    assert result["total_cost_usd"] == pytest.approx(1_300_000.0)
    assert result["suggested_registration_fee_usd"] == pytest.approx(78.0)
    assert result["sponsorship_needed_usd"] == pytest.approx(520_000.0)

    custom = estimate_budget(2_000, cost_per_runner_usd=200)
    assert custom["total_cost_usd"] == pytest.approx(400_000.0)


def test_ex3_planner_has_the_new_tool():
    from src.planner_agent.agent.tools import estimate_budget, get_tools

    assert estimate_budget.__doc__, "Write a docstring: the model reads it to decide when to use the tool"
    names = [getattr(t, "name", None) or type(t).__name__ for t in get_tools()]
    assert "estimate_budget" in names, "Append FunctionTool(func=estimate_budget) in get_tools()"


# --- Exercise 5: teach the Planner about heat ---------------------------------

def test_ex5_instruction_mentions_heat_protocol():
    text = (ROOT / "src/planner_agent/agent/planner-instruction.md").read_text().lower()
    assert "heat protocol" in text, "Add a 'heat protocol' rule to Core Requirements"
