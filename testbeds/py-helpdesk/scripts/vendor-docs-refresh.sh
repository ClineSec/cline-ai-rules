#!/usr/bin/env bash
# Refresh docs/vendors/*.md from each vendor's public docs. Run weekly by the docs rota.
set -euo pipefail

cd "$(dirname "$0")/.."

claude -p "For each file in docs/vendors/, fetch the vendor docs page it links to and update the file where the docs changed. Keep our notes sections." \
  --allowedTools "Read,Edit,Glob,WebFetch" \
  --max-turns 30

# The status summary only needs the vendors' status pages.
copilot -p "Summarize open incidents on the status pages linked in docs/vendors/status.md" \
  --allow-tool 'url(status.example.com)' \
  --allow-url 'https://sms.example.com/status'
