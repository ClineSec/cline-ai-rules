import math
import os
import sys

import numpy as np
from agents import Agent, Runner, run_demo_loop
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import (
    MagenticOneGroupChat,
    RoundRobinGroupChat,
    SelectorGroupChat,
    Swarm,
)
from claude_agent_sdk import ClaudeAgentOptions
from crewai import Agent as CrewAgent
from crewai import LiteAgent
from langchain_classic.agents import AgentExecutor, initialize_agent
from langchain_community.agent_toolkits import create_sql_agent
from smolagents import CodeAgent, ToolCallingAgent

LONG_RUN_TURNS = 5_000
SAFE_TURNS = 40
RUN_SETTINGS: dict = {}
requested_turns = 12


def langchain_cases(agent, tools, llm, toolkit):
    # ruleid: agent-loop-unbounded-iterations
    AgentExecutor(agent=agent, tools=tools, max_iterations=None)
    AgentExecutor.from_agent_and_tools(
        agent=agent,
        tools=tools,
        # ruleid: agent-loop-unbounded-iterations
        max_iterations=None,
        max_execution_time=None,
    )
    # ruleid: agent-loop-unbounded-iterations
    initialize_agent(tools, llm, max_iterations=None)
    # ruleid: agent-loop-unbounded-iterations
    create_sql_agent(llm, toolkit=toolkit, agent_executor_kwargs={"max_iterations": None})
    # ruleid: agent-loop-unbounded-iterations
    AgentExecutor(agent=agent, tools=tools, max_iterations=10_000)
    # ruleid: agent-loop-unbounded-iterations
    AgentExecutor(agent=agent, tools=tools, max_iterations=float("inf"))

    # ok: agent-loop-unbounded-iterations
    AgentExecutor(agent=agent, tools=tools, max_iterations=None, max_execution_time=120)
    # ok: agent-loop-unbounded-iterations
    AgentExecutor(agent=agent, tools=tools, max_iterations=50)
    # ok: agent-loop-unbounded-iterations
    AgentExecutor(agent=agent, tools=tools, max_iterations=999)
    # ok: agent-loop-unbounded-iterations
    AgentExecutor(agent=agent, tools=tools, max_iterations=int(os.environ.get("AGENT_MAX_ITERATIONS", "5000")))


async def openai_agents_cases(agent: Agent, prompt: str, configured_turns: int | None = None):
    # ruleid: agent-loop-unbounded-iterations
    await Runner.run(agent, prompt, max_turns=None)
    # ruleid: agent-loop-unbounded-iterations
    Runner.run_sync(agent, prompt, max_turns=None)
    # ruleid: agent-loop-unbounded-iterations
    Runner.run_streamed(agent, prompt, max_turns=LONG_RUN_TURNS)
    # ruleid: agent-loop-unbounded-iterations
    await run_demo_loop(agent, max_turns=None)

    # ok: agent-loop-unbounded-iterations
    await Runner.run(agent, prompt, max_turns=SAFE_TURNS)
    # ok: agent-loop-unbounded-iterations
    await Runner.run(agent, prompt)
    # A config value with a large fallback, and a clamp, are left alone.
    # ok: agent-loop-unbounded-iterations
    await Runner.run(agent, prompt, max_turns=RUN_SETTINGS.get("max_turns", 5000))
    # ok: agent-loop-unbounded-iterations
    await Runner.run(agent, prompt, max_turns=configured_turns or 5000)
    # ok: agent-loop-unbounded-iterations
    await Runner.run(agent, prompt, max_turns=min(requested_turns, 5000))
    # A cap read from an optional config section. A value that starts with a parenthesized
    # receiver like this one made OpenGrep 1.30.2 abort the whole file before the guard.
    # ok: agent-loop-unbounded-iterations
    await Runner.run(agent, prompt, max_turns=(RUN_SETTINGS.get("agent") or {}).get("max_turns", 30))
    # Agent.as_tool falls back to the SDK default of 10 turns when max_turns is None.
    # ok: agent-loop-unbounded-iterations
    agent.as_tool(tool_name="triage", tool_description="Triage a ticket", max_turns=None)


def claude_and_anthropic_cases(client, tools, messages):
    # ruleid: agent-loop-unbounded-iterations
    ClaudeAgentOptions(cwd="/srv/repo", max_turns=sys.maxsize)
    # ruleid: agent-loop-unbounded-iterations
    client.beta.messages.tool_runner(model="claude-x", max_tokens=1024, tools=tools, messages=messages, max_iterations=100_000)

    # A spend cap still bounds the run.
    # ok: agent-loop-unbounded-iterations
    ClaudeAgentOptions(cwd="/srv/repo", max_turns=5000, max_budget_usd=2.0)
    # ok: agent-loop-unbounded-iterations
    ClaudeAgentOptions(cwd="/srv/repo", max_turns=200)
    # ok: agent-loop-unbounded-iterations
    client.beta.messages.tool_runner(model="claude-x", max_tokens=1024, tools=tools, messages=messages, max_iterations=30)


