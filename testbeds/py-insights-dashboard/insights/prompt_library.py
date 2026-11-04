"""Prompt library: analysts share the LangChain prompts behind their dashboard questions.

The prompt lab exports a prompt as LangChain JSON (`dumps(prompt)`). Another analyst pastes
that export into the library form, or uploads the file, and it is saved under a name everyone
can schedule. The blueprint is mounted next to the share-link app.
"""

from flask import Blueprint, jsonify, request
from langchain_core.load import loads

from insights.prompt_store import save_prompt

bp = Blueprint("prompt_library", __name__, url_prefix="/prompts")


def _revive(manifest: str):
    """Rebuild a shared prompt. Core classes only, and no keys from the environment."""
    return loads(manifest, allowed_objects="core", secrets_from_env=False)


@bp.post("/import")
def import_prompt():
    name = request.form["name"]
    prompt = _revive(request.form["manifest"])
    save_prompt(name, prompt)
    return jsonify(name=name, variables=prompt.input_variables)


@bp.post("/upload")
def upload_prompt():
    upload = request.files["prompt"]
    shared = upload.read().decode("utf-8")
    prompt = loads(shared)
    save_prompt(upload.filename.removesuffix(".json"), prompt)
    return jsonify(name=upload.filename, variables=prompt.input_variables)


@bp.post("/conversation")
def import_conversation():
    """A chat transcript exported from the assistant, so a teammate can pick it up."""
    history = loads(
        request.get_data(as_text=True), allowed_objects="messages", secrets_from_env=False
    )
    return jsonify(turns=len(history))
