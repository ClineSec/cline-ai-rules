from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# ruleid: hf-trust-remote-code
model = AutoModelForCausalLM.from_pretrained("acme/chat-model", trust_remote_code=True)

# ruleid: hf-trust-remote-code
tok = AutoTokenizer.from_pretrained("acme/chat-model", revision="main", trust_remote_code=True)

# ruleid: hf-trust-remote-code
gen = pipeline("text-generation", model="acme/chat-model", trust_remote_code=True)

# ruleid: hf-trust-remote-code
ds = load_dataset("acme/eval-set", trust_remote_code=True)

# ok: hf-trust-remote-code
pinned = AutoModelForCausalLM.from_pretrained(
    "acme/chat-model",
    revision="3f1c2a9d0b7e4c5f8a6d2e1b9c0f7a3e5d4b2c1a",
    trust_remote_code=True,
)

# ok: hf-trust-remote-code
native = AutoModelForCausalLM.from_pretrained("acme/chat-model")

# ok: hf-trust-remote-code
explicit_off = AutoTokenizer.from_pretrained("acme/chat-model", trust_remote_code=False)

# ruleid: hf-trust-remote-code
tagged = AutoModelForCausalLM.from_pretrained("acme/chat-model", revision="v1.2", trust_remote_code=True)

ROUTER_REVISION = "9c2e4b7a1f3d5e6c8b0a2d4f6e8c0b1a3d5f7e9c"
ROUTER_BRANCH = "dev"

# ok: hf-trust-remote-code
pinned_by_constant = AutoModelForCausalLM.from_pretrained(
    "acme/chat-model", revision=ROUTER_REVISION, trust_remote_code=True
)

# ruleid: hf-trust-remote-code
branch_by_constant = AutoModelForCausalLM.from_pretrained(
    "acme/chat-model", revision=ROUTER_BRANCH, trust_remote_code=True
)


def load(revision):
    # ok: hf-trust-remote-code
    return AutoModelForCausalLM.from_pretrained("acme/chat-model", revision=revision, trust_remote_code=True)


# Load options kept in a config dict and passed as **kwargs.
# ruleid: hf-trust-remote-code
NIGHTLY = {"model": "example-org/x", "revision": "nightly", "trust_remote_code": True}
# ruleid: hf-trust-remote-code
UNPINNED = {"trust_remote_code": True, "model": "example-org/x"}
# ok: hf-trust-remote-code
PINNED = {"revision": "0123456789abcdef0123456789abcdef01234567", "trust_remote_code": True}
# ok: hf-trust-remote-code
NATIVE = {"model": "example-org/x", "revision": "main", "trust_remote_code": False}
