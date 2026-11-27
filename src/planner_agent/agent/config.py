"""Configuration for the Marathon Planner Agent."""

import os

AGENT_NAME = "planner_agent"
AGENT_DESCRIPTION = (
    "Marathon Planner Agent — Lead Architect. "
    "Designs comprehensive city marathon plans with built-in expertise in route design, "
    "traffic management, community impact, and economics. Evaluates plans with the "
    "Evaluator (local sub-agent) and submits them to the Simulation Controller (A2A)."
)
MODEL = os.getenv("PLANNER_MODEL", "gemini-3-flash-preview")

# Automatic iteration: how many times the Planner may revise a plan that did not
# pass the Evaluator and send it again. 0 (default) = a single evaluation, as in
# the codelab. Each revision adds roughly one more full evaluation (time + cost).
MAX_REVISIONS = 3


def _read_revisions() -> int:
    raw = os.getenv("PLANNER_REVISIONS", "0").strip() or "0"
    try:
        value = int(raw)
    except ValueError:
        raise ValueError(f"PLANNER_REVISIONS must be a whole number from 0 to {MAX_REVISIONS}, got {raw!r}")
    return max(0, min(value, MAX_REVISIONS))


PLANNER_REVISIONS = _read_revisions()

# Phase 1: No structured output — agent returns free-form text
OUTPUT_SCHEMA = None
