"""Ticket routing desk on the OpenAI Agents SDK: triage hands each ticket to a specialist."""

from dataclasses import dataclass

from agents import Agent, Runner

from .llm import PLANNER_MODEL

BILLING = Agent(
    name="Billing specialist",
    model=PLANNER_MODEL,
    instructions="You answer questions about invoices and refunds. Never promise a refund.",
)
ACCESS = Agent(
    name="Access specialist",
    model=PLANNER_MODEL,
    instructions="You help people get back into their accounts. Never reset MFA yourself.",
)
TRIAGE = Agent(
    name="Triage",
    model=PLANNER_MODEL,
    instructions="Read the ticket and hand it to the right specialist.",
    handoffs=[BILLING, ACCESS],
)
# The summary desk consults billing as a tool; as_tool falls back to the SDK's 10 turns.
SUMMARY = Agent(
    name="Summary",
    model=PLANNER_MODEL,
    instructions="Summarize the ticket in two sentences, checking invoice facts with billing.",
    tools=[BILLING.as_tool(tool_name="ask_billing", tool_description="Ask billing a question", max_turns=None)],
)


@dataclass
class RoutedTicket:
    ticket_id: str
    answer: str


class HandoffDesk:
    # Specialists can hand tickets back and forth; some threads took more than the default
    # 10 turns, so the routing cap was removed. Regional desks override these.
    route_turns: int | None = None
    summary_turns = 25

    def __init__(self, triage: Agent = TRIAGE):
        self.triage = triage

    async def route(self, ticket_id: str, ticket_text: str) -> RoutedTicket:
        result = await Runner.run(self.triage, ticket_text, max_turns=self.route_turns)
        return RoutedTicket(ticket_id, str(result.final_output))

    async def summarize(self, ticket_id: str, ticket_text: str) -> RoutedTicket:
        result = await Runner.run(SUMMARY, ticket_text, max_turns=self.summary_turns)
        return RoutedTicket(ticket_id, str(result.final_output))


class EmeaHandoffDesk(HandoffDesk):
    # EMEA tickets bounce between three language queues; give them a little more room.
    summary_turns = 40
