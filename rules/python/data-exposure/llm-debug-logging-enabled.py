import json
import logging
import os
import subprocess
import sys

import langchain
import litellm
from anthropic import Anthropic
from langchain_core.globals import set_debug, set_verbose
from langchain_core.tracers import ConsoleCallbackHandler
from langchain_core.tracers.stdout import ConsoleCallbackHandler as StdoutTracer
from langchain.agents import AgentExecutor, create_agent, initialize_agent
from langchain.chains import ConversationChain, LLMChain
from langchain.chains.question_answering import load_qa_chain
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from openai import AsyncOpenAI, OpenAI

from app.config import settings

logger = logging.getLogger(__name__)
client = OpenAI()
aclient = AsyncOpenAI()
claude = Anthropic()

LANGCHAIN_DEBUG = True

# ruleid: llm-debug-logging-enabled
set_debug(True)

# ruleid: llm-debug-logging-enabled
set_debug(LANGCHAIN_DEBUG)

# ruleid: llm-debug-logging-enabled
langchain.debug = True

# ok: llm-debug-logging-enabled
set_debug(False)

# ok: llm-debug-logging-enabled
set_debug(settings.langchain_debug)

# Every legacy chain and agent defaults to the global verbose.
# ruleid: llm-debug-logging-enabled
set_verbose(True)

# ok: llm-debug-logging-enabled
set_verbose(False)

if settings.debug:
    # ok: llm-debug-logging-enabled
    set_debug(True)

if os.getenv("APP_ENV") == "development":
    # ok: llm-debug-logging-enabled
    litellm.set_verbose = True


def enable_debug_tracing():
    # ok: llm-debug-logging-enabled
    set_debug(True)


TRACE_CONFIG = {
    # ruleid: llm-debug-logging-enabled
    "callbacks": [ConsoleCallbackHandler()],
    "tags": ["report"],
}


def summarize(chain, rows):
    # ruleid: llm-debug-logging-enabled
    return chain.invoke({"rows": rows}, config={"callbacks": [StdoutTracer()]})


# ruleid: llm-debug-logging-enabled
litellm.set_verbose = True

# ok: llm-debug-logging-enabled
litellm.set_verbose = False

# ruleid: llm-debug-logging-enabled
litellm._turn_on_debug()

# ok: llm-debug-logging-enabled
litellm.suppress_debug_info = True


def ask_gateway(messages):
    return litellm.completion(
        model="gpt-4.1-mini",
        messages=messages,
        # ruleid: llm-debug-logging-enabled
        litellm_request_debug=True,
    )


def start_gateway(config_path):
    return subprocess.Popen(
        # ruleid: llm-debug-logging-enabled
        [sys.executable, "-m", "litellm", "--config", config_path, "--port", "4000", "--detailed_debug"],
    )


def start_gateway_quietly(config_path):
    # ok: llm-debug-logging-enabled
    return subprocess.Popen([sys.executable, "-m", "litellm", "--config", config_path, "--port", "4000"])


# ruleid: llm-debug-logging-enabled
os.environ["LITELLM_LOG"] = "DEBUG"

# ok: llm-debug-logging-enabled
os.environ["LITELLM_LOG"] = "INFO"

# ruleid: llm-debug-logging-enabled
os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true")

# ruleid: llm-debug-logging-enabled
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "SPAN_AND_EVENT"

# ok: llm-debug-logging-enabled
os.environ["OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT"] = "false"

# ok: llm-debug-logging-enabled
os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "NO_CONTENT")

# ruleid: llm-debug-logging-enabled
os.environ["OPENAI_AGENTS_DONT_LOG_MODEL_DATA"] = "0"

# ok: llm-debug-logging-enabled
os.environ["OPENAI_AGENTS_DONT_LOG_MODEL_DATA"] = "1"

# The default is already on, so setting it is not a switch.
# ok: llm-debug-logging-enabled
os.environ["OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA"] = "true"

TRACING_DEFAULTS = {
    "OTEL_SERVICE_NAME": "fixture-app",
    # ruleid: llm-debug-logging-enabled
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "event_only",
    # ok: llm-debug-logging-enabled
    "OPENAI_AGENTS_DONT_LOG_TOOL_DATA": "1",
}


def apply_tracing_defaults():
    for key, value in TRACING_DEFAULTS.items():
        os.environ.setdefault(key, value)


def run_gateway_worker(args):
    # ruleid: llm-debug-logging-enabled
    return subprocess.run(args, env={**os.environ, "LITELLM_LOG": "DEBUG"}, check=True)


