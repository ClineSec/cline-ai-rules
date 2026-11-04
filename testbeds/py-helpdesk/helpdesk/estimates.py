"""Answer 'how long will this take' questions with a quick formula from the model."""

import ast

import litellm

from .llm import PLANNER_MODEL

# Ops-approved staffing formula. The model only supplies the hours estimate.
STAFFING_FORMULA = "max(1, round(hours / 6))"
STAFFING_BUILTINS = {"max": max, "round": round}


def estimate_hours(question: str, open_tickets: int) -> float:
    response = litellm.completion(
        model=PLANNER_MODEL,
        messages=[
            {
                "role": "user",
                "content": (
                    "Write a Python arithmetic expression using the variable `open_tickets` "
                    f"that estimates hours for: {question}"
                ),
            }
        ],
    )
    formula = response.choices[0].message.content
    return _evaluate(formula, {"open_tickets": open_tickets})


def engineers_needed(question: str) -> int:
    response = litellm.completion(
        model=PLANNER_MODEL,
        messages=[{"role": "user", "content": f"Estimate hours, as a bare number, for: {question}"}],
    )
    hours = float(response.choices[0].message.content)
    return int(_evaluate(STAFFING_FORMULA, {"hours": hours}, STAFFING_BUILTINS))


def _evaluate(expression: str, variables: dict, builtins: dict | None = None) -> float:
    """Evaluate an arithmetic expression with no builtins unless the caller allows some."""
    return float(eval(expression, {"__builtins__": builtins or {}}, variables))


def parse_saved_estimate(raw: str) -> float:
    # Stored estimates are plain numeric literals written by this service.
    return float(ast.literal_eval(raw))