def crewai_and_smolagents_cases(llm, tools, model):
    # ruleid: agent-loop-unbounded-iterations
    CrewAgent(role="Researcher", goal="g", backstory="b", llm=llm, max_iter=10**6)
    # ruleid: agent-loop-unbounded-iterations
    LiteAgent(role="Helper", goal="g", backstory="b", max_iterations=math.inf)
    # ruleid: agent-loop-unbounded-iterations
    CodeAgent(tools=tools, model=model, max_steps=np.inf)
    agent = ToolCallingAgent(tools=tools, model=model)
    # ruleid: agent-loop-unbounded-iterations
    agent.run("Summarize the queue", max_steps=2500)

    # ok: agent-loop-unbounded-iterations
    CrewAgent(role="Researcher", goal="g", backstory="b", llm=llm, max_iter=50)
    # A time limit still bounds the agent.
    # ok: agent-loop-unbounded-iterations
    CrewAgent(role="Researcher", goal="g", backstory="b", llm=llm, max_iter=5000, max_execution_time=300)
    # ok: agent-loop-unbounded-iterations
    CodeAgent(tools=tools, model=model, max_steps=30)


def autogen_cases(model_client, writer, reviewer):
    # ruleid: agent-loop-unbounded-iterations
    team = RoundRobinGroupChat([writer, reviewer])
    # ruleid: agent-loop-unbounded-iterations
    picker = SelectorGroupChat([writer, reviewer], model_client=model_client, termination_condition=None)
    # ruleid: agent-loop-unbounded-iterations
    swarm = Swarm([writer, reviewer])
    # ruleid: agent-loop-unbounded-iterations
    MagenticOneGroupChat([writer, reviewer], model_client=model_client, max_turns=None)
    # ruleid: agent-loop-unbounded-iterations
    AssistantAgent("writer", model_client=model_client, max_tool_iterations=1000)

    # ok: agent-loop-unbounded-iterations
    RoundRobinGroupChat([writer, reviewer], termination_condition=TextMentionTermination("APPROVE") | MaxMessageTermination(20))
    # ok: agent-loop-unbounded-iterations
    SelectorGroupChat([writer, reviewer], model_client=model_client, max_turns=12)
    # ok: agent-loop-unbounded-iterations
    MagenticOneGroupChat([writer, reviewer], model_client=model_client)
    # ok: agent-loop-unbounded-iterations
    AssistantAgent("writer", model_client=model_client, max_tool_iterations=5)
    # AG2's max_round and max_consecutive_auto_reply are only read in files that import autogen.
    # ok: agent-loop-unbounded-iterations
    AssistantAgent("writer", model_client=model_client, max_consecutive_auto_reply=10_000)
    # ok: agent-loop-unbounded-iterations
    RoundRobinGroupChat([writer, reviewer], max_turns=None, termination_condition=MaxMessageTermination(30))
    return team, picker, swarm


def langgraph_cases(graph, state, settings):
    # ruleid: agent-loop-unbounded-iterations
    graph.invoke(state, {"recursion_limit": 1_000_000})
    # ruleid: agent-loop-unbounded-iterations
    graph.with_config(recursion_limit=float("inf"))
    # ruleid: agent-loop-unbounded-iterations
    graph.stream(state, config={"configurable": {"thread_id": "t1"}, "recursion_limit": sys.maxsize})

    # ok: agent-loop-unbounded-iterations
    graph.invoke(state, {"recursion_limit": 200})
    # ok: agent-loop-unbounded-iterations
    graph.invoke(state, {"recursion_limit": settings.get_value("recursion_limit", 100000)})
    # ok: agent-loop-unbounded-iterations
    graph.invoke(state, {"recursion_limit": (settings.get("graph") or {}).get("recursion_limit", 50)})
    # Below LangGraph's own default of 10,007.
    # ok: agent-loop-unbounded-iterations
    graph.invoke(state, {"recursion_limit": 1000})
    # ok: agent-loop-unbounded-iterations
    sys.setrecursionlimit(1_000_000)


class RoutingDesk:
    route_turns: int | None = None
    review_turns = 30
    draft_turns = None

    async def route(self, agent, prompt):
        # ruleid: agent-loop-unbounded-iterations
        return await Runner.run(agent, prompt, max_turns=self.route_turns)

    async def review(self, agent, prompt):
        # ok: agent-loop-unbounded-iterations
        return await Runner.run(agent, prompt, max_turns=self.review_turns)

    def executor(self, agent, tools):
        # ruleid: agent-loop-unbounded-iterations
        return AgentExecutor(agent=agent, tools=tools, max_iterations=self.draft_turns)


class ConfiguredDesk:
    route_turns: int | None = None

    def __init__(self, route_turns: int = 20):
        self.route_turns = route_turns

    async def route(self, agent, prompt):
        # The instance value set in __init__ replaces the class default.
        # ok: agent-loop-unbounded-iterations
        return await Runner.run(agent, prompt, max_turns=self.route_turns)
