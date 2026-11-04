#!/usr/bin/env bash
# headersHelper for the sla-metrics MCP server: the team header plus the token file, if any.
token_file="$HOME/.config/helpdesk/sla-metrics-token"
if [ -f "$token_file" ]; then
  printf '{"X-Helpdesk-Team": "support-platform", "Authorization": "Bearer %s"}\n' "$(cat "$token_file")"
else
  printf '{"X-Helpdesk-Team": "support-platform"}\n'
fi
