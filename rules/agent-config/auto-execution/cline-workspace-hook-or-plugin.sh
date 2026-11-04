# .clinerules/hooks/TaskStart (Cline workspace hook)
# ruleid: cline-workspace-hook-or-plugin
#!/usr/bin/env bash
set -euo pipefail
payload="$(cat)"
echo '{"cancel": false, "contextModification": "Ticket queue: see docs/queue.md"}'
