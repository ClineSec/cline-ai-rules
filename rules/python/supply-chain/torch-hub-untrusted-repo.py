import functools
import os
from functools import partial

import torch
import torch.hub as th
from torch import hub
from torch.hub import load as hub_load

PINNED_SHA = "4b1f9e2c7a3d5e6f8091a2b3c4d5e6f708192a3b"

# --- Trust prompt turned off ------------------------------------------------------------

# ruleid: torch-hub-untrusted-repo
detector = torch.hub.load("example-org/detector", "small", trust_repo=True)

# ruleid: torch-hub-untrusted-repo
tagged = torch.hub.load("example-org/detector:v7.0", "small", trust_repo=True)

# ruleid: torch-hub-untrusted-repo
short_sha = torch.hub.load("example-org/detector:4b1f9e2", "small", trust_repo=True)

# None skips the prompt too (before torch 2.11 it was the default and only warned).
# ruleid: torch-hub-untrusted-repo
legacy = torch.hub.load("example-org/detector:main", "small", trust_repo=None)

# Any value other than False or "check" skips the prompt, so an environment string does too,
# even when it reads "false".
# ruleid: torch-hub-untrusted-repo
from_env = torch.hub.load("example-org/detector", "small", trust_repo=os.getenv("HUB_TRUST"))

# ruleid: torch-hub-untrusted-repo
from_environ = torch.hub.load("example-org/detector", "small", trust_repo=os.environ["HUB_TRUST"])

HUB_TRUST = os.environ.get("HUB_TRUST", "false")


def load_env_constant():
    # ruleid: torch-hub-untrusted-repo
    return torch.hub.load("example-org/detector", "small", trust_repo=HUB_TRUST, pretrained=True)


# ruleid: torch-hub-untrusted-repo
string_flag = torch.hub.load("example-org/detector", "small", trust_repo="false")

# list() and help() import hubconf.py as well.
# ruleid: torch-hub-untrusted-repo
entrypoints = torch.hub.list("example-org/detector", trust_repo=True)

# ruleid: torch-hub-untrusted-repo
doc = torch.hub.help("example-org/detector", "small", trust_repo=True)

# ruleid: torch-hub-untrusted-repo
positional = torch.hub.list("example-org/detector", False, False, True)

# Import aliases.
# ruleid: torch-hub-untrusted-repo
aliased = th.load("example-org/detector", "small", trust_repo=True)

# ruleid: torch-hub-untrusted-repo
from_module = hub.load("example-org/detector", "small", trust_repo=True)

# ruleid: torch-hub-untrusted-repo
bare = hub_load("example-org/detector", "small", trust_repo=True)

# Keyword repo argument.
# ruleid: torch-hub-untrusted-repo
by_keyword = torch.hub.load(repo_or_dir="example-org/detector", model="small", trust_repo=True)

DETECTOR_REPO = "example-org/detector:main"
TRUST_HUB = True

# ruleid: torch-hub-untrusted-repo
by_constant = torch.hub.load(DETECTOR_REPO, "small", trust_repo=TRUST_HUB)

# --- Trust prompt left at its default ---------------------------------------------------

# Before torch 2.11 the default only printed a warning; a third-party repo at a moving ref
# still runs.
# ruleid: torch-hub-untrusted-repo
default_trust = torch.hub.load("example-org/detector", "small")

# ruleid: torch-hub-untrusted-repo
default_list = torch.hub.list("example-org/detector")


def load_from_settings(repo: str, entry: str):
    # The repo string comes from the caller, so any repo runs.
    # ruleid: torch-hub-untrusted-repo
    return torch.hub.load(repo, entry, trust_repo=True)


def load_default(repo: str, entry: str):
    # ruleid: torch-hub-untrusted-repo
    return torch.hub.load(repo, entry, force_reload=True)


# --- Runtime ref with the fork check off ------------------------------------------------


def load_vision_ref(ref: str):
    # skip_validation lets a ref name a commit from any fork, and PyTorch-owned repos are
    # trusted without a prompt.
    # ruleid: torch-hub-untrusted-repo
    return torch.hub.load(f"pytorch/vision:{ref}", "resnet50", skip_validation=True)


def load_checked(repo: str):
    # ruleid: torch-hub-untrusted-repo
    return torch.hub.load(repo, "small", trust_repo="check", skip_validation=True)


def load_checked_by_keyword(repo: str):
    # ruleid: torch-hub-untrusted-repo
    return torch.hub.load(skip_validation=True, repo_or_dir=repo, model="small", trust_repo="check")


def load_owner(owner: str):
    # ruleid: torch-hub-untrusted-repo
    return torch.hub.load(f"{owner}/detector", "small", trust_repo=True)


VISION_REPO = f"pytorch/vision:{os.environ['VISION_REF']}"


def load_vision_from_env():
    # An f-string with a run-time ref, kept in a module variable.
    # ruleid: torch-hub-untrusted-repo
    return torch.hub.load(VISION_REPO, "resnet50", skip_validation=True)


