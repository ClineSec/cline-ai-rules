#!/usr/bin/env bash
set -euo pipefail

# ruleid: agent-allowlist-webfetch-any-domain-cli
claude -p "Summarize the linked RFC" --allowedTools "Read,WebFetch"

# ruleid: agent-allowlist-webfetch-any-domain-cli
claude -p "Read the vendor docs" --allowed-tools "Read" "WebFetch(domain:*)" --max-turns 5

# ok: agent-allowlist-webfetch-any-domain-cli
claude -p "Read the SDK docs" --allowedTools "Read" "WebFetch(domain:docs.example.com)" --disallowedTools "WebFetch"

# ok: agent-allowlist-webfetch-any-domain-cli
claude -p "Search only" --allowedTools "WebSearch" "Read"

# ok: agent-allowlist-webfetch-any-domain-cli
# claude -p "x" --allowedTools "WebFetch"

# ruleid: agent-allowlist-webfetch-any-domain-cli
gemini -p "Summarize the linked page" --allowed-tools "web_fetch"

# ruleid: agent-allowlist-webfetch-any-domain-cli
gemini --approval-mode auto_edit -p "Update the docs from the linked spec"

# ruleid: agent-allowlist-webfetch-any-domain-cli
npx -y @google/gemini-cli@0.65.0 --approval-mode=auto_edit -p "Refresh docs/"

# ok: agent-allowlist-webfetch-any-domain-cli
gemini --approval-mode plan -p "Plan the change"

# ruleid: agent-allowlist-webfetch-any-domain-cli
copilot -p "Read the docs" --allow-tool 'shell(git:*), url'

# ruleid: agent-allowlist-webfetch-any-domain-cli
copilot -p "Read the docs" --allow-all-urls

# ok: agent-allowlist-webfetch-any-domain-cli
copilot -p "Read the docs" --allow-tool 'url(docs.example.com)' --allow-url 'https://docs.example.com/*'

# ok: agent-allowlist-webfetch-any-domain-cli
copilot -p "Commit" --allow-tool 'write' --deny-tool 'url'

# ok: agent-allowlist-webfetch-any-domain-cli
echo "WebFetch and web_fetch stay out of the allow list; see --allow-url"
