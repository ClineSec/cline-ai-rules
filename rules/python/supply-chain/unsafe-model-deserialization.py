import functools
import os
import pickle

import dill
import joblib
import keras
import lightning as L
import numpy as np
import pandas as pd
import skops.io as sio
import tensorflow as tf
import torch
import huggingface_hub
from fastai.learner import load_learner
from huggingface_hub import from_pretrained_fastai, hf_hub_download
from keras.saving import load_model
from langchain_community.vectorstores import FAISS
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from torch import load as torch_load
from torch.utils.model_zoo import load_url

# --- PyTorch ---------------------------------------------------------------------------

# ruleid: unsafe-model-deserialization
ckpt = torch.load("checkpoints/classifier.pt", weights_only=False)

# ruleid: unsafe-model-deserialization
aliased = torch_load("checkpoints/classifier.pt", map_location="cpu", weights_only=False)

# ruleid: unsafe-model-deserialization
with_dill = torch.load("checkpoints/classifier.pt", map_location="cpu", pickle_module=dill)

# ruleid: unsafe-model-deserialization
positional_module = torch.load("checkpoints/classifier.pt", "cpu", pickle)

# ruleid: unsafe-model-deserialization
remote = torch.hub.load_state_dict_from_url("https://example.com/weights/resnet.pth")

# ruleid: unsafe-model-deserialization
zoo = load_url("https://example.com/weights/resnet.pth", map_location="cpu")

# ruleid: unsafe-model-deserialization
lit = TriageModel.load_from_checkpoint("checkpoints/last.ckpt", weights_only=False)

# ruleid: unsafe-model-deserialization
lit_remote = TriageModel.load_from_checkpoint("https://example.com/ckpt/last.ckpt")

# ruleid: unsafe-model-deserialization
trainer.fit(model, datamodule=dm, ckpt_path="https://example.com/ckpt/last.ckpt")

# ruleid: unsafe-model-deserialization
os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"

# ruleid: unsafe-model-deserialization
os.environ.setdefault("TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD", "true")

# ruleid: unsafe-model-deserialization
os.environ.update(TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD="YES")

# ruleid: unsafe-model-deserialization
torch.multiprocessing.spawn(worker, args=({"TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD": "1"},))

# ruleid: unsafe-model-deserialization
lazy_load = functools.partial(torch.load, map_location="cpu", weights_only=False)

fabric = L.Fabric(accelerator="cpu")
# ruleid: unsafe-model-deserialization
state = fabric.load("https://example.com/ckpt/fabric.ckpt")
# ok: unsafe-model-deserialization
local_state = fabric.load("checkpoints/fabric.ckpt")

# ok: unsafe-model-deserialization
safe_default = torch.load("checkpoints/classifier.pt", map_location="cpu")

# ok: unsafe-model-deserialization
explicit_safe = torch.load("checkpoints/classifier.pt", weights_only=True)

# ok: unsafe-model-deserialization
remote_safe = torch.hub.load_state_dict_from_url("https://example.com/w.pth", weights_only=True)


def fetch_weights(url, trusted_source):
    # ok: unsafe-model-deserialization
    return torch.hub.load_state_dict_from_url(url, weights_only=not trusted_source)

# ok: unsafe-model-deserialization
lit_local = TriageModel.load_from_checkpoint("checkpoints/last.ckpt")

# ok: unsafe-model-deserialization
lit_remote_safe = TriageModel.load_from_checkpoint("https://example.com/c.ckpt", weights_only=True)

# Saving with weights_only=False means "save the full trainer state", not unpickling.
# ok: unsafe-model-deserialization
trainer.save_checkpoint("checkpoints/last.ckpt", weights_only=False)

# ok: unsafe-model-deserialization
torch.save(model.state_dict(), "checkpoints/classifier.pt")

# ok: unsafe-model-deserialization
os.environ["TORCH_FORCE_WEIGHTS_ONLY_LOAD"] = "1"

# ok: unsafe-model-deserialization
os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "0"

# --- NumPy -----------------------------------------------------------------------------

# ruleid: unsafe-model-deserialization
labels = np.load("artifacts/labels.npy", allow_pickle=True)

# ruleid: unsafe-model-deserialization
positional = np.load("artifacts/labels.npy", None, True)

# ok: unsafe-model-deserialization
vectors = np.load("artifacts/vectors.npy")

# ok: unsafe-model-deserialization
vectors_explicit = np.load("artifacts/vectors.npy", allow_pickle=False)

# Writing an object array with pickle is not the risk; reading it back is.
# ok: unsafe-model-deserialization
np.save("artifacts/labels.npy", labels, allow_pickle=True)

# ok: unsafe-model-deserialization
np.savez_compressed("artifacts/bundle.npz", labels=labels, allow_pickle=True)

# --- LangChain -------------------------------------------------------------------------

# ruleid: unsafe-model-deserialization
index = FAISS.load_local("indexes/kb", embeddings, allow_dangerous_deserialization=True)

# ruleid: unsafe-model-deserialization
from_bytes = FAISS.deserialize_from_bytes(blob, embeddings, allow_dangerous_deserialization=True)

# ok: unsafe-model-deserialization
refused = FAISS.load_local("indexes/kb", embeddings, allow_dangerous_deserialization=False)

# ok: unsafe-model-deserialization
fresh = FAISS.from_texts(["reset a password"], embeddings)

# --- LangGraph -------------------------------------------------------------------------

# ruleid: unsafe-model-deserialization
serde = JsonPlusSerializer(pickle_fallback=True)

# ruleid: unsafe-model-deserialization
legacy = JsonPlusSerializer(allowed_json_modules=True)

# ruleid: unsafe-model-deserialization
permissive = JsonPlusSerializer(allowed_msgpack_modules=True)

