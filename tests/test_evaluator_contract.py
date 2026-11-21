"""Tests for the judge output contract and the Evaluator's honest fallback.

No credentials needed: the Vertex AI client is replaced by a fake one.
"""

import json
from types import SimpleNamespace

import pytest

from src.planner_agent.evaluator import tools
from src.planner_agent.evaluator.config import CRITERION_WEIGHTS, MAX_FINDING_CHARS

PLAN = json.dumps({"user_intent": "Scenic marathon", "proposed_plan": "26.2 miles, water station, budget"})


def test_six_llm_judges_carry_the_json_contract():
    makers = [
        tools._create_safety_compliance_metric,
        tools._create_community_impact_metric,
        tools._create_logistics_completeness_metric,
        tools._create_financial_viability_metric,
        tools._create_participant_experience_metric,
        tools._create_intent_alignment_metric,
    ]
    metrics = [make() for make in makers]
    assert [m.name for m in metrics] == list(tools.LLM_METRIC_NAMES)
    for m in metrics:
        assert m.judge_model_system_instruction == tools.JUDGE_OUTPUT_CONTRACT
    assert '"score"' in tools.JUDGE_OUTPUT_CONTRACT and '"explanation"' in tools.JUDGE_OUTPUT_CONTRACT


def test_llm_metrics_plus_distance_cover_every_weighted_criterion():
    assert set(tools.LLM_METRIC_NAMES) | {"distance_compliance"} == set(CRITERION_WEIGHTS)


def _fake_vertex(monkeypatch, scores: dict):
    """Patch vertexai so client.evals.evaluate returns the given scores."""
    metric_results = {
        name: SimpleNamespace(score=score, explanation=f"why {name}", error_message="judge said prose")
        for name, score in scores.items()
    }
    result = SimpleNamespace(eval_case_results=[
        SimpleNamespace(response_candidate_results=[SimpleNamespace(metric_results=metric_results)])
    ])
    client = SimpleNamespace(evals=SimpleNamespace(evaluate=lambda **_: result))
    monkeypatch.setattr(tools.vertexai, "init", lambda **_: None)
    monkeypatch.setattr(tools.vertexai, "Client", lambda **_: client)


async def test_all_judges_answer_gives_vertex_result(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo")
    monkeypatch.setenv("EVALUATOR_MODE", "vertex")
    _fake_vertex(monkeypatch, {c: 90.0 for c in CRITERION_WEIGHTS})
    result = await tools.evaluate_plan(PLAN)
    assert result["eval_method"] == "vertex_ai_eval"
    assert result["overall_score"] == pytest.approx(90.0)
    assert result["passed"] is True


async def test_a_judge_without_score_is_never_turned_into_50(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo")
    monkeypatch.setenv("EVALUATOR_MODE", "vertex")
    scores = {c: 90.0 for c in CRITERION_WEIGHTS}
    scores["safety_compliance"] = None
    _fake_vertex(monkeypatch, scores)
    result = await tools.evaluate_plan(PLAN)
    assert result["eval_method"] == "heuristic_fallback"
    assert "safety_compliance" in result["eval_error"]


async def test_heuristic_mode_skips_vertex(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "demo")
    monkeypatch.setenv("EVALUATOR_MODE", "heuristic")

    async def boom(**_):
        raise AssertionError("Vertex AI Evaluation should not be called")

    monkeypatch.setattr(tools, "_run_custom_eval", boom)
    result = await tools.evaluate_plan(PLAN)
    assert result["eval_method"] == "heuristic"
    assert "eval_error" not in result


def test_high_severity_blocks_pass_even_with_high_average():
    scores = {c: 100.0 for c in CRITERION_WEIGHTS}
    scores["distance_compliance"] = 1.0  # 5% weight: the average stays high
    result = tools._build_result(scores, {}, eval_method="test")
    assert result["overall_score"] > 90
    assert result["passed"] is False


def test_long_judge_explanations_are_trimmed():
    scores = {c: 100.0 for c in CRITERION_WEIGHTS}
    scores["community_impact"] = 50.0
    result = tools._build_result(scores, {"community_impact": "x" * 5000}, eval_method="test")
    assert len(result["findings"][0]["description"]) <= MAX_FINDING_CHARS
