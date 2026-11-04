"""Knowledge-base gap finder: a LangChain agent that checks which ticket themes have no article."""

from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from .llm import PLANNER_MODEL

KB_TITLES = {
    "vpn": "Connecting to the VPN from home",
    "printer": "Adding the office printer",
    "mfa": "Resetting your MFA device",
}

GAP_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "You compare ticket themes with the knowledge base and list themes with no article."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

EXECUTOR_DEFAULTS = {"handle_parsing_errors": True, "return_intermediate_steps": True}


@tool
def kb_article_for(topic: str) -> str:
    """Return the title of the knowledge-base article for a topic, or 'none'."""
    return KB_TITLES.get(topic.lower(), "none")


TOOLS = [kb_article_for]


def _agent():
    llm = ChatOpenAI(model=PLANNER_MODEL, temperature=0)
    return create_tool_calling_agent(llm, TOOLS, GAP_PROMPT)


def build_gap_finder() -> AgentExecutor:
    # The full gap report checks every theme of the quarter, and the default cap of 15 cut
    # it off halfway, so the cap was taken off.
    return AgentExecutor(agent=_agent(), tools=TOOLS, max_iterations=None, **EXECUTOR_DEFAULTS)


def build_article_checker() -> AgentExecutor:
    # No step cap, but a two-minute wall clock stops a stuck run.
    return AgentExecutor(
        agent=_agent(),
        tools=TOOLS,
        max_iterations=None,
        max_execution_time=120,
        **EXECUTOR_DEFAULTS,
    )


def build_quick_lookup() -> AgentExecutor:
    return AgentExecutor(agent=_agent(), tools=TOOLS, max_iterations=30, **EXECUTOR_DEFAULTS)