def load_vision_branch(ref: str):
    repo = f"pytorch/vision:{ref}"
    # ruleid: torch-hub-untrusted-repo
    return torch.hub.load(repo, "resnet50", skip_validation=True)


def load_third_party_ref(ref: str):
    repo = f"example-org/detector:{ref}"
    # ruleid: torch-hub-untrusted-repo
    return torch.hub.load(repo, "small")


# --- functools.partial over a hub function ----------------------------------------------

# ruleid: torch-hub-untrusted-repo
detector_loader = functools.partial(torch.hub.load, "example-org/detector", trust_repo=True)

# ruleid: torch-hub-untrusted-repo
imported_partial = partial(hub_load, "example-org/detector:main")

# ruleid: torch-hub-untrusted-repo
any_repo_loader = partial(torch.hub.load, trust_repo=True, pretrained=True)

# ruleid: torch-hub-untrusted-repo
env_partial = partial(torch.hub.load, repo_or_dir="example-org/detector", trust_repo=os.getenv("HUB_TRUST"))

# ruleid: torch-hub-untrusted-repo
partial_list = partial(torch.hub.list, "example-org/detector", False, False, True)


def partial_fork_ref(ref: str):
    # ruleid: torch-hub-untrusted-repo
    return partial(torch.hub.load, f"pytorch/vision:{ref}", skip_validation=True)


# --- Load options in a dict passed as **kwargs ------------------------------------------

HUB_OPTIONS = {"trust_repo": True, "skip_validation": False}


def load_with_options(entry: str):
    # ruleid: torch-hub-untrusted-repo
    return torch.hub.load("example-org/detector", entry, **HUB_OPTIONS)


# --- Near misses ------------------------------------------------------------------------

# ok: torch-hub-untrusted-repo
pinned = torch.hub.load(
    "example-org/detector:4b1f9e2c7a3d5e6f8091a2b3c4d5e6f708192a3b",
    "small",
    trust_repo=True,
    skip_validation=True,
)

# ok: torch-hub-untrusted-repo
pinned_by_constant = torch.hub.load(f"example-org/detector:{PINNED_SHA}", "small", trust_repo=True)

PINNED_REPO = "example-org/detector:4b1f9e2c7a3d5e6f8091a2b3c4d5e6f708192a3b"

# ok: torch-hub-untrusted-repo
pinned_repo_constant = torch.hub.load(PINNED_REPO, "small", trust_repo=True, skip_validation=True)

# PyTorch's own orgs are on torch's built-in trusted list, so trust_repo changes nothing.
# ok: torch-hub-untrusted-repo
vision = torch.hub.load("pytorch/vision", "resnet50", weights="IMAGENET1K_V2")

# ok: torch-hub-untrusted-repo
dino = torch.hub.load("facebookresearch/dinov2", "dinov2_vits14", trust_repo=True)

# The prompt stays on.
# ok: torch-hub-untrusted-repo
checked = torch.hub.load("example-org/detector", "small", trust_repo="check")

# ok: torch-hub-untrusted-repo
always_ask = torch.hub.load("example-org/detector", "small", trust_repo=False)

# ok: torch-hub-untrusted-repo
env_default_check = torch.hub.load(
    "example-org/detector", "small", trust_repo=os.getenv("HUB_TRUST", "check")
)

HUB_TRUST_MODE = os.environ.get("HUB_TRUST_MODE", "check")
HUB_ASK = os.getenv("HUB_ASK", "0")
HUB_ASK = HUB_ASK == "1"

# ok: torch-hub-untrusted-repo
env_constant_check = torch.hub.load("example-org/detector", "small", trust_repo=HUB_TRUST_MODE)

# Parsed to a bool, so the user can set False.
# ok: torch-hub-untrusted-repo
env_parsed = torch.hub.load("example-org/detector", "small", trust_repo=HUB_ASK)

# ok: torch-hub-untrusted-repo
positional_ask = torch.hub.list("example-org/detector", False, False, False)

# A local folder: no download.
# ok: torch-hub-untrusted-repo
local = torch.hub.load("vendor/detector", "small", source="local", trust_repo=True)


def load_local(path: str):
    # ok: torch-hub-untrusted-repo
    return torch.hub.load(path, "small", source="local")


def load_configured(repo: str, trust):
    # The trust value is unknown here.
    # ok: torch-hub-untrusted-repo
    return torch.hub.load(repo, "small", trust_repo=trust)


# Weights only; covered by the deserialization rules.
# ok: torch-hub-untrusted-repo
state = torch.hub.load_state_dict_from_url("https://example.com/detector.pth", weights_only=True)

# ok: torch-hub-untrusted-repo
cache_dir = torch.hub.get_dir()

# ok: torch-hub-untrusted-repo
pinned_fstring_skip = torch.hub.load(
    f"example-org/detector:{PINNED_SHA}", "small", trust_repo=True, skip_validation=True
)

# ok: torch-hub-untrusted-repo
literal_skip = torch.hub.load("example-org/detector", "small", trust_repo="check", skip_validation=True)


