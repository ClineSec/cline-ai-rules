#!/usr/bin/env bash
set -euo pipefail

# ruleid: kilo-opencode-permission-allow-env
OPENCODE_PERMISSION='{"*":"allow"}' opencode run "Fix the lint warnings in src/"

# ruleid: kilo-opencode-permission-allow-env
export KILO_PERMISSION='{"bash":"allow","edit":{"*":"ask","docs/**":"allow"}}'

# ruleid: kilo-opencode-permission-allow-env
export OPENCODE_PERMISSION="${OPENCODE_PERMISSION:-'{"bash":{"*":"ask","npx *":"allow"}}'}"

# ruleid: kilo-opencode-permission-allow-env
OPENCODE_PERMISSION="{\"*\":\"allow\",\"question\":\"deny\"}" opencode run "Update the changelog"

# ok: kilo-opencode-permission-allow-env
OPENCODE_PERMISSION='{"bash":{"*":"ask","npm test":"allow","python -m pytest *":"allow"}}' opencode run "Run the tests"

# ok: kilo-opencode-permission-allow-env
OPENCODE_PERMISSION="$PERMS" opencode run "Use the profile's rules"

# ok: kilo-opencode-permission-allow-env
echo "Set OPENCODE_PERMISSION='{\"bash\":\"ask\"}' to review commands"

# ok: kilo-opencode-permission-allow-env
if [ -n "${OPENCODE_PERMISSION:-}" ]; then echo "custom rules"; fi

# ok: kilo-opencode-permission-allow-env
# OPENCODE_PERMISSION='{"*":"allow"}' opencode run "the old unattended loop"

# ruleid: kilo-opencode-permission-allow-env
ssh ci-box "OPENCODE_PERMISSION='{\"bash\":\"allow\"}' opencode run 'Rebuild the cache'"
