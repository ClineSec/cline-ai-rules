# No LangGraph or mem0 import here: the store and the memory client come from the app's own
# modules, so only their names and call shapes say what they are.
import requests

from .clients import memory, notes, store


def save_page(url: str, user_id: str, namespace: tuple):
    page = requests.get(url).text
    # ruleid: agent-memory-write-untrusted
    memory.add(page, user_id=user_id)
    # A tuple namespace is LangGraph's shape.
    # ruleid: agent-memory-write-untrusted
    store.put(("pages", user_id), url, {"text": page})
    # A store of another kind, without LangGraph in the file.
    # ok: agent-memory-write-untrusted
    store.put(namespace, url, {"text": page})
    # No mem0 scope ids: some other add().
    # ok: agent-memory-write-untrusted
    memory.add(page)
    # ok: agent-memory-write-untrusted
    notes.add(page, user_id=user_id)
