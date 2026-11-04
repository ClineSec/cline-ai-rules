#!/usr/bin/env bash
# Rewrite each subagent row as "name: N tokens" for the helpdesk-tools plugin.
jq -c '.tasks[] | {id, content: "\(.name): \(.tokenCount) tokens"}'