# ruleid: llm-debug-logging-enabled
os.environ.update({"OPENAI_AGENTS_DONT_LOG_MODEL_DATA": "false"})


def build_graph(builder: StateGraph):
    # ruleid: llm-debug-logging-enabled
    return builder.compile(debug=True)


def build_graph_quiet(builder: StateGraph):
    # ok: llm-debug-logging-enabled
    return builder.compile(debug=False)


# ruleid: llm-debug-logging-enabled
agent = create_react_agent("openai:gpt-4.1-mini", tools=[], debug=True)

# ruleid: llm-debug-logging-enabled
triage = create_agent("openai:gpt-4.1-mini", tools=[], debug=True)

# ok: llm-debug-logging-enabled
quiet_agent = create_react_agent("openai:gpt-4.1-mini", tools=[], debug=settings.debug)


def run_graph(graph, state):
    # ruleid: llm-debug-logging-enabled
    return graph.invoke(state, debug=True)


def answer(messages):
    # ruleid: llm-debug-logging-enabled
    logger.info("chat request: %s", messages)
    response = client.chat.completions.create(model="gpt-4.1-mini", messages=messages)
    return response.choices[0].message.content


async def answer_async(history):
    reply = await aclient.chat.completions.create(model="gpt-4.1-mini", messages=history)
    # ruleid: llm-debug-logging-enabled
    logger.warning(f"model call failed for conversation {json.dumps(history)}")
    return reply


def answer_claude(convo):
    # ruleid: llm-debug-logging-enabled
    logging.info(convo)
    return claude.messages.create(model="claude-sonnet-4-5", max_tokens=1024, messages=convo)


def answer_counted(messages):
    # ok: llm-debug-logging-enabled
    logger.info("chat request with %d messages", len(messages))
    # Debug-level logs are off in production.
    # ok: llm-debug-logging-enabled
    logger.debug("chat request: %s", messages)
    return client.chat.completions.create(model="gpt-4.1-mini", messages=messages)


def log_only(messages):
    # Not sent to a model in this function.
    # ok: llm-debug-logging-enabled
    logger.info("stored transcript: %s", messages)


def start_gateway_shell(config_path):
    # ruleid: llm-debug-logging-enabled
    return subprocess.run(f"litellm --config {config_path} --detailed_debug", shell=True, check=True)


def gateway_help():
    # ok: llm-debug-logging-enabled
    print("Restart the gateway with --detailed_debug to see raw requests.")


GATEWAY_CMD = "litellm --config /etc/litellm/config.yaml --port 4000"


def start_gateway_with_raw_requests():
    # ruleid: llm-debug-logging-enabled
    return subprocess.run("litellm --config /etc/litellm/config.yaml --detailed_debug", shell=True, check=True)


def start_gateway_plain_shell():
    # ok: llm-debug-logging-enabled
    return subprocess.run(GATEWAY_CMD, shell=True, check=True)


CHAIN_VERBOSE = True
chat_model = ChatOpenAI(model="gpt-4.1-mini")

# ruleid: llm-debug-logging-enabled
qa_chain = LLMChain(llm=chat_model, prompt=QA_PROMPT, verbose=True)

support_chain = ConversationChain(
    llm=chat_model,
    # ruleid: llm-debug-logging-enabled
    verbose=CHAIN_VERBOSE,
)

# ok: llm-debug-logging-enabled
quiet_chain = LLMChain(llm=chat_model, prompt=QA_PROMPT, verbose=False)

# A chat model's own verbose prints nothing for model calls.
# ok: llm-debug-logging-enabled
loud_model = ChatOpenAI(model="gpt-4.1-mini", verbose=True)

# ok: llm-debug-logging-enabled
env_chain = LLMChain(llm=chat_model, prompt=QA_PROMPT, verbose=settings.debug)

EXECUTOR_OPTIONS = {
    "max_iterations": 6,
    # ruleid: llm-debug-logging-enabled
    "verbose": True,
}


def build_executor(agent, tools):
    return AgentExecutor(agent=agent, tools=tools, **EXECUTOR_OPTIONS)


# ruleid: llm-debug-logging-enabled
legacy_agent = initialize_agent([], chat_model, agent="zero-shot-react-description", verbose=True)

# ruleid: llm-debug-logging-enabled
doc_chain = load_qa_chain(chat_model, chain_type="stuff", verbose=True)

# ok: llm-debug-logging-enabled
executor = AgentExecutor.from_agent_and_tools(agent=legacy_agent.agent, tools=[], verbose=False)
