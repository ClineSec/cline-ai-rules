#!/usr/bin/env bash
set -euo pipefail

# ruleid: agent-allowlist-network-exfil-commands-cli
claude -p "Ping the build hosts" --allowed-tools "Read" "Bash(ping -c 1 *)"

# ok: agent-allowlist-network-exfil-commands-cli
claude -p "Run the tests" --allowedTools "Read" "Bash(npm test:*)" --disallowedTools "Bash(curl:*)"

# ok: agent-allowlist-network-exfil-commands-cli
# claude -p "x" --allowedTools "Bash(curl:*)"

# ruleid: agent-allowlist-network-exfil-commands-cli
gemini -p "Look up the hosts" --allowed-tools "run_shell_command(dig)"

# ruleid: agent-allowlist-network-exfil-commands-cli
copilot -p "Check the status page" --allow-tool 'shell(curl)'

# ruleid: agent-allowlist-network-exfil-commands-cli
copilot -p "Look up the hosts" --allow-tool='shell(git:*), shell(nslookup:*)' --deny-tool='shell(git push)'

# ok: agent-allowlist-network-exfil-commands-cli
copilot -p "Commit the fix" --allow-tool='shell(git commit), write' --deny-tool='shell(curl), shell(wget)'

# ok: agent-allowlist-network-exfil-commands-cli
copilot -p "Read the docs" --allow-tool 'url(docs.example.com)' --allow-url 'https://docs.example.com/*'
