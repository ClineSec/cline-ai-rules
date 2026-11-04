"""LangChain version of the warehouse questions, used by the Slack bot.

A prompt | model | parser chain writes the SQL from the table info LangChain reads out of the
warehouse, and SQLDatabase runs it.
"""

from langchain_community.utilities import SQLDatabase
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from .llm import PLANNER_MODEL

WAREHOUSE_URI = "sqlite:///file:/srv/helpdesk/warehouse.sqlite?mode=ro&uri=true"

warehouse = SQLDatabase.from_uri(WAREHOUSE_URI, include_tables=["tickets", "queues"], sample_rows_in_table_info=0)

write_sql = (
    ChatPromptTemplate.from_messages(
        [
            ("system", "Write one SQLite SELECT statement for these tables:\n{schema}\nReply with SQL only."),
            ("human", "{question}"),
        ]
    )
    | ChatOpenAI(model=PLANNER_MODEL, temperature=0)
    | StrOutputParser()
)

pick_team = (
    ChatPromptTemplate.from_messages(
        [("system", "Reply with the team name the question is about, nothing else."), ("human", "{question}")]
    )
    | ChatOpenAI(model=PLANNER_MODEL, temperature=0)
    | StrOutputParser()
)


@tool
def warehouse_question(question: str) -> str:
    """Answer a question about ticket volumes, queues, and response times."""
    query = write_sql.invoke({"question": question, "schema": warehouse.get_table_info()})
    return warehouse.run(query, include_columns=True)


@tool
def team_queues(question: str) -> str:
    """List the queues that belong to the team the question is about."""
    team = pick_team.invoke({"question": question}).strip()
    return warehouse.run("SELECT name FROM queues WHERE team = :team", parameters={"team": team})
