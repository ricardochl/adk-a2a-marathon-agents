"""Evaluator configuration.

Constants live here (not in agent.py) so that tools.py and agent.py can both
import them without depending on each other. In the codelab, tools.py imports
from agent.py and agent.py imports from tools.py: it only works when modules
are imported in a particular order, and a bare `except Exception` in
__init__.py hides the failure.
"""

import os

AGENT_NAME = "evaluator_agent"
AGENT_DESCRIPTION = (
    "Evaluates marathon plans across multiple quality criteria using Vertex AI "
    "Evaluation with custom metrics. Acts as LLM-as-Judge to score plans and "
    "provide actionable feedback for iterative improvement."
)

# gemini-3.1-pro-preview for the best judging quality.
# Note: Gemini 3 models are served from GOOGLE_CLOUD_LOCATION=global.
MODEL = os.getenv("EVALUATOR_MODEL", "gemini-3.1-pro-preview")

# "vertex" (default): Vertex AI Evaluation with 6 LLM judges + 1 deterministic rule.
# "heuristic": skip the judges (useful live when the API is slow or out of quota).
EVALUATOR_MODE = os.getenv("EVALUATOR_MODE", "vertex").strip().lower()

# Weights must sum to 1.0
CRITERION_WEIGHTS = {
    "safety_compliance": 0.20,
    "community_impact": 0.15,
    "logistics_completeness": 0.20,
    "financial_viability": 0.15,
    "participant_experience": 0.15,
    "intent_alignment": 0.10,
    "distance_compliance": 0.05,
}

SEVERITY_THRESHOLDS = {"high": 40.0, "medium": 60.0, "low": 80.0}
PASS_THRESHOLD = 85.0

# Each judge returns a long explanation; when the agent copies all seven into
# EvaluationResult the structured output gets truncated. Trim every finding.
MAX_FINDING_CHARS = 400
MAX_OUTPUT_TOKENS = 8192
