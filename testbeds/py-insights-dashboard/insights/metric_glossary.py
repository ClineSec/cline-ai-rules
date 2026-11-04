"""Metric glossary: plain-language definitions for each KPI, written by the model on the
legacy LangChain chains the glossary started on (langchain-classic)."""

import os

from langchain_classic.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from insights import metrics
from insights.llm import ANALYST_MODEL

GLOSSARY_PROMPT = PromptTemplate.from_template(
    "Define the KPI '{metric}' for a non-analyst in two sentences. "
    "Recent values: {recent}. Mention what usually moves it."
)

# Shared by the glossary and the weekly definitions refresh.
CHAIN_SETTINGS = dict(
    verbose=True,
    output_key="definition",
)

# The model's own verbose flag prints nothing for model calls.
glossary_model = ChatOpenAI(model=ANALYST_MODEL, temperature=0, verbose=True)


def glossary_chain() -> LLMChain:
    return LLMChain(llm=glossary_model, prompt=GLOSSARY_PROMPT, **CHAIN_SETTINGS)


def review_chain() -> LLMChain:
    """The reviewer's chain prints its prompt only when they ask for it."""
    return LLMChain(
        llm=glossary_model,
        prompt=GLOSSARY_PROMPT,
        verbose=os.environ.get("GLOSSARY_VERBOSE") == "1",
    )


def define(metric: str) -> str:
    recent = ", ".join(f"{value:,.0f}" for value in metrics.load_kpis()[metric].tail(4))
    return glossary_chain().invoke({"metric": metric, "recent": recent})["definition"]
