"""Prompt lab: an analyst asks the assistant for a reusable question about one metric, and
the lab runs that question for every metric in the KPI table.

Used from a notebook (`from insights.prompt_lab import ...`).
"""

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from insights import metrics
from insights.llm import ANALYST_MODEL

llm = ChatOpenAI(model=ANALYST_MODEL, temperature=0)

TEMPLATE_REQUEST = (
    "Write one analysis question an analyst could ask about a KPI. Use {placeholder} where "
    "the metric name goes and nothing else. Reply with the question only. Goal: {goal}"
)


def suggest_question(goal: str) -> PromptTemplate:
    """A question template in Jinja syntax, so analysts can add loops over past weeks."""
    draft = llm.invoke(TEMPLATE_REQUEST.format(placeholder="{{ metric }}", goal=goal))
    return PromptTemplate.from_template(draft.content, template_format="jinja2")


def suggest_simple_question(goal: str) -> PromptTemplate:
    """The same, as a plain f-string template (no loops or filters)."""
    draft = llm.invoke(TEMPLATE_REQUEST.format(placeholder="{metric}", goal=goal))
    return PromptTemplate.from_template(draft.content)


def run_for_all_metrics(question: PromptTemplate) -> dict[str, str]:
    answers = {}
    for name in metrics.KPI_NAMES:
        answers[name] = llm.invoke(question.format(metric=name)).content
    return answers
