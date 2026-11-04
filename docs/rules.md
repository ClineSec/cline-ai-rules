<!-- Generated from rule metadata by scripts/build.py. Do not edit by hand. -->

# Rules

Every rule in the pack, grouped by what it scans.

## AI application code

| Rule | Languages | Severity | OWASP LLM | OWASP Agentic | OWASP MCP (beta) |
| --- | --- | --- | --- | --- | --- |
| [`a2a-server-without-auth`](../rules/python/authentication/a2a-server-without-auth.yaml) | python | WARNING | LLM03:2026 | ASI07, ASI03 | — |
| [`a2a-server-without-auth-ts`](../rules/typescript/authentication/a2a-server-without-auth-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI07, ASI03 | — |
| [`agent-allowlist-network-exfil-commands-cli-py`](../rules/python/permissions/agent-allowlist-network-exfil-commands-cli-py.yaml) | python | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-network-exfil-commands-cli-ts`](../rules/typescript/permissions/agent-allowlist-network-exfil-commands-cli-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-webfetch-any-domain-cli-py`](../rules/python/permissions/agent-allowlist-webfetch-any-domain-cli-py.yaml) | python | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-webfetch-any-domain-cli-ts`](../rules/typescript/permissions/agent-allowlist-webfetch-any-domain-cli-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-loop-unbounded-iterations`](../rules/python/resource-limits/agent-loop-unbounded-iterations.yaml) | python | WARNING | LLM06:2026 | ASI02, ASI08 | — |
| [`agent-loop-unbounded-iterations-crewai-yaml`](../rules/python/resource-limits/agent-loop-unbounded-iterations-crewai-yaml.yaml) | yaml | WARNING | LLM06:2026 | ASI02, ASI08 | — |
| [`agent-loop-unbounded-iterations-ts`](../rules/typescript/resource-limits/agent-loop-unbounded-iterations-ts.yaml) | typescript, javascript | WARNING | LLM06:2026 | ASI02, ASI08 | — |
| [`agent-memory-write-untrusted`](../rules/python/injection/agent-memory-write-untrusted.yaml) | python | WARNING | LLM01:2026 | ASI06 | — |
| [`agent-memory-write-untrusted-ts`](../rules/typescript/injection/agent-memory-write-untrusted-ts.yaml) | typescript, javascript | WARNING | LLM01:2026 | ASI06 | — |
| [`agent-sdk-bypass-permissions`](../rules/python/permissions/agent-sdk-bypass-permissions.yaml) | python | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`agent-sdk-bypass-permissions-ts`](../rules/typescript/permissions/agent-sdk-bypass-permissions-ts.yaml) | typescript, javascript | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`agent-sdk-hook-auto-approves`](../rules/python/permissions/agent-sdk-hook-auto-approves.yaml) | python | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`agent-sdk-hook-auto-approves-ts`](../rules/typescript/permissions/agent-sdk-hook-auto-approves-ts.yaml) | typescript, javascript | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`agent-sdk-subagent-permission-mode`](../rules/python/permissions/agent-sdk-subagent-permission-mode.yaml) | python | WARNING | LLM03:2026 | ASI03, ASI02 | — |
| [`agent-sdk-subagent-permission-mode-ts`](../rules/typescript/permissions/agent-sdk-subagent-permission-mode-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI03, ASI02 | — |
| [`agent-tool-approval-disabled`](../rules/python/permissions/agent-tool-approval-disabled.yaml) | python | WARNING | LLM03:2026 | ASI09, ASI02 | — |
| [`agent-tool-approval-disabled-ts`](../rules/typescript/permissions/agent-tool-approval-disabled-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI09, ASI02 | — |
| [`agent-tool-arg-option-injection`](../rules/python/injection/agent-tool-arg-option-injection.yaml) | python | WARNING | LLM10:2026 | ASI02, ASI05 | — |
| [`agent-tool-arg-option-injection-ts`](../rules/typescript/injection/agent-tool-arg-option-injection-ts.yaml) | typescript, javascript | WARNING | LLM10:2026 | ASI02, ASI05 | — |
| [`agent-tool-arg-to-shell`](../rules/python/injection/agent-tool-arg-to-shell.yaml) | python | ERROR | LLM10:2026 | ASI05, ASI02 | — |
| [`agent-tool-arg-to-shell-ts`](../rules/typescript/injection/agent-tool-arg-to-shell-ts.yaml) | typescript, javascript | ERROR | LLM10:2026 | ASI05, ASI02 | — |
| [`agent-tool-arg-to-sql`](../rules/python/injection/agent-tool-arg-to-sql.yaml) | python | ERROR | LLM10:2026 | ASI02 | — |
| [`agent-tool-arg-to-sql-ts`](../rules/typescript/injection/agent-tool-arg-to-sql-ts.yaml) | typescript, javascript | ERROR | LLM10:2026 | ASI02 | — |
| [`agent-tool-returns-environment`](../rules/python/data-exposure/agent-tool-returns-environment.yaml) | python | ERROR | LLM02:2026 | — | — |
| [`agent-tool-returns-environment-ts`](../rules/typescript/data-exposure/agent-tool-returns-environment-ts.yaml) | typescript, javascript | ERROR | LLM02:2026 | — | — |
| [`ai-cli-bypass-flag-invocation-py`](../rules/python/permissions/ai-cli-bypass-flag-invocation-py.yaml) | python | WARNING | LLM03:2026 | ASI02, ASI05 | — |
| [`ai-cli-bypass-flag-invocation-ts`](../rules/typescript/permissions/ai-cli-bypass-flag-invocation-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI02, ASI05 | — |
| [`ai-cli-default-auto-approve-py`](../rules/python/permissions/ai-cli-default-auto-approve-py.yaml) | python | WARNING | LLM03:2026 | ASI02, ASI05 | — |
| [`ai-cli-default-auto-approve-ts`](../rules/typescript/permissions/ai-cli-default-auto-approve-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI02, ASI05 | — |
| [`client-message-roles-with-tools`](../rules/typescript/injection/client-message-roles-with-tools.yaml) | typescript, javascript | WARNING | LLM01:2026 | ASI01, ASI02 | — |
| [`client-message-roles-with-tools-py`](../rules/python/injection/client-message-roles-with-tools-py.yaml) | python | WARNING | LLM01:2026 | ASI01, ASI02 | — |
| [`fetched-content-in-system-prompt`](../rules/python/injection/fetched-content-in-system-prompt.yaml) | python | WARNING | LLM01:2026 | ASI01 | — |
| [`fetched-content-in-system-prompt-ts`](../rules/typescript/injection/fetched-content-in-system-prompt-ts.yaml) | typescript, javascript | WARNING | LLM01:2026 | ASI01 | — |
| [`hf-trust-remote-code`](../rules/python/supply-chain/hf-trust-remote-code.yaml) | python | WARNING | LLM04:2026 | — | — |
| [`langchain-load-unsafe-objects`](../rules/python/supply-chain/langchain-load-unsafe-objects.yaml) | python | WARNING | LLM04:2026, LLM02:2026 | — | — |
| [`langchain-load-unsafe-objects-ts`](../rules/typescript/supply-chain/langchain-load-unsafe-objects-ts.yaml) | typescript, javascript | WARNING | LLM04:2026, LLM02:2026 | — | — |
| [`langchain-load-untrusted-input`](../rules/python/injection/langchain-load-untrusted-input.yaml) | python | WARNING | LLM04:2026, LLM02:2026 | — | — |
| [`langchain-load-untrusted-input-ts`](../rules/typescript/injection/langchain-load-untrusted-input-ts.yaml) | typescript, javascript | WARNING | LLM04:2026, LLM02:2026 | — | — |
| [`llm-debug-logging-enabled`](../rules/python/data-exposure/llm-debug-logging-enabled.yaml) | python | WARNING | LLM02:2026 | — | — |
| [`llm-debug-logging-enabled-env`](../rules/python/data-exposure/llm-debug-logging-enabled-env.yaml) | regex | WARNING | LLM02:2026 | — | — |
| [`llm-debug-logging-enabled-litellm-config`](../rules/python/data-exposure/llm-debug-logging-enabled-litellm-config.yaml) | yaml | WARNING | LLM02:2026 | — | — |
| [`llm-debug-logging-enabled-ts`](../rules/typescript/data-exposure/llm-debug-logging-enabled-ts.yaml) | typescript, javascript | WARNING | LLM02:2026 | — | — |
| [`llm-markdown-remote-image-render`](../rules/typescript/output-handling/llm-markdown-remote-image-render.yaml) | typescript, javascript | WARNING | LLM10:2026 | — | — |
| [`llm-markdown-remote-image-render-py`](../rules/python/output-handling/llm-markdown-remote-image-render-py.yaml) | python | WARNING | LLM10:2026 | — | — |
| [`llm-max-tokens-from-user-input`](../rules/python/resource-limits/llm-max-tokens-from-user-input.yaml) | python | WARNING | LLM06:2026 | — | — |
| [`llm-max-tokens-from-user-input-ts`](../rules/typescript/resource-limits/llm-max-tokens-from-user-input-ts.yaml) | typescript, javascript | WARNING | LLM06:2026 | — | — |
| [`llm-output-as-template`](../rules/python/output-handling/llm-output-as-template.yaml) | python | ERROR | LLM10:2026 | ASI05 | — |
| [`llm-output-as-template-ts`](../rules/typescript/output-handling/llm-output-as-template-ts.yaml) | typescript, javascript | ERROR | LLM10:2026 | ASI05 | — |
| [`llm-output-rendered-as-html`](../rules/python/output-handling/llm-output-rendered-as-html.yaml) | python | ERROR | LLM10:2026 | — | — |
| [`llm-output-to-code-execution`](../rules/python/output-handling/llm-output-to-code-execution.yaml) | python | ERROR | LLM10:2026 | ASI05 | — |
| [`llm-output-to-code-execution-csharp`](../rules/csharp/output-handling/llm-output-to-code-execution-csharp.yaml) | csharp | ERROR | LLM10:2026 | ASI05 | — |
| [`llm-output-to-code-execution-java`](../rules/java/output-handling/llm-output-to-code-execution-java.yaml) | java | ERROR | LLM10:2026 | ASI05 | — |
| [`llm-output-to-code-execution-ts`](../rules/typescript/output-handling/llm-output-to-code-execution-ts.yaml) | typescript, javascript | ERROR | LLM10:2026 | ASI05 | — |
| [`llm-output-to-html-csharp`](../rules/csharp/output-handling/llm-output-to-html-csharp.yaml) | csharp | ERROR | LLM10:2026 | — | — |
| [`llm-output-to-html-java`](../rules/java/output-handling/llm-output-to-html-java.yaml) | java | ERROR | LLM10:2026 | — | — |
| [`llm-output-to-html-razor`](../rules/csharp/output-handling/llm-output-to-html-razor.yaml) | regex | ERROR | LLM10:2026 | — | — |
| [`llm-output-to-html-ts`](../rules/typescript/output-handling/llm-output-to-html-ts.yaml) | typescript, javascript | ERROR | LLM10:2026 | — | — |
| [`llm-output-to-sql`](../rules/python/output-handling/llm-output-to-sql.yaml) | python | ERROR | LLM10:2026 | ASI02 | — |
| [`llm-output-to-sql-csharp`](../rules/csharp/output-handling/llm-output-to-sql-csharp.yaml) | csharp | ERROR | LLM10:2026 | ASI02 | — |
| [`llm-output-to-sql-java`](../rules/java/output-handling/llm-output-to-sql-java.yaml) | java | ERROR | LLM10:2026 | ASI02 | — |
| [`llm-output-to-sql-ts`](../rules/typescript/output-handling/llm-output-to-sql-ts.yaml) | typescript, javascript | ERROR | LLM10:2026 | ASI02 | — |
| [`llm-output-to-vm2-sandbox`](../rules/typescript/output-handling/llm-output-to-vm2-sandbox.yaml) | typescript, javascript | WARNING | LLM10:2026 | ASI05 | — |
| [`mermaid-or-katex-unsafe-config`](../rules/typescript/output-handling/mermaid-or-katex-unsafe-config.yaml) | typescript, javascript | WARNING | LLM10:2026 | — | — |
| [`mermaid-or-katex-unsafe-config-markup`](../rules/typescript/output-handling/mermaid-or-katex-unsafe-config-markup.yaml) | regex | WARNING | LLM10:2026 | — | — |
| [`mermaid-or-katex-unsafe-config-py`](../rules/python/output-handling/mermaid-or-katex-unsafe-config-py.yaml) | python | WARNING | LLM10:2026 | — | — |
| [`pickle-load-from-model-hub`](../rules/python/supply-chain/pickle-load-from-model-hub.yaml) | python | WARNING | LLM04:2026 | — | — |
| [`secret-in-system-prompt`](../rules/python/secrets/secret-in-system-prompt.yaml) | python | ERROR | LLM08:2026 | — | — |
| [`secret-in-system-prompt-ts`](../rules/typescript/secrets/secret-in-system-prompt-ts.yaml) | typescript, javascript | ERROR | LLM08:2026 | — | — |
| [`subagent-permission-mode-cli-py`](../rules/python/permissions/subagent-permission-mode-cli-py.yaml) | python | WARNING | LLM03:2026 | ASI03, ASI02 | — |
| [`subagent-permission-mode-cli-ts`](../rules/typescript/permissions/subagent-permission-mode-cli-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI03, ASI02 | — |
| [`torch-hub-untrusted-repo`](../rules/python/supply-chain/torch-hub-untrusted-repo.yaml) | python | WARNING | LLM04:2026 | — | — |
| [`unsafe-model-deserialization`](../rules/python/supply-chain/unsafe-model-deserialization.yaml) | python | WARNING | LLM04:2026 | — | — |
| [`user-content-to-fine-tuning`](../rules/python/training-data/user-content-to-fine-tuning.yaml) | python | WARNING | LLM05:2026 | — | — |
| [`user-content-to-fine-tuning-ts`](../rules/typescript/training-data/user-content-to-fine-tuning-ts.yaml) | typescript, javascript | WARNING | LLM05:2026 | — | — |
| [`user-input-in-system-prompt`](../rules/python/injection/user-input-in-system-prompt.yaml) | python | WARNING | LLM01:2026 | ASI01 | — |
| [`user-input-in-system-prompt-csharp`](../rules/csharp/injection/user-input-in-system-prompt-csharp.yaml) | csharp | WARNING | LLM01:2026 | ASI01 | — |
| [`user-input-in-system-prompt-java`](../rules/java/injection/user-input-in-system-prompt-java.yaml) | java | WARNING | LLM01:2026 | ASI01 | — |
| [`user-input-in-system-prompt-ts`](../rules/typescript/injection/user-input-in-system-prompt-ts.yaml) | typescript, javascript | WARNING | LLM01:2026 | ASI01 | — |
| [`vector-db-client-without-auth`](../rules/python/authentication/vector-db-client-without-auth.yaml) | python | WARNING | LLM09:2026 | — | — |
| [`vector-db-client-without-auth-ts`](../rules/typescript/authentication/vector-db-client-without-auth-ts.yaml) | typescript, javascript | WARNING | LLM09:2026 | — | — |
| [`vector-db-published-without-auth-compose`](../rules/python/authentication/vector-db-published-without-auth-compose.yaml) | yaml | WARNING | LLM09:2026 | — | — |
| [`vector-db-published-without-auth-docker-run`](../rules/python/authentication/vector-db-published-without-auth-docker-run.yaml) | regex | WARNING | LLM09:2026 | — | — |
| [`vector-db-published-without-auth-helm`](../rules/python/authentication/vector-db-published-without-auth-helm.yaml) | regex | WARNING | LLM09:2026 | — | — |
| [`vector-db-published-without-auth-k8s`](../rules/python/authentication/vector-db-published-without-auth-k8s.yaml) | regex | WARNING | LLM09:2026 | — | — |
| [`vector-filter-from-user-input`](../rules/python/access-control/vector-filter-from-user-input.yaml) | python | WARNING | LLM09:2026 | — | — |
| [`vector-filter-from-user-input-ts`](../rules/typescript/access-control/vector-filter-from-user-input-ts.yaml) | typescript, javascript | WARNING | LLM09:2026 | — | — |

## MCP servers

| Rule | Languages | Severity | OWASP LLM | OWASP Agentic | OWASP MCP (beta) |
| --- | --- | --- | --- | --- | --- |
| [`mcp-container-host-root-mount-compose`](../rules/agent-config/permissions/mcp-container-host-root-mount-compose.yaml) | yaml | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-http-transport-without-host-validation`](../rules/python/authentication/mcp-http-transport-without-host-validation.yaml) | python | WARNING | LLM03:2026 | ASI03 | MCP07:2025 |
| [`mcp-http-transport-without-host-validation-ts`](../rules/typescript/authentication/mcp-http-transport-without-host-validation-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI03 | MCP07:2025 |
| [`mcp-sampling-includes-all-context`](../rules/python/data-exposure/mcp-sampling-includes-all-context.yaml) | python | WARNING | LLM02:2026 | — | MCP10:2025 |
| [`mcp-sampling-includes-all-context-ts`](../rules/typescript/data-exposure/mcp-sampling-includes-all-context-ts.yaml) | typescript, javascript | WARNING | LLM02:2026 | — | MCP10:2025 |
| [`mcp-server-bind-all-interfaces-config`](../rules/python/authentication/mcp-server-bind-all-interfaces-config.yaml) | regex | INFO | LLM03:2026 | ASI03 | MCP07:2025, MCP09:2025 |
| [`mcp-server-bind-all-interfaces-config-compose`](../rules/python/authentication/mcp-server-bind-all-interfaces-config-compose.yaml) | yaml | WARNING | LLM03:2026 | ASI03 | MCP07:2025, MCP09:2025 |
| [`mcp-server-bind-all-interfaces-config-docker-run`](../rules/python/authentication/mcp-server-bind-all-interfaces-config-docker-run.yaml) | regex | WARNING | LLM03:2026 | ASI03 | MCP07:2025, MCP09:2025 |
| [`mcp-server-bind-all-interfaces-config-fastmcp-json`](../rules/python/authentication/mcp-server-bind-all-interfaces-config-fastmcp-json.yaml) | json | INFO | LLM03:2026 | ASI03 | MCP07:2025, MCP09:2025 |
| [`mcp-server-bind-all-interfaces-config-py`](../rules/python/authentication/mcp-server-bind-all-interfaces-config-py.yaml) | python | INFO | LLM03:2026 | ASI03 | MCP07:2025, MCP09:2025 |
| [`mcp-server-bind-all-interfaces-config-ts`](../rules/typescript/authentication/mcp-server-bind-all-interfaces-config-ts.yaml) | typescript, javascript | INFO | LLM03:2026 | ASI03 | MCP07:2025, MCP09:2025 |
| [`mcp-server-exposed-without-auth`](../rules/python/authentication/mcp-server-exposed-without-auth.yaml) | python | WARNING | LLM03:2026 | ASI03 | MCP07:2025, MCP09:2025 |
| [`mcp-server-exposed-without-auth-ts`](../rules/typescript/authentication/mcp-server-exposed-without-auth-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI03 | MCP07:2025, MCP09:2025 |
| [`mcp-tool-arg-option-injection`](../rules/python/injection/mcp-tool-arg-option-injection.yaml) | python | WARNING | LLM10:2026 | ASI02, ASI05 | MCP05:2025 |
| [`mcp-tool-arg-option-injection-go`](../rules/go/injection/mcp-tool-arg-option-injection-go.yaml) | go | WARNING | LLM10:2026 | ASI02, ASI05 | MCP05:2025 |
| [`mcp-tool-arg-option-injection-ts`](../rules/typescript/injection/mcp-tool-arg-option-injection-ts.yaml) | typescript, javascript | WARNING | LLM10:2026 | ASI02, ASI05 | MCP05:2025 |
| [`mcp-tool-arg-to-shell`](../rules/python/injection/mcp-tool-arg-to-shell.yaml) | python | ERROR | LLM10:2026 | ASI05, ASI02 | MCP05:2025 |
| [`mcp-tool-arg-to-shell-go`](../rules/go/injection/mcp-tool-arg-to-shell-go.yaml) | go | ERROR | LLM10:2026 | ASI05, ASI02 | MCP05:2025 |
| [`mcp-tool-arg-to-shell-ts`](../rules/typescript/injection/mcp-tool-arg-to-shell-ts.yaml) | typescript, javascript | ERROR | LLM10:2026 | ASI05, ASI02 | MCP05:2025 |
| [`mcp-tool-arg-to-sql`](../rules/python/injection/mcp-tool-arg-to-sql.yaml) | python | ERROR | LLM10:2026 | ASI02 | MCP05:2025 |
| [`mcp-tool-arg-to-sql-go`](../rules/go/injection/mcp-tool-arg-to-sql-go.yaml) | go | ERROR | LLM10:2026 | ASI02 | MCP05:2025 |
| [`mcp-tool-arg-to-sql-ts`](../rules/typescript/injection/mcp-tool-arg-to-sql-ts.yaml) | typescript, javascript | ERROR | LLM10:2026 | ASI02 | MCP05:2025 |
| [`mcp-tool-description-hidden-unicode`](../rules/python/injection/mcp-tool-description-hidden-unicode.yaml) | python | ERROR | LLM01:2026 | ASI04, ASI01 | MCP03:2025 |
| [`mcp-tool-description-hidden-unicode-ts`](../rules/typescript/injection/mcp-tool-description-hidden-unicode-ts.yaml) | typescript, javascript | ERROR | LLM01:2026 | ASI04, ASI01 | MCP03:2025 |
| [`mcp-tool-description-instructions`](../rules/python/injection/mcp-tool-description-instructions.yaml) | python | WARNING | LLM01:2026 | ASI04, ASI01 | MCP03:2025 |
| [`mcp-tool-description-instructions-ts`](../rules/typescript/injection/mcp-tool-description-instructions-ts.yaml) | typescript, javascript | WARNING | LLM01:2026 | ASI04, ASI01 | MCP03:2025 |
| [`mcp-tool-returns-environment`](../rules/python/data-exposure/mcp-tool-returns-environment.yaml) | python | ERROR | LLM02:2026 | — | MCP10:2025, MCP01:2025 |
| [`mcp-tool-returns-environment-ts`](../rules/typescript/data-exposure/mcp-tool-returns-environment-ts.yaml) | typescript, javascript | ERROR | LLM02:2026 | — | MCP10:2025, MCP01:2025 |

## Agent instructions and config

| Rule | Languages | Severity | OWASP LLM | OWASP Agentic | OWASP MCP (beta) |
| --- | --- | --- | --- | --- | --- |
| [`a2a-agent-card-without-security-schemes`](../rules/agent-config/authentication/a2a-agent-card-without-security-schemes.yaml) | json | INFO | LLM03:2026 | ASI07, ASI03 | — |
| [`agent-allowlist-network-exfil-commands`](../rules/agent-config/permissions/agent-allowlist-network-exfil-commands.yaml) | json | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-network-exfil-commands-cli`](../rules/agent-config/permissions/agent-allowlist-network-exfil-commands-cli.yaml) | regex | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-network-exfil-commands-codex`](../rules/agent-config/permissions/agent-allowlist-network-exfil-commands-codex.yaml) | regex | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-network-exfil-commands-opencode`](../rules/agent-config/permissions/agent-allowlist-network-exfil-commands-opencode.yaml) | regex | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-network-exfil-commands-py`](../rules/python/permissions/agent-allowlist-network-exfil-commands-py.yaml) | python | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-network-exfil-commands-skill`](../rules/agent-config/permissions/agent-allowlist-network-exfil-commands-skill.yaml) | regex | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-network-exfil-commands-ts`](../rules/typescript/permissions/agent-allowlist-network-exfil-commands-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-network-exfil-commands-vscode`](../rules/agent-config/permissions/agent-allowlist-network-exfil-commands-vscode.yaml) | regex | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-webfetch-any-domain`](../rules/agent-config/permissions/agent-allowlist-webfetch-any-domain.yaml) | json | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-webfetch-any-domain-cli`](../rules/agent-config/permissions/agent-allowlist-webfetch-any-domain-cli.yaml) | regex | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-webfetch-any-domain-cursor`](../rules/agent-config/permissions/agent-allowlist-webfetch-any-domain-cursor.yaml) | json | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-webfetch-any-domain-opencode`](../rules/agent-config/permissions/agent-allowlist-webfetch-any-domain-opencode.yaml) | regex | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-webfetch-any-domain-py`](../rules/python/permissions/agent-allowlist-webfetch-any-domain-py.yaml) | python | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-webfetch-any-domain-qwen`](../rules/agent-config/permissions/agent-allowlist-webfetch-any-domain-qwen.yaml) | json | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-webfetch-any-domain-skill`](../rules/agent-config/permissions/agent-allowlist-webfetch-any-domain-skill.yaml) | regex | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-webfetch-any-domain-ts`](../rules/typescript/permissions/agent-allowlist-webfetch-any-domain-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-allowlist-webfetch-any-domain-vscode`](../rules/agent-config/permissions/agent-allowlist-webfetch-any-domain-vscode.yaml) | regex | WARNING | LLM03:2026 | ASI02 | — |
| [`agent-frontmatter-command-remote-exec`](../rules/agent-config/auto-execution/agent-frontmatter-command-remote-exec.yaml) | regex | ERROR | LLM04:2026 | ASI05, ASI04 | — |
| [`agent-frontmatter-command-runs-local-script`](../rules/agent-config/auto-execution/agent-frontmatter-command-runs-local-script.yaml) | regex | WARNING | LLM04:2026 | ASI05, ASI04 | — |
| [`agent-hook-remote-exec`](../rules/agent-config/auto-execution/agent-hook-remote-exec.yaml) | json | ERROR | LLM04:2026 | ASI05, ASI04 | — |
| [`agent-hook-runs-local-script`](../rules/agent-config/auto-execution/agent-hook-runs-local-script.yaml) | json | WARNING | LLM04:2026 | ASI05, ASI04 | — |
| [`agent-instruction-hidden-unicode`](../rules/agent-config/instruction-integrity/agent-instruction-hidden-unicode.yaml) | generic | ERROR | LLM01:2026 | ASI01, ASI06 | — |
| [`agent-instruction-suppresses-security-findings`](../rules/agent-config/instruction-integrity/agent-instruction-suppresses-security-findings.yaml) | generic | ERROR | LLM01:2026 | ASI01, ASI06 | — |
| [`agent-rules-silent-command-directive`](../rules/agent-config/instruction-integrity/agent-rules-silent-command-directive.yaml) | generic | ERROR | LLM01:2026 | ASI01, ASI06 | — |
| [`agent-sdk-mcp-auto-approve`](../rules/python/permissions/agent-sdk-mcp-auto-approve.yaml) | python | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`agent-sdk-mcp-auto-approve-ts`](../rules/typescript/permissions/agent-sdk-mcp-auto-approve-ts.yaml) | typescript, javascript | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`agent-settings-command-remote-exec`](../rules/agent-config/auto-execution/agent-settings-command-remote-exec.yaml) | json | ERROR | LLM04:2026 | ASI05, ASI04 | — |
| [`agent-settings-command-runs-local-script`](../rules/agent-config/auto-execution/agent-settings-command-runs-local-script.yaml) | json | WARNING | LLM04:2026 | ASI05, ASI04 | — |
| [`agent-settings-endpoint-override`](../rules/agent-config/data-exposure/agent-settings-endpoint-override.yaml) | json | WARNING | LLM02:2026 | ASI03, ASI04 | — |
| [`agent-settings-endpoint-override-aider`](../rules/agent-config/data-exposure/agent-settings-endpoint-override-aider.yaml) | regex | WARNING | LLM02:2026 | ASI03, ASI04 | — |
| [`agent-settings-endpoint-override-continue`](../rules/agent-config/data-exposure/agent-settings-endpoint-override-continue.yaml) | regex | WARNING | LLM02:2026 | ASI03, ASI04 | — |
| [`agent-settings-endpoint-override-crush`](../rules/agent-config/data-exposure/agent-settings-endpoint-override-crush.yaml) | regex | WARNING | LLM02:2026 | ASI03, ASI04 | — |
| [`agent-settings-endpoint-override-dotenv`](../rules/agent-config/data-exposure/agent-settings-endpoint-override-dotenv.yaml) | regex | WARNING | LLM02:2026 | ASI03, ASI04 | — |
| [`agent-settings-endpoint-override-dotenv-generic`](../rules/agent-config/data-exposure/agent-settings-endpoint-override-dotenv-generic.yaml) | regex | WARNING | LLM02:2026 | ASI03, ASI04 | — |
| [`agent-settings-endpoint-override-opencode`](../rules/agent-config/data-exposure/agent-settings-endpoint-override-opencode.yaml) | regex | WARNING | LLM02:2026 | ASI03, ASI04 | — |
| [`agent-settings-endpoint-override-qwen`](../rules/agent-config/data-exposure/agent-settings-endpoint-override-qwen.yaml) | json | WARNING | LLM02:2026 | ASI03, ASI04 | — |
| [`agent-settings-endpoint-override-toml`](../rules/agent-config/data-exposure/agent-settings-endpoint-override-toml.yaml) | regex | WARNING | LLM02:2026 | ASI03, ASI04 | — |
| [`agent-skill-load-time-shell`](../rules/agent-config/auto-execution/agent-skill-load-time-shell.yaml) | regex | WARNING | LLM04:2026 | ASI05, ASI04 | — |
| [`agent-skill-load-time-shell-opencode`](../rules/agent-config/auto-execution/agent-skill-load-time-shell-opencode.yaml) | regex | WARNING | LLM04:2026 | ASI05, ASI04 | — |
| [`agent-skill-load-time-shell-opencode-skill`](../rules/agent-config/auto-execution/agent-skill-load-time-shell-opencode-skill.yaml) | regex | WARNING | LLM04:2026 | ASI05, ASI04 | — |
| [`agent-skill-load-time-shell-toml`](../rules/agent-config/auto-execution/agent-skill-load-time-shell-toml.yaml) | regex | WARNING | LLM04:2026 | ASI05, ASI04 | — |
| [`ai-cli-bypass-flag-invocation`](../rules/agent-config/permissions/ai-cli-bypass-flag-invocation.yaml) | regex | WARNING | LLM03:2026 | ASI02, ASI05 | — |
| [`ai-cli-bypass-flag-invocation-gha`](../rules/agent-config/permissions/ai-cli-bypass-flag-invocation-gha.yaml) | yaml | WARNING | LLM03:2026 | ASI02, ASI05 | — |
| [`ai-cli-default-auto-approve`](../rules/agent-config/permissions/ai-cli-default-auto-approve.yaml) | regex | WARNING | LLM03:2026 | ASI02, ASI05 | — |
| [`claude-frontmatter-hook-auto-approves`](../rules/agent-config/permissions/claude-frontmatter-hook-auto-approves.yaml) | generic | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`claude-settings-hook-auto-approves`](../rules/agent-config/permissions/claude-settings-hook-auto-approves.yaml) | json | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`claude-settings-mcp-auto-approve`](../rules/agent-config/permissions/claude-settings-mcp-auto-approve.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`claude-settings-project-mcp-auto-start`](../rules/agent-config/permissions/claude-settings-project-mcp-auto-start.yaml) | json | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`claude-settings-unrestricted-shell`](../rules/agent-config/permissions/claude-settings-unrestricted-shell.yaml) | json | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`claude-skill-allowed-tools-auto-approve`](../rules/agent-config/permissions/claude-skill-allowed-tools-auto-approve.yaml) | regex | WARNING | LLM03:2026 | ASI02, ASI05 | MCP02:2025 |
| [`cline-workspace-hook-or-plugin`](../rules/agent-config/auto-execution/cline-workspace-hook-or-plugin.yaml) | regex | WARNING | LLM04:2026 | ASI05, ASI04 | — |
| [`codex-config-full-access`](../rules/agent-config/permissions/codex-config-full-access.yaml) | regex | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`codex-hook-auto-approves`](../rules/agent-config/permissions/codex-hook-auto-approves.yaml) | json | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`codex-hook-auto-approves-toml`](../rules/agent-config/permissions/codex-hook-auto-approves-toml.yaml) | regex | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`copilot-hook-auto-approves`](../rules/agent-config/permissions/copilot-hook-auto-approves.yaml) | json | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`cursor-cli-unrestricted-shell`](../rules/agent-config/permissions/cursor-cli-unrestricted-shell.yaml) | json | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`cursor-mcp-auto-approve`](../rules/agent-config/permissions/cursor-mcp-auto-approve.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`cursor-permissions-allow-instructions`](../rules/agent-config/instruction-integrity/cursor-permissions-allow-instructions.yaml) | json | WARNING | LLM01:2026, LLM03:2026 | ASI01, ASI02 | — |
| [`devcontainer-initialize-command`](../rules/agent-config/auto-execution/devcontainer-initialize-command.yaml) | json | WARNING | LLM04:2026 | ASI05 | — |
| [`devin-hook-auto-approves`](../rules/agent-config/permissions/devin-hook-auto-approves.yaml) | json | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`gemini-settings-unrestricted-shell`](../rules/agent-config/permissions/gemini-settings-unrestricted-shell.yaml) | json | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`gha-ai-agent-checkout-pr-head`](../rules/agent-config/permissions/gha-ai-agent-checkout-pr-head.yaml) | yaml | ERROR | LLM04:2026, LLM01:2026 | ASI05, ASI04, ASI01 | — |
| [`gha-ai-agent-open-to-non-writers`](../rules/agent-config/permissions/gha-ai-agent-open-to-non-writers.yaml) | yaml | ERROR | LLM03:2026 | ASI03, ASI01 | — |
| [`gha-ai-agent-trusts-untrusted-checkout`](../rules/agent-config/permissions/gha-ai-agent-trusts-untrusted-checkout.yaml) | yaml | ERROR | LLM04:2026 | ASI05, ASI04 | — |
| [`gha-ai-agent-untrusted-trigger`](../rules/agent-config/permissions/gha-ai-agent-untrusted-trigger.yaml) | yaml | ERROR | LLM01:2026 | ASI01, ASI05 | — |
| [`kilo-opencode-permission-allow`](../rules/agent-config/permissions/kilo-opencode-permission-allow.yaml) | regex | ERROR | LLM03:2026 | ASI02, ASI05 | MCP02:2025 |
| [`kilo-opencode-permission-allow-env`](../rules/agent-config/permissions/kilo-opencode-permission-allow-env.yaml) | regex | ERROR | LLM03:2026 | ASI02, ASI05 | MCP02:2025 |
| [`kilo-opencode-permission-allow-md`](../rules/agent-config/permissions/kilo-opencode-permission-allow-md.yaml) | regex | ERROR | LLM03:2026 | ASI02, ASI05 | MCP02:2025 |
| [`kilo-opencode-permission-allow-modes`](../rules/agent-config/permissions/kilo-opencode-permission-allow-modes.yaml) | regex | INFO | LLM03:2026 | ASI02, ASI05 | MCP02:2025 |
| [`mcp-config-auto-approve`](../rules/agent-config/permissions/mcp-config-auto-approve.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-config-auto-approve-toml`](../rules/agent-config/permissions/mcp-config-auto-approve-toml.yaml) | regex | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-config-ephemeral-remote-host`](../rules/agent-config/supply-chain/mcp-config-ephemeral-remote-host.yaml) | json | WARNING | LLM04:2026 | ASI04 | MCP09:2025, MCP04:2025 |
| [`mcp-config-ephemeral-remote-host-subagent`](../rules/agent-config/supply-chain/mcp-config-ephemeral-remote-host-subagent.yaml) | generic | WARNING | LLM04:2026 | ASI04 | MCP09:2025, MCP04:2025 |
| [`mcp-config-ephemeral-remote-host-toml`](../rules/agent-config/supply-chain/mcp-config-ephemeral-remote-host-toml.yaml) | regex | WARNING | LLM04:2026 | ASI04 | MCP09:2025, MCP04:2025 |
| [`mcp-config-ephemeral-remote-host-workspace`](../rules/agent-config/supply-chain/mcp-config-ephemeral-remote-host-workspace.yaml) | regex | WARNING | LLM04:2026 | ASI04 | MCP09:2025, MCP04:2025 |
| [`mcp-config-ephemeral-remote-host-yaml`](../rules/agent-config/supply-chain/mcp-config-ephemeral-remote-host-yaml.yaml) | yaml | WARNING | LLM04:2026 | ASI04 | MCP09:2025, MCP04:2025 |
| [`mcp-config-hidden-path-command`](../rules/agent-config/supply-chain/mcp-config-hidden-path-command.yaml) | json | WARNING | LLM04:2026 | ASI04 | MCP04:2025, MCP09:2025 |
| [`mcp-config-hidden-path-command-subagent`](../rules/agent-config/supply-chain/mcp-config-hidden-path-command-subagent.yaml) | generic | WARNING | LLM04:2026 | ASI04 | MCP04:2025, MCP09:2025 |
| [`mcp-config-hidden-path-command-toml`](../rules/agent-config/supply-chain/mcp-config-hidden-path-command-toml.yaml) | regex | WARNING | LLM04:2026 | ASI04 | MCP04:2025, MCP09:2025 |
| [`mcp-config-hidden-path-command-workspace`](../rules/agent-config/supply-chain/mcp-config-hidden-path-command-workspace.yaml) | regex | WARNING | LLM04:2026 | ASI04 | MCP04:2025, MCP09:2025 |
| [`mcp-config-hidden-path-command-yaml`](../rules/agent-config/supply-chain/mcp-config-hidden-path-command-yaml.yaml) | yaml | WARNING | LLM04:2026 | ASI04 | MCP04:2025, MCP09:2025 |
| [`mcp-config-paas-remote-host`](../rules/agent-config/supply-chain/mcp-config-paas-remote-host.yaml) | json | INFO | LLM04:2026 | ASI04 | MCP09:2025, MCP04:2025 |
| [`mcp-config-paas-remote-host-subagent`](../rules/agent-config/supply-chain/mcp-config-paas-remote-host-subagent.yaml) | generic | INFO | LLM04:2026 | ASI04 | MCP09:2025, MCP04:2025 |
| [`mcp-config-paas-remote-host-toml`](../rules/agent-config/supply-chain/mcp-config-paas-remote-host-toml.yaml) | regex | INFO | LLM04:2026 | ASI04 | MCP09:2025, MCP04:2025 |
| [`mcp-config-paas-remote-host-workspace`](../rules/agent-config/supply-chain/mcp-config-paas-remote-host-workspace.yaml) | regex | INFO | LLM04:2026 | ASI04 | MCP09:2025, MCP04:2025 |
| [`mcp-config-paas-remote-host-yaml`](../rules/agent-config/supply-chain/mcp-config-paas-remote-host-yaml.yaml) | yaml | INFO | LLM04:2026 | ASI04 | MCP09:2025, MCP04:2025 |
| [`mcp-config-plaintext-secret`](../rules/agent-config/secrets/mcp-config-plaintext-secret.yaml) | json | ERROR | LLM02:2026 | ASI03 | MCP01:2025 |
| [`mcp-config-plaintext-secret-subagent`](../rules/agent-config/secrets/mcp-config-plaintext-secret-subagent.yaml) | generic | ERROR | LLM02:2026 | ASI03 | MCP01:2025 |
| [`mcp-config-plaintext-secret-toml`](../rules/agent-config/secrets/mcp-config-plaintext-secret-toml.yaml) | regex | ERROR | LLM02:2026 | ASI03 | MCP01:2025 |
| [`mcp-config-plaintext-secret-workspace`](../rules/agent-config/secrets/mcp-config-plaintext-secret-workspace.yaml) | regex | ERROR | LLM02:2026 | ASI03 | MCP01:2025 |
| [`mcp-config-plaintext-secret-yaml`](../rules/agent-config/secrets/mcp-config-plaintext-secret-yaml.yaml) | yaml | ERROR | LLM02:2026 | ASI03 | MCP01:2025 |
| [`mcp-config-unpinned-package`](../rules/agent-config/supply-chain/mcp-config-unpinned-package.yaml) | json | WARNING | LLM04:2026 | ASI04 | MCP04:2025 |
| [`mcp-config-unpinned-package-subagent`](../rules/agent-config/supply-chain/mcp-config-unpinned-package-subagent.yaml) | generic | WARNING | LLM04:2026 | ASI04 | MCP04:2025 |
| [`mcp-config-unpinned-package-toml`](../rules/agent-config/supply-chain/mcp-config-unpinned-package-toml.yaml) | regex | WARNING | LLM04:2026 | ASI04 | MCP04:2025 |
| [`mcp-config-unpinned-package-workspace`](../rules/agent-config/supply-chain/mcp-config-unpinned-package-workspace.yaml) | regex | WARNING | LLM04:2026 | ASI04 | MCP04:2025 |
| [`mcp-config-unpinned-package-yaml`](../rules/agent-config/supply-chain/mcp-config-unpinned-package-yaml.yaml) | yaml | WARNING | LLM04:2026 | ASI04 | MCP04:2025 |
| [`mcp-container-host-root-mount`](../rules/agent-config/permissions/mcp-container-host-root-mount.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-container-host-root-mount-cline`](../rules/agent-config/permissions/mcp-container-host-root-mount-cline.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-container-host-root-mount-gemini`](../rules/agent-config/permissions/mcp-container-host-root-mount-gemini.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-container-host-root-mount-literal`](../rules/agent-config/permissions/mcp-container-host-root-mount-literal.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-container-host-root-mount-subagent`](../rules/agent-config/permissions/mcp-container-host-root-mount-subagent.yaml) | generic | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-container-host-root-mount-toml`](../rules/agent-config/permissions/mcp-container-host-root-mount-toml.yaml) | regex | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-container-host-root-mount-vscode`](../rules/agent-config/permissions/mcp-container-host-root-mount-vscode.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-container-host-root-mount-workspace`](../rules/agent-config/permissions/mcp-container-host-root-mount-workspace.yaml) | regex | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-container-host-root-mount-yaml`](../rules/agent-config/permissions/mcp-container-host-root-mount-yaml.yaml) | yaml | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-filesystem-root-too-broad`](../rules/agent-config/permissions/mcp-filesystem-root-too-broad.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-filesystem-root-too-broad-cline`](../rules/agent-config/permissions/mcp-filesystem-root-too-broad-cline.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-filesystem-root-too-broad-gemini`](../rules/agent-config/permissions/mcp-filesystem-root-too-broad-gemini.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-filesystem-root-too-broad-literal`](../rules/agent-config/permissions/mcp-filesystem-root-too-broad-literal.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-filesystem-root-too-broad-subagent`](../rules/agent-config/permissions/mcp-filesystem-root-too-broad-subagent.yaml) | generic | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-filesystem-root-too-broad-toml`](../rules/agent-config/permissions/mcp-filesystem-root-too-broad-toml.yaml) | regex | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-filesystem-root-too-broad-vscode`](../rules/agent-config/permissions/mcp-filesystem-root-too-broad-vscode.yaml) | json | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-filesystem-root-too-broad-workspace`](../rules/agent-config/permissions/mcp-filesystem-root-too-broad-workspace.yaml) | regex | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`mcp-filesystem-root-too-broad-yaml`](../rules/agent-config/permissions/mcp-filesystem-root-too-broad-yaml.yaml) | yaml | WARNING | LLM03:2026 | ASI02 | MCP02:2025 |
| [`project-mcp-server-no-prompt`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt.yaml) | json | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-continue`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-continue.yaml) | json | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-copilot-cli`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-copilot-cli.yaml) | json | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-devcontainer`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-devcontainer.yaml) | json | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-gemini`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-gemini.yaml) | json | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-kiro`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-kiro.yaml) | json | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-opencode`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-opencode.yaml) | regex | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-roo`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-roo.yaml) | json | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-subagent`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-subagent.yaml) | regex | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-toml`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-toml.yaml) | regex | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-workspace`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-workspace.yaml) | regex | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-yaml`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-yaml.yaml) | yaml | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`project-mcp-server-no-prompt-zed`](../rules/agent-config/supply-chain/project-mcp-server-no-prompt-zed.yaml) | json | WARNING | LLM04:2026 | ASI04, ASI05 | MCP04:2025, MCP09:2025 |
| [`subagent-permission-mode`](../rules/agent-config/permissions/subagent-permission-mode.yaml) | regex | WARNING | LLM03:2026 | ASI03, ASI02 | — |
| [`subagent-permission-mode-cli`](../rules/agent-config/permissions/subagent-permission-mode-cli.yaml) | regex | WARNING | LLM03:2026 | ASI03, ASI02 | — |
| [`subagent-permission-mode-qwen`](../rules/agent-config/permissions/subagent-permission-mode-qwen.yaml) | regex | ERROR | LLM03:2026 | ASI03, ASI05 | — |
| [`vscode-chat-auto-approve`](../rules/agent-config/permissions/vscode-chat-auto-approve.yaml) | regex | ERROR | LLM03:2026 | ASI02, ASI05 | — |
| [`vscode-task-runs-automatically`](../rules/agent-config/auto-execution/vscode-task-runs-automatically.yaml) | regex | WARNING | LLM04:2026 | ASI05 | — |
