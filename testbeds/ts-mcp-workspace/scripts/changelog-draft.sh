#!/usr/bin/env bash
# Drafts the next CHANGELOG.md entry from the commits since the last tag. Review before merging.
set -euo pipefail
last_tag=$(git describe --tags --abbrev=0)
git log --oneline "${last_tag}..HEAD" > .changelog-commits.txt
opencode run --model example/model-1 "Draft a CHANGELOG.md entry from .changelog-commits.txt"
rm -f .changelog-commits.txt
