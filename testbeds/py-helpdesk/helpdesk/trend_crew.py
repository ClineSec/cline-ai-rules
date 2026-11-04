"""Weekly ticket-trend digest: a CrewAI crew that reads the week's closed tickets."""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.tools import tool

QUEUE_NAMES = ("hardware", "access", "network", "software")

# The deep-dive agent re-reads every ticket in a queue, and big queues kept hitting the
# default cap of 25 before it finished, so the cap was raised "for good".
DEEP_DIVE_ITERATIONS = 10_000


@tool("Closed tickets")
def closed_tickets(queue: str) -> str:
    """List the subjects of tickets closed this week in one queue."""
    if queue not in QUEUE_NAMES:
        return f"Unknown queue. Known queues: {', '.join(QUEUE_NAMES)}"
    return f"(subjects of tickets closed this week in {queue})"


@CrewBase
class TrendDigestCrew:
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def trend_researcher(self) -> Agent:
        return Agent(config=self.agents_config["trend_researcher"], tools=[closed_tickets])

    @agent
    def digest_writer(self) -> Agent:
        return Agent(config=self.agents_config["digest_writer"])

    @agent
    def queue_deep_dive(self) -> Agent:
        return Agent(
            role="Queue deep-dive analyst",
            goal="Explain why one queue's volume moved this week",
            backstory="You read every ticket in the queue before drawing a conclusion.",
            tools=[closed_tickets],
            max_iter=DEEP_DIVE_ITERATIONS,
        )

    @agent
    def escalation_reviewer(self) -> Agent:
        return Agent(
            role="Escalation reviewer",
            goal="Check that every escalated ticket got a reply within the SLA",
            backstory="You are careful and quick.",
            tools=[closed_tickets],
            # Raised from 25 for the end-of-quarter backlog, with a time limit as the backstop.
            max_iter=2_000,
            max_execution_time=900,
        )

    @agent
    def headline_editor(self) -> Agent:
        return Agent(
            role="Headline editor",
            goal="Write a one-line headline for the digest",
            backstory="You keep it short.",
            max_iter=40,
        )

    @task
    def research_task(self) -> Task:
        return Task(config=self.tasks_config["research_task"])

    @task
    def digest_task(self) -> Task:
        return Task(config=self.tasks_config["digest_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential)
