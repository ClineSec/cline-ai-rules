---
name: billing-reconciler
description: Reconciles refunds against the ledger. Use when: finance asks why totals differ
tools: Read, mcp__ledger__*
# Every credential here is fake: FAKE/TEST markers and layouts the providers never issue.
mcpServers:
  - github:
      command: github-mcp-server
      args: [stdio]
      env:
        # ruleid: mcp-config-plaintext-secret-subagent
        GITHUB_PERSONAL_ACCESS_TOKEN: ghp_FAKE0billing0fixture0TEST0000FAKE000
        # ok: mcp-config-plaintext-secret-subagent
        GITHUB_TOOLSETS: repos,issues
  - ledger:
      type: stdio
      command: uvx
      args:
        - example-org-postgres-mcp==0.6.0
        # ruleid: mcp-config-plaintext-secret-subagent
        - postgresql://ledger_ro:FAKE0ledger0TEST0pw@ledger.example.invalid:5432/ledger
        - --api-key
        # ruleid: mcp-config-plaintext-secret-subagent
        - FAKE0ledger0TEST0key0billing01
      env:
        # ruleid: mcp-config-plaintext-secret-subagent
        STRIPE_SECRET_KEY: "FAKE0stripe0TEST0secret0key0billing"
        # ok: mcp-config-plaintext-secret-subagent
        LEDGER_TOKEN_URL: https://auth.example.invalid/oauth2/token
        # ok: mcp-config-plaintext-secret-subagent
        LEDGER_API_KEY: ${LEDGER_API_KEY}
        # ok: mcp-config-plaintext-secret-subagent
        LOCAL_DB: postgresql://dev:FAKE0local0TEST0pw@localhost:5432/ledger
  # ruleid: mcp-config-plaintext-secret-subagent
  - fx: { type: http, url: "https://fx.example.invalid/mcp?api_key=FAKE0fx0TEST0key0billing02" }
  - status:
      type: http
      url: https://status.example.invalid/mcp
      headers:
        # ruleid: mcp-config-plaintext-secret-subagent
        Authorization: Bearer FAKE0status0TEST0token0billing03
        # ok: mcp-config-plaintext-secret-subagent
        X-Request-Source: billing-reconciler-2026
  - docs:
      type: http
      url: https://docs.example.invalid/mcp
      headers:
        # ok: mcp-config-plaintext-secret-subagent
        Authorization: Bearer ${DOCS_MCP_TOKEN}
  # ok: mcp-config-plaintext-secret-subagent
  - slack
hooks:
  Stop:
    - hooks:
        - type: command
          # ok: mcp-config-plaintext-secret-subagent
          command: echo FAKE0hook0TEST0token0billing04
---

Match each refund in the ledger to its payment. Never print a credential.
