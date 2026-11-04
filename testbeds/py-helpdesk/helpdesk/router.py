"""Intent router that sends tickets to the right queue."""

from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline

ROUTER_REPO = "example-org/helpdesk-intent-router"
ROUTER_REVISION = "9c2e4b7a1f3d5e6c8b0a2d4f6e8c0b1a3d5f7e9c"

# Pinned to a reviewed commit; the model ships custom pooling code.
tokenizer = AutoTokenizer.from_pretrained(
    ROUTER_REPO, revision=ROUTER_REVISION, trust_remote_code=True
)
model = AutoModelForSequenceClassification.from_pretrained(
    ROUTER_REPO, revision=ROUTER_REVISION, trust_remote_code=True
)


# Load options per A/B arm, so the experiment config can change without touching the loader.
EXPERIMENT_ARMS = {
    "control": {"model": ROUTER_REPO, "revision": ROUTER_REVISION, "trust_remote_code": True},
    # Tracks the team's dev branch.
    "candidate": {
        "model": "example-org/helpdesk-intent-router-exp",
        "revision": "dev",
        "trust_remote_code": True,
    },
}


def load_experimental_router(arm: str = "candidate"):
    return pipeline("text-classification", **EXPERIMENT_ARMS[arm])


def load_language_detector():
    return pipeline("text-classification", model="example-org/lang-detect")
