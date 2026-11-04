import json
import sqlite3

import anthropic
import asyncpg
import litellm
import pandas as pd
import psycopg
import sqlalchemy as sa
from langchain_community.utilities import SQLDatabase
from openai import OpenAI
from psycopg import sql
from sqlalchemy import select, text

openai_client = OpenAI()
claude = anthropic.Anthropic()
conn = sqlite3.connect("reports.db")
engine = sa.create_engine("sqlite:///reports.db")

ALLOWED_TABLES = {"tickets", "queues"}
SORT_COLUMNS = {"newest": "created_at DESC", "oldest": "created_at ASC"}


def answer_with_sql(question):
    resp = openai_client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    query = resp.choices[0].message.content
    # ruleid: llm-output-to-sql
    return conn.execute(query).fetchall()


def answer_with_cursor(question):
    msg = claude.messages.create(
        model="claude-sonnet-5-5", max_tokens=512, messages=[{"role": "user", "content": question}]
    )
    cur = conn.cursor()
    # ruleid: llm-output-to-sql
    cur.executescript(msg.content[0].text)


def filter_by_model_column(question):
    out = litellm.completion(model="gpt-5", messages=[{"role": "user", "content": question}])
    column = out.choices[0].message.content.strip()
    # ruleid: llm-output-to-sql
    return conn.execute(f"SELECT id, {column} FROM tickets LIMIT 20").fetchall()


def sqlalchemy_text(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    with engine.connect() as c:
        # ruleid: llm-output-to-sql
        return c.execute(text(resp.output_text)).all()


def sqlalchemy_driver_sql(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    with engine.connect() as c:
        # ruleid: llm-output-to-sql
        return c.exec_driver_sql(resp.output_text).all()


def pandas_report(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    # ruleid: llm-output-to-sql
    return pd.read_sql_query(resp.output_text, engine)


def pandas_report_keyword(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    # ruleid: llm-output-to-sql
    return pd.read_sql(con=engine, sql=resp.output_text)


def langchain_chain(chain, question):
    db = SQLDatabase.from_uri("sqlite:///reports.db")
    generated = chain.invoke({"question": question})
    # ruleid: llm-output-to-sql
    return db.run(generated)


def langchain_no_throw(llm, db, question):
    generated = llm.invoke(question).content
    # ruleid: llm-output-to-sql
    return db.run_no_throw(generated)


async def asyncpg_fetch(pg, question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    # ruleid: llm-output-to-sql
    return await pg.fetch(resp.output_text)


def psycopg_composed(pgconn, question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    # ruleid: llm-output-to-sql
    query = sql.SQL(resp.output_text)
    return pgconn.execute(query).fetchall()


def structured_where_clause(question):
    resp = openai_client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": question}],
        response_format={"type": "json_object"},
    )
    plan = json.loads(resp.choices[0].message.content)
    # ruleid: llm-output-to-sql
    return conn.execute("SELECT id FROM tickets WHERE " + plan["where"]).fetchall()


# --- near misses ---------------------------------------------------------------------


def bound_parameter(question):
    resp = openai_client.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": question}],
        response_format={"type": "json_object"},
    )
    args = json.loads(resp.choices[0].message.content)
    # ok: llm-output-to-sql
    return conn.execute("SELECT id, title FROM tickets WHERE queue = ?", (args["queue"],)).fetchall()


def sqlalchemy_bindparams(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    stmt = text("SELECT id FROM tickets WHERE title LIKE :q").bindparams(q=f"%{resp.output_text}%")
    with engine.connect() as c:
        # ok: llm-output-to-sql
        return c.execute(stmt).all()


def sqlalchemy_core_select(tickets, question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    stmt = select(tickets.c.id).where(tickets.c.queue == resp.output_text.strip()).limit(20)
    with engine.connect() as c:
        # ok: llm-output-to-sql
        return c.execute(stmt).all()


def allowlisted_sort(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    order = SORT_COLUMNS.get(resp.output_text.strip(), "created_at DESC")
    # ok: llm-output-to-sql
    return conn.execute(f"SELECT id FROM tickets ORDER BY {order} LIMIT 20").fetchall()


def checked_table(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    table = resp.output_text.strip()
    if table not in ALLOWED_TABLES:
        raise ValueError(table)
    # ok: llm-output-to-sql
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()


def identifier_quoted(pgconn, question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    # ok: llm-output-to-sql
    query = sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(resp.output_text.strip()))
    return pgconn.execute(query).fetchone()


def numeric_limit(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    # ok: llm-output-to-sql
    return conn.execute(f"SELECT id FROM tickets LIMIT {int(resp.output_text)}").fetchall()


def log_usage(question):
    resp = openai_client.chat.completions.create(
        model="gpt-5", messages=[{"role": "user", "content": question}]
    )
    # ok: llm-output-to-sql
    conn.execute(f"UPDATE usage SET tokens = tokens + {resp.usage.total_tokens}")


def store_answer(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    # ok: llm-output-to-sql
    conn.executemany("INSERT INTO answers (question, answer) VALUES (?, ?)", [(question, resp.output_text)])


def pandas_params(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    # ok: llm-output-to-sql
    return pd.read_sql_query("SELECT id FROM tickets WHERE queue = ?", conn, params=[resp.output_text])


def html_escape_is_not_sql_quoting(question):
    import html
    resp = openai_client.responses.create(model="gpt-5", input=question)
    # ruleid: llm-output-to-sql
    return conn.execute(f"SELECT id FROM tickets WHERE title = '{html.escape(resp.output_text)}'")


def _run_report(query, params=()):
    with sqlite3.connect("reports.db") as db:
        return db.execute(query, params).fetchall()


def tickets_by_model_sort(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    order = resp.output_text.strip()
    # ruleid: llm-output-to-sql
    return _run_report(f"SELECT id, status FROM tickets ORDER BY {order} LIMIT 50")


def tickets_by_named_sort(question):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    order = SORT_COLUMNS.get(resp.output_text.strip(), SORT_COLUMNS["newest"])
    # ok: llm-output-to-sql
    return _run_report(f"SELECT id, status FROM tickets ORDER BY {order} LIMIT 50")


def log_model_sort(question, logger):
    resp = openai_client.responses.create(model="gpt-5", input=question)
    # ok: llm-output-to-sql
    logger.info(f"SELECT for report ordered by {resp.output_text} FROM the cache")


def answer_from_claude_stream(question):
    with claude.messages.stream(
        model="claude-sonnet-5-5", max_tokens=512, messages=[{"role": "user", "content": question}]
    ) as stream:
        query = stream.get_final_text()
    # ruleid: llm-output-to-sql
    return conn.execute(query).fetchall()


def answer_from_gemini_chat(gemini, question):
    chat = gemini.chats.create(model="gemini-3-pro")
    reply = chat.send_message(question)
    # ruleid: llm-output-to-sql
    return conn.execute(reply.text).fetchall()
