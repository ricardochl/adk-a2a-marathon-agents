"""System instructions for the Marathon Planner Agent."""

import pathlib

from .config import PLANNER_REVISIONS

_PROMPT_DIR = pathlib.Path(__file__).parent
_BASE = (_PROMPT_DIR / "planner-instruction.md").read_text()

# The markdown file describes the default flow (one evaluation). With
# PLANNER_REVISIONS > 0 these two pieces are swapped for an iteration loop.
_SINGLE_PASS_RULES = """   - SINGLE PASS ONLY. Do not call twice to verify successful fixes.
   - Report the score as it came back. If you change the plan afterwards, say clearly that those changes were not evaluated.
"""
_SINGLE_PASS_STEP = "5. Send to Evaluator.\n"


def _iteration_rules(revisions: int) -> str:
    rounds = revisions + 1
    return f"""   - ITERATE: if the plan does not pass (`passed` is false), revise it using the findings and send the revised plan again.
   - At most {revisions} revision(s), so at most {rounds} evaluations in total. Stop as soon as a round passes.
   - Change only what the findings ask for and keep everything that already works.
   - In the final answer, show a table with the score of every round and, for each revision, what you changed. The final score is the one of the last round.
"""


def build_instruction(revisions: int) -> str:
    """Return the Planner instruction for a given number of revisions."""
    if revisions <= 0:
        return _BASE
    assert _SINGLE_PASS_RULES in _BASE and _SINGLE_PASS_STEP in _BASE, "planner-instruction.md changed"
    return (
        _BASE.replace(_SINGLE_PASS_RULES, _iteration_rules(revisions))
        .replace(_SINGLE_PASS_STEP,
                 f"5. Send to Evaluator; if it does not pass, revise and re-send (up to {revisions} time(s)).\n")
    )


INSTRUCTION = build_instruction(PLANNER_REVISIONS)
