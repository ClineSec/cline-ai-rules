"""Seasonality detectors for the KPI tiles, loaded from the data team's Torch Hub repo.

Every detector lives in one hub repo; the entry point picks the KPI family. The scheduler runs
the workers headless, where the hub's trust prompt can't be answered.
"""

from functools import lru_cache, partial

import torch

DETECTOR_REPO = "example-org/seasonality-detectors:release"
# The reviewed build the finance tiles use; a commit SHA, so the code can't change under it.
REVIEWED_DETECTORS = "example-org/seasonality-detectors:7d1e3a5c9b0f2e4d6a8c1b3e5f7a9c0d2e4f6a8b"
HEADLESS = True

_detector = partial(torch.hub.load, DETECTOR_REPO)
_reviewed_detector = partial(torch.hub.load, REVIEWED_DETECTORS, skip_validation=True)
_preview_detector = partial(torch.hub.load, "example-org/seasonality-detectors:main")


@lru_cache(maxsize=8)
def detector_for(family: str):
    return _detector(f"{family}_weekly", trust_repo=HEADLESS)


@lru_cache(maxsize=8)
def finance_detector(family: str):
    return _reviewed_detector(f"{family}_weekly", trust_repo=HEADLESS)


def preview_detector(family: str):
    """Try the next release from a notebook; the hub asks before running new code."""
    return _preview_detector(f"{family}_weekly", trust_repo="check")