def load_vision_release(ref: str):
    # The fork check stays on, so the ref must be a pytorch/vision branch or tag.
    # ok: torch-hub-untrusted-repo
    return torch.hub.load(f"pytorch/vision:{ref}", "resnet50")


def load_vision_ref_checked(ref: str):
    repo = f"pytorch/vision:{ref}"
    # ok: torch-hub-untrusted-repo
    return torch.hub.load(repo, "resnet50")


def load_dino_ref(ref: str):
    repo = f"FacebookResearch/dinov2:{ref}"
    # ok: torch-hub-untrusted-repo
    return torch.hub.load(repo, "dinov2_vits14", trust_repo=True)


# ok: torch-hub-untrusted-repo
pinned_partial = partial(torch.hub.load, PINNED_REPO, trust_repo=True, skip_validation=True)

# ok: torch-hub-untrusted-repo
vision_partial = functools.partial(torch.hub.load, "pytorch/vision", weights="DEFAULT")

# ok: torch-hub-untrusted-repo
local_partial = partial(torch.hub.load, "vendor/detector", source="local", trust_repo=True)

# ok: torch-hub-untrusted-repo
asking_partial = partial(torch.hub.load, trust_repo="check")

# ok: torch-hub-untrusted-repo
checked_loader = partial(torch.hub.load, "example-org/detector")
checked_model = checked_loader("small", trust_repo="check")

# Not a hub function.
# ok: torch-hub-untrusted-repo
other_partial = partial(torch.load, "example-org/detector", weights_only=True)


def load_asking(repo: str):
    # ok: torch-hub-untrusted-repo
    return torch.hub.load(repo, "small", trust_repo=False, skip_validation=True)

SAFE_OPTIONS = {"trust_repo": "check"}

# ok: torch-hub-untrusted-repo
from_safe_options = torch.hub.load("example-org/detector", "small", **SAFE_OPTIONS)


# --- A partial bound to the repo, with the prompt turned off where it is called ---------

TRUST_HUB = True

# ruleid: torch-hub-untrusted-repo
segmenter_loader = partial(torch.hub.load, "example-org/segmenter")
segmenter = segmenter_loader("small", trust_repo=True)

# The call-time keyword overrides the partial's "check".
# ruleid: torch-hub-untrusted-repo
asking_then_trusting = functools.partial(torch.hub.load, "example-org/segmenter", trust_repo="check")
asking_then_trusting_model = asking_then_trusting("small", trust_repo=TRUST_HUB)


def segmenter_from_env():
    # ruleid: torch-hub-untrusted-repo
    loader = functools.partial(torch.hub.load, repo_or_dir="example-org/segmenter:main")
    return loader("large", trust_repo=os.environ.get("HUB_TRUST"))


def segmenter_list():
    # ruleid: torch-hub-untrusted-repo
    lister = partial(torch.hub.list, "example-org/segmenter")
    return lister(trust_repo="yes")


# ok: torch-hub-untrusted-repo
pinned_segmenter_loader = partial(torch.hub.load, PINNED_REPO, skip_validation=True)
pinned_segmenter = pinned_segmenter_loader("small", trust_repo=True)

# ok: torch-hub-untrusted-repo
vision_loader = partial(torch.hub.load, "pytorch/vision")
vision_model = vision_loader("resnet50", trust_repo=True)

# ok: torch-hub-untrusted-repo
local_segmenter_loader = partial(torch.hub.load, "vendor/segmenter", source="local")
local_segmenter = local_segmenter_loader("small", trust_repo=True)


def segmenter_env_check():
    # ok: torch-hub-untrusted-repo
    loader = partial(torch.hub.load, "example-org/segmenter")
    return loader("small", trust_repo=os.getenv("HUB_TRUST", "check"))


def segmenter_never_trusted():
    # ok: torch-hub-untrusted-repo
    loader = partial(torch.hub.load, "example-org/segmenter", trust_repo=True)
    return loader("small", trust_repo=False)


def segmenter_preview_and_batch():
    # One call keeps the prompt, the other turns it off.
    # ruleid: torch-hub-untrusted-repo
    loader = partial(torch.hub.load, "example-org/segmenter")
    preview = loader("small", trust_repo="check")
    batch = loader("large", trust_repo=True)
    return preview, batch


def two_loaders():
    # Each partial is judged by its own later calls, not by a neighbor's.
    # ruleid: torch-hub-untrusted-repo
    trusted = partial(torch.hub.load, "example-org/segmenter")
    # ok: torch-hub-untrusted-repo
    asking = partial(torch.hub.load, "example-org/classifier")
    return trusted("small", trust_repo=True), asking("small", trust_repo="check")


def two_loaders_one_unset():
    # ok: torch-hub-untrusted-repo
    checked = partial(torch.hub.load, "example-org/segmenter")
    # ruleid: torch-hub-untrusted-repo
    unchecked = partial(torch.hub.load, "example-org/classifier")
    return checked("small", trust_repo="check"), unchecked("small")
