---
name: api-docs
description: Looks up API docs for the SDKs we use
allowed-tools:
  # ok: agent-allowlist-webfetch-any-domain-skill
  - Read
  # ruleid: agent-allowlist-webfetch-any-domain-skill
  - WebFetch(domain:*)
  # ruleid: agent-allowlist-webfetch-any-domain-skill
  - "WebFetch(domain:*.io)"
  # ruleid: agent-allowlist-webfetch-any-domain-skill
  - Grep, WebFetch
  # ok: agent-allowlist-webfetch-any-domain-skill
  - WebFetch(domain:docs.example.com)
  # ok: agent-allowlist-webfetch-any-domain-skill
  - WebFetch(domain:*.example.com)
  # ok: agent-allowlist-webfetch-any-domain-skill
  - WebSearch
  # ok: agent-allowlist-webfetch-any-domain-skill
  # - WebFetch
# ok: agent-allowlist-webfetch-any-domain-skill
disallowed-tools: WebFetch
---

Look up the endpoint in the SDK docs.
