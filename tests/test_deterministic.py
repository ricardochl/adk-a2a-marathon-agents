"""Tests for the deterministic parts of the system.

No Google Cloud credentials needed: these cover the pieces that don't call
Gemini (distance check, heuristic evaluator, readiness checklist, route tool,
session cache). Run with:  uv run pytest
"""

import importlib.util
import json
import pathlib
import time

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def _load_route_tools():
    path = ROOT / "src/planner_agent/skills/route-planning/tools.py"
    spec = importlib.util.spec_from_file_location("route_planning_tools", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# --- Evaluator -------------------------------------------------------------

def test_criterion_weights_sum_to_one():
    from src.planner_agent.evaluator.agent import CRITERION_WEIGHTS
    assert sum(CRITERION_WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("The route is 26.2 miles long", 100.0),
        ("Total distance: 42.195 km", 100.0),
        ("Route covers 26.4 miles", 60.0),
        ("Route covers 24 miles", 1.0),
        ("A 45 km course", 1.0),
    ],
)
def test_distance_compliance(text, expected):
    from src.planner_agent.evaluator.tools import _check_distance_compliance_logic
    assert _check_distance_compliance_logic(text)["score"] == expected


async def test_evaluate_plan_heuristic_fallback(monkeypatch):
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    from src.planner_agent.evaluator.tools import evaluate_plan

    plan = (ROOT / "examples/sample_plan.md").read_text()
    result = await evaluate_plan(json.dumps({"user_intent": "Scenic Las Vegas marathon", "proposed_plan": plan}))
    assert result["eval_method"] == "heuristic"
    assert set(result["scores"]) == {
        "safety_compliance", "community_impact", "logistics_completeness",
        "financial_viability", "participant_experience", "intent_alignment",
        "distance_compliance",
    }
    assert 0 <= result["overall_score"] <= 100


async def test_evaluate_plan_invalid_json():
    from src.planner_agent.evaluator.tools import evaluate_plan
    result = await evaluate_plan("not json")
    assert result["eval_method"] == "error" and result["passed"] is False


# --- Simulator -------------------------------------------------------------

async def test_readiness_complete_plan():
    from src.simulator_agent.agent.tools import check_plan_readiness
    result = await check_plan_readiness((ROOT / "examples/sample_plan.md").read_text())
    assert result["missing_elements"] == []
    assert result["readiness_score"] == 1.0


async def test_readiness_incomplete_plan():
    from src.simulator_agent.agent.tools import check_plan_readiness
    result = await check_plan_readiness("A fun run through the park.")
    assert "water_stations" in result["missing_elements"]
    assert result["readiness_score"] < 0.5


# --- Route planning --------------------------------------------------------

@pytest.mark.parametrize("theme", ["scenic", "fast"])
@pytest.mark.parametrize("city", ["Las Vegas", "Madrid", "Tegucigalpa", "San Pedro Sula", "San Salvador", "Unknown City"])
def test_route_is_exactly_a_marathon(city, theme):
    tools = _load_route_tools()
    route = tools.plan_marathon_route(city, ["Landmark A", "Landmark B"], theme)
    assert route["distance_km"] == pytest.approx(42.195, abs=0.01)
    assert route["geojson"]["type"] == "FeatureCollection"
    kinds = {f["properties"].get("kind") for f in route["geojson"]["features"]}
    assert {"start_finish", "landmark", "water_station", "medical_tent"} <= kinds


# --- Session cache ---------------------------------------------------------

def test_ttl_cache_expires():
    from src.planner_agent.services.session_manager import TTLCache
    cache = TTLCache(maxsize=10, ttl=1)
    cache.set("ctx", "session-1")
    assert cache.get("ctx") == "session-1"
    time.sleep(1.1)
    assert cache.get("ctx") is None


def test_ttl_cache_evicts_when_full():
    from src.planner_agent.services.session_manager import TTLCache
    cache = TTLCache(maxsize=3, ttl=60)
    for i in range(4):
        cache.set(f"k{i}", i)
    assert len(cache._cache) <= 3