# ok: unsafe-model-deserialization
strict = JsonPlusSerializer()

# ok: unsafe-model-deserialization
listed = JsonPlusSerializer(allowed_msgpack_modules=[("helpdesk.models", "Ticket")])

# --- Keras -----------------------------------------------------------------------------

# ruleid: unsafe-model-deserialization
k3 = keras.saving.load_model("models/router.keras", safe_mode=False)

# ruleid: unsafe-model-deserialization
k3_imported = load_model("models/router.keras", compile=False, safe_mode=False)

# ruleid: unsafe-model-deserialization
tfk = tf.keras.models.load_model("models/router.keras", safe_mode=False)

# ruleid: unsafe-model-deserialization
k3_positional = keras.models.load_model("models/router.keras", None, True, False)

# ruleid: unsafe-model-deserialization
layer = keras.layers.Lambda.from_config(layer_config, safe_mode=False)

# ruleid: unsafe-model-deserialization
with keras.saving.serialization_lib.SafeModeScope(False):
    restored = keras.saving.deserialize_keras_object(layer_config)

# ruleid: unsafe-model-deserialization
keras.config.enable_unsafe_deserialization()

# ok: unsafe-model-deserialization
k3_safe = keras.saving.load_model("models/router.keras")

# ok: unsafe-model-deserialization
k3_explicit = keras.saving.load_model("models/router.keras", safe_mode=True)

# safe_mode is a common keyword name; only Keras loaders count.
# ok: unsafe-model-deserialization
renderer = MarkdownRenderer(safe_mode=False)

# ok: unsafe-model-deserialization
UI_FLAGS = {"safe_mode": False, "theme": "dark"}

# --- skops -----------------------------------------------------------------------------

# ruleid: unsafe-model-deserialization
pipe = sio.load("models/triage.skops", trusted=sio.get_untrusted_types(file="models/triage.skops"))

unknown = sio.get_untrusted_types(file="models/triage.skops")
# ruleid: unsafe-model-deserialization
pipe2 = sio.load("models/triage.skops", trusted=unknown)

# ok: unsafe-model-deserialization
pipe3 = sio.load("models/triage.skops", trusted=["sklearn.pipeline.Pipeline"])

# ok: unsafe-model-deserialization
pipe4 = sio.load("models/triage.skops")

# --- Pickle files from the Hugging Face Hub ----------------------------------------------

REPO = "example-org/ticket-triage"
MODEL_FILE = "triage.joblib"
MODEL_SHA = "4b9e1c7a2d3f5e6a8c0b1d2e3f4a5b6c7d8e9f0a"

# ruleid: unsafe-model-deserialization
clf = joblib.load(hf_hub_download(REPO, "sklearn_model.joblib"))


def fetch_triage_model():
    # A helper: the path leaves this function, so the pickle filename is the signal.
    # ruleid: unsafe-model-deserialization
    return hf_hub_download(repo_id=REPO, filename=MODEL_FILE)


def load_by_name(name):
    # ruleid: unsafe-model-deserialization
    return joblib.load(hf_hub_download(REPO, filename=f"models/{name}.joblib"))


def load_encoder(name):
    # The filename isn't known here; the taint rule pickle-load-from-model-hub reports
    # this flow at the pickle.load, so this rule stays quiet to avoid a second finding.
    # ok: unsafe-model-deserialization
    path = hf_hub_download(REPO, name)
    with open(path, "rb") as fh:
        return pickle.load(fh)


# ok: unsafe-model-deserialization
pinned = joblib.load(hf_hub_download(REPO, MODEL_FILE, revision=MODEL_SHA))

# ok: unsafe-model-deserialization
config_path = hf_hub_download(REPO, "config.json")

# ok: unsafe-model-deserialization
card_path = hf_hub_download(REPO, filename=f"cards/{REPO}.md")

# ok: unsafe-model-deserialization
weights = torch.load(hf_hub_download(REPO, "pytorch_model.bin"), map_location="cpu")

# A pickle written by this service to its own disk is not flagged.
# ok: unsafe-model-deserialization
local_clf = joblib.load("models/triage.joblib")

# ruleid: unsafe-model-deserialization
remote_frame = pd.read_pickle("https://example.com/exports/tickets.pkl")

# ok: unsafe-model-deserialization
local_frame = pd.read_pickle("exports/tickets.pkl")

# --- fastai ------------------------------------------------------------------------------

# ruleid: unsafe-model-deserialization
tone = from_pretrained_fastai("example-org/ticket-tone")

# ruleid: unsafe-model-deserialization
tone_main = huggingface_hub.from_pretrained_fastai("example-org/ticket-tone", revision="main")

# ok: unsafe-model-deserialization
tone_pinned = from_pretrained_fastai("example-org/ticket-tone", revision=MODEL_SHA)

# ok: unsafe-model-deserialization
tone_suffix = from_pretrained_fastai("example-org/ticket-tone@4b9e1c7a2d3f5e6a8c0b1d2e3f4a5b6c7d8e9f0a")

# A learner exported by this service to its own volume is not flagged.
# ok: unsafe-model-deserialization
tone_local = load_learner("models/ticket-tone.pkl")

# --- Load options in a dict passed as **kwargs ----------------------------------------

# ruleid: unsafe-model-deserialization
TORCH_LOAD_OPTS = {"map_location": "cpu", "weights_only": False}
# ruleid: unsafe-model-deserialization
INDEX_OPTS = {"index_name": "kb", "allow_dangerous_deserialization": True}
# ruleid: unsafe-model-deserialization
NPY_OPTS = dict(mmap_mode="r", allow_pickle=True)
# ok: unsafe-model-deserialization
SAFE_TORCH_OPTS = {"map_location": "cpu", "weights_only": True}

