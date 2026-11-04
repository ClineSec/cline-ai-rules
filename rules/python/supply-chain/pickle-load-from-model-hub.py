import io
import json
import os
import pickle
import urllib.request
from pathlib import Path

import cloudpickle
import dill
import httpx
import joblib
import pandas as pd
import requests
import torch
from fastai.learner import load_learner
from huggingface_hub import HfApi, hf_hub_download, snapshot_download

REPO = "example-org/ticket-triage"
MODEL_SHA = "4b9e1c7a2d3f5e6a8c0b1d2e3f4a5b6c7d8e9f0a"
MODEL_URL = "https://models.example.com/helpdesk/reranker.pkl"


def load_encoder(name):
    path = hf_hub_download(REPO, name)
    with open(path, "rb") as fh:
        # ruleid: pickle-load-from-model-hub
        return pickle.load(fh)


def load_frame():
    local_dir = snapshot_download(REPO, allow_patterns=["*.pkl"])
    # ruleid: pickle-load-from-model-hub
    return pd.read_pickle(os.path.join(local_dir, "features.pkl"))


def load_via_api(name):
    api = HfApi()
    # ruleid: pickle-load-from-model-hub
    return dill.loads(open(api.hf_hub_download(REPO, name), "rb").read())


def load_tokenizer_state(name):
    with open(hf_hub_download(REPO, name), "rb") as fh:
        # ruleid: pickle-load-from-model-hub
        return pickle.Unpickler(fh).load()


def load_with_config(name):
    snapshot = Path(hf_hub_download(REPO, name))
    config = json.loads(Path(hf_hub_download(REPO, "config.json")).read_text())
    with snapshot.open("rb") as fh:
        # ruleid: pickle-load-from-model-hub
        return pickle.load(fh), config


def load_learner_from_hub(name):
    # ruleid: pickle-load-from-model-hub
    return load_learner(hf_hub_download(REPO, name))


# --- Plain URL downloads ---------------------------------------------------------------


def load_reranker(cache_dir):
    dst = os.path.join(cache_dir, "reranker.pkl")
    if not os.path.exists(dst):
        torch.hub.download_url_to_file(MODEL_URL, dst)
    # ruleid: pickle-load-from-model-hub
    return joblib.load(dst)


def load_retrieved():
    path, _headers = urllib.request.urlretrieve(MODEL_URL)
    # ruleid: pickle-load-from-model-hub
    return joblib.load(path)


def load_stream():
    # ruleid: pickle-load-from-model-hub
    return pickle.load(urllib.request.urlopen(MODEL_URL))


def load_bytes():
    resp = requests.get(MODEL_URL, timeout=30)
    resp.raise_for_status()
    # ruleid: pickle-load-from-model-hub
    return cloudpickle.loads(resp.content)


def load_buffer():
    # ruleid: pickle-load-from-model-hub
    return joblib.load(io.BytesIO(httpx.get(MODEL_URL).content))


# --- Near misses -----------------------------------------------------------------------


def load_pinned(name):
    path = hf_hub_download(REPO, name, revision=MODEL_SHA)
    # ok: pickle-load-from-model-hub
    return joblib.load(path)


def load_named_pickle():
    # unsafe-model-deserialization reports this on the download line; no second finding.
    path = hf_hub_download(REPO, "triage.joblib")
    # ok: pickle-load-from-model-hub
    return joblib.load(path)


def load_named_fstring(name):
    path = hf_hub_download(REPO, filename=f"models/{name}.joblib")
    # ok: pickle-load-from-model-hub
    return joblib.load(path)


def load_label_map(name):
    path = hf_hub_download(REPO, name)
    # ok: pickle-load-from-model-hub
    return json.load(open(path))


def load_manifest_model():
    # The release manifest names a model already on local disk; only the name is remote.
    manifest = requests.get("https://models.example.com/helpdesk/manifest.json").json()
    # ok: pickle-load-from-model-hub
    return joblib.load(os.path.join("/srv/helpdesk/models", manifest["model_file"]))


def load_local_pickle():
    # ok: pickle-load-from-model-hub
    return joblib.load("/srv/helpdesk/models/triage.joblib")


def load_weights(name):
    # torch.load is weights-only by default; opt-outs are unsafe-model-deserialization's.
    # ok: pickle-load-from-model-hub
    return torch.load(hf_hub_download(REPO, name), map_location="cpu")
