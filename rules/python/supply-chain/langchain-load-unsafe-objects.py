import json
import os

import langchain_core.load as lc_load
from langchain import hub
from langchain_classic.load.load import Reviver as ClassicReviver
from langchain_core.load import load, loads
from langchain_core.load.load import Reviver
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

client = Client()


def restore_chain(text):
    # ruleid: langchain-load-unsafe-objects
    return loads(text, allowed_objects="all")


def restore_with_keys(manifest):
    # ruleid: langchain-load-unsafe-objects
    return load(manifest, secrets_from_env=True)


def restore_jinja_prompt(manifest):
    # ruleid: langchain-load-unsafe-objects
    return load(manifest, allowed_objects=[ChatPromptTemplate], init_validator=None)


def restore_with_env_map(text):
    # ruleid: langchain-load-unsafe-objects
    return lc_load.loads(text, secrets_map=dict(os.environ))


def restore_with_env_copy(text):
    # ruleid: langchain-load-unsafe-objects
    return loads(text, secrets_map=os.environ.copy())


def restore_with_env_overrides(text):
    # ruleid: langchain-load-unsafe-objects
    return loads(text, secrets_map={**os.environ, "OPENAI_API_KEY": "sk-test-invalid"})


def restore_with_object_hook(text):
    # ruleid: langchain-load-unsafe-objects
    return json.loads(text, object_hook=Reviver("all"))


def restore_classic(text):
    # ruleid: langchain-load-unsafe-objects
    return json.loads(text, object_hook=ClassicReviver(secrets_from_env=True))


def restore_positional(text):
    # ruleid: langchain-load-unsafe-objects
    return json.loads(text, object_hook=Reviver("core", None, None, True))


ALL_PARTNERS = "all"


def restore_from_constant(text):
    # ruleid: langchain-load-unsafe-objects
    return loads(text, allowed_objects=ALL_PARTNERS)


# ruleid: langchain-load-unsafe-objects
RESTORE_OPTIONS = {"allowed_objects": "core", "secrets_from_env": True}


def restore_with_options(text):
    return loads(text, **RESTORE_OPTIONS)


def pull_digest_prompt():
    # ruleid: langchain-load-unsafe-objects
    return client.pull_prompt("growth-team/weekly-digest", include_model=True)


def pull_digest_prompt_with_keys():
    # ruleid: langchain-load-unsafe-objects
    return client.pull_prompt("growth-team/weekly-digest:9f2c4e1a", secrets_from_env=True)


def pull_from_hub():
    # ruleid: langchain-load-unsafe-objects
    return hub.pull("growth-team/kpi-explainer", include_model=True)


# --- near misses --------------------------------------------------------------------------


def restore_defaults(text):
    # ok: langchain-load-unsafe-objects
    return loads(text)


def restore_core(text):
    # ok: langchain-load-unsafe-objects
    return loads(text, allowed_objects="core", secrets_from_env=False)


def restore_messages(text):
    # ok: langchain-load-unsafe-objects
    return loads(text, allowed_objects="messages")


def restore_listed(manifest):
    # ok: langchain-load-unsafe-objects
    return load(manifest, allowed_objects=[AIMessage, HumanMessage, ChatPromptTemplate])


def restore_with_one_key(text):
    # ok: langchain-load-unsafe-objects
    return loads(text, secrets_map={"OPENAI_API_KEY": os.environ["OPENAI_API_KEY"]})


def pull_pinned_prompt():
    # ok: langchain-load-unsafe-objects
    return client.pull_prompt("growth-team/weekly-digest:9f2c4e1a", include_model=True)


def pull_prompt_only():
    # ok: langchain-load-unsafe-objects
    return client.pull_prompt("growth-team/weekly-digest")


def pull_pinned_from_hub():
    # ok: langchain-load-unsafe-objects
    return hub.pull("growth-team/kpi-explainer:0b7d3e5f", include_model=True)


def parse_settings(text):
    # A different loader with a keyword of the same name.
    # ok: langchain-load-unsafe-objects
    return json.loads(text, object_hook=dict)
