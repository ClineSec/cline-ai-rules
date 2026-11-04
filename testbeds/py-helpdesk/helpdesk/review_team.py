"""Reply review: an AutoGen team where a drafter and a checker polish replies to tickets."""

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

from .llm import PLANNER_MODEL

DRAFTER_PROMPT = "You draft a short, friendly reply to the ticket you are given."
CHECKER_PROMPT = "You check the draft for tone and accuracy and suggest fixes. Say SHIP IT when it is ready."


def _client() -> OpenAIChatCompletionClient:
    return OpenAIChatCompletionClient(model=PLANNER_MODEL)


def _pair(client: OpenAIChatCompletionClient) -> list[AssistantAgent]:
    drafter = AssistantAgent("drafter", model_client=client, system_message=DRAFTER_PROMPT)
    checker = AssistantAgent("checker", model_client=client, system_message=CHECKER_PROMPT, max_tool_iterations=3)
    return [drafter, checker]


def build_reply_review_team() -> RoundRobinGroupChat:
    # The checker is told to say SHIP IT, but nothing stops the team when it does.
    return RoundRobinGroupChat(
        _pair(_client()),
        name="reply_review",
        description="Drafts and checks replies to tickets.",
    )


def build_escalation_review_team() -> SelectorGroupChat:
    client = _client()
    return SelectorGroupChat(
        _pair(client),
        model_client=client,
        termination_condition=TextMentionTermination("SHIP IT") | MaxMessageTermination(16),
    )


async def review(ticket_text: str) -> str:
    team = build_reply_review_team()
    result = await team.run(task=ticket_text)
    return result.messages[-1].to_text()
