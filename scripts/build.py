#!/usr/bin/env python3
"""Validate rule metadata and regenerate rules.yaml, docs/rules.md, and docs/owasp-coverage.md.

Also regenerates the rule files that scripts/gen_mcp_unpinned.py,
scripts/gen_mcp_plaintext_secret.py, scripts/gen_mcp_remote_host.py,
scripts/gen_secret_in_system_prompt.py, scripts/gen_mcp_hidden_path.py,
scripts/gen_mcp_auto_approve.py, scripts/gen_user_input_in_system_prompt.py,
scripts/gen_client_message_roles.py, scripts/gen_mcp_filesystem_root.py,
scripts/gen_kilo_opencode_permission.py, scripts/gen_mcp_hidden_unicode.py,
scripts/gen_agent_hooks.py, scripts/gen_fetched_content_in_system_prompt.py,
scripts/gen_user_content_to_fine_tuning.py, scripts/gen_vector_filter_from_user_input.py,
scripts/gen_agent_memory_write_untrusted.py, scripts/gen_tool_returns_environment.py,
scripts/gen_project_mcp_no_prompt.py, scripts/gen_llm_max_tokens_from_user_input.py,
scripts/gen_agent_settings_endpoint.py and scripts/gen_langchain_load_untrusted_input.py write
from shared regexes and paths, so a hand edit to one of them is overwritten here and caught by
--check.

Usage:
    python3 scripts/build.py           # validate, then write generated files
    python3 scripts/build.py --check   # validate, and fail if generated files are stale
"""

from __future__ import annotations

import copy
import re
import sys
from pathlib import Path

import yaml

import gen_agent_hooks
import gen_agent_settings_endpoint
import gen_agent_memory_write_untrusted
import gen_client_message_roles
import gen_fetched_content_in_system_prompt
import gen_kilo_opencode_permission
import gen_langchain_load_untrusted_input
import gen_llm_max_tokens_from_user_input
import gen_mcp_auto_approve
import gen_mcp_filesystem_root
import gen_mcp_hidden_path
import gen_mcp_hidden_unicode
import gen_mcp_plaintext_secret
import gen_mcp_remote_host
import gen_mcp_unpinned
import gen_project_mcp_no_prompt
import gen_secret_in_system_prompt
import gen_tool_returns_environment
import gen_user_content_to_fine_tuning
import gen_user_input_in_system_prompt
import gen_vector_filter_from_user_input

# Each generator's render() maps a rule file to its content; build.py writes and checks them.
GENERATORS = (gen_mcp_unpinned, gen_mcp_plaintext_secret, gen_mcp_remote_host,
              gen_secret_in_system_prompt, gen_mcp_hidden_path, gen_user_input_in_system_prompt,
              gen_mcp_auto_approve, gen_client_message_roles, gen_mcp_filesystem_root,
              gen_kilo_opencode_permission, gen_mcp_hidden_unicode, gen_agent_hooks,
              gen_fetched_content_in_system_prompt, gen_user_content_to_fine_tuning,
              gen_vector_filter_from_user_input, gen_agent_memory_write_untrusted,
              gen_tool_returns_environment, gen_project_mcp_no_prompt,
              gen_llm_max_tokens_from_user_input, gen_agent_settings_endpoint,
              gen_langchain_load_untrusted_input)

ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = ROOT / "rules"
TAXONOMY = ROOT / "taxonomy" / "owasp.yaml"
AISVS = ROOT / "taxonomy" / "aisvs.yaml"
ATLAS = ROOT / "taxonomy" / "atlas.yaml"
AGGREGATE = ROOT / "rules.yaml"
RULES_DOC = ROOT / "docs" / "rules.md"
COVERAGE_DOC = ROOT / "docs" / "owasp-coverage.md"

PACK_CATEGORIES = {
    "ai-code": "AI application code",
    "mcp-server": "MCP servers",
    "agent-config": "Agent instructions and config",
}
OWASP_FIELDS = ("owasp-llm", "owasp-agentic", "owasp-mcp")
REQUIRED_METADATA = ("category", "subcategory", "pack-category", "owasp-llm", "cwe",
                     "confidence", "likelihood", "impact", "technology", "references")
LEVELS = {"HIGH", "MEDIUM", "LOW"}
SEVERITIES = {"ERROR", "WARNING", "INFO"}
CWE_RE = re.compile(r"^CWE-\d+: .+")
# Rules that scan the same set of files keep identical `paths`, so a file added to one is added
# to all. Edit every rule in a group together; build.py fails when they differ.
SHARED_PATHS = {
    "agent instruction files": (
        "agent-rules-silent-command-directive",
        "agent-instruction-suppresses-security-findings",
        "agent-instruction-hidden-unicode",
    ),
    "agent CLI command lines": (
        "ai-cli-bypass-flag-invocation",
        "ai-cli-default-auto-approve",
        "agent-allowlist-network-exfil-commands-cli",
        "subagent-permission-mode-cli",
        "agent-allowlist-webfetch-any-domain-cli",
    ),
    # The MCP config families take their paths from gen_mcp_unpinned.py; these groups catch a
    # family that stops importing them.
    "MCP client config (JSON)": (
        "mcp-config-unpinned-package",
        "mcp-config-plaintext-secret",
        "mcp-config-ephemeral-remote-host",
        "mcp-config-paas-remote-host",
        "mcp-config-hidden-path-command",
        "mcp-config-auto-approve",
    ),
    # gen_mcp_filesystem_root.py splits the same JSON files by client (which variables each
    # expands) and checks that the groups cover JSON_PATHS; the two families share each group.
    "MCP JSON config, Claude Code and Copilot CLI": (
        "mcp-filesystem-root-too-broad",
        "mcp-container-host-root-mount",
    ),
    "MCP JSON config, VS Code and Cursor": (
        "mcp-filesystem-root-too-broad-vscode",
        "mcp-container-host-root-mount-vscode",
    ),
    "MCP JSON config, Cline, Windsurf and Roo Code": (
        "mcp-filesystem-root-too-broad-cline",
        "mcp-container-host-root-mount-cline",
    ),
    "MCP JSON config, Gemini CLI": (
        "mcp-filesystem-root-too-broad-gemini",
        "mcp-container-host-root-mount-gemini",
    ),
    "MCP JSON config, clients that expand nothing": (
        "mcp-filesystem-root-too-broad-literal",
        "mcp-container-host-root-mount-literal",
    ),
    "MCP client config (Continue YAML)": (
        "mcp-config-unpinned-package-yaml",
        "mcp-config-plaintext-secret-yaml",
        "mcp-config-ephemeral-remote-host-yaml",
        "mcp-config-paas-remote-host-yaml",
        "mcp-config-hidden-path-command-yaml",
        "mcp-filesystem-root-too-broad-yaml",
        "mcp-container-host-root-mount-yaml",
        "project-mcp-server-no-prompt-yaml",
    ),
    "MCP client config (Codex TOML)": (
        "mcp-config-unpinned-package-toml",
        "mcp-config-plaintext-secret-toml",
        "mcp-config-ephemeral-remote-host-toml",
        "mcp-config-paas-remote-host-toml",
        "mcp-config-hidden-path-command-toml",
        "mcp-config-auto-approve-toml",
        "mcp-filesystem-root-too-broad-toml",
        "mcp-container-host-root-mount-toml",
        "project-mcp-server-no-prompt-toml",
    ),
    # Claude Code subagent files: the MCP config families' -subagent rules and
    # subagent-permission-mode.
    "Claude Code subagent front matter": (
        "mcp-config-unpinned-package-subagent",
        "mcp-config-plaintext-secret-subagent",
        "mcp-config-ephemeral-remote-host-subagent",
        "mcp-config-paas-remote-host-subagent",
        "mcp-config-hidden-path-command-subagent",
        "project-mcp-server-no-prompt-subagent",
        "mcp-filesystem-root-too-broad-subagent",
        "subagent-permission-mode",
        "mcp-container-host-root-mount-subagent",
    ),
    "MCP client config (VS Code workspace files)": (
        "mcp-config-unpinned-package-workspace",
        "mcp-config-plaintext-secret-workspace",
        "mcp-config-ephemeral-remote-host-workspace",
        "mcp-config-paas-remote-host-workspace",
        "mcp-config-hidden-path-command-workspace",
        "project-mcp-server-no-prompt-workspace",
        "mcp-filesystem-root-too-broad-workspace",
        "mcp-container-host-root-mount-workspace",
    ),
    "GitHub Actions workflows": (
        "ai-cli-bypass-flag-invocation-gha",
        "gha-ai-agent-untrusted-trigger",
        "gha-ai-agent-trusts-untrusted-checkout",
        "gha-ai-agent-checkout-pr-head",
        "gha-ai-agent-open-to-non-writers",
    ),
    # gen_mcp_auto_approve.py writes the same list as claude-settings-unrestricted-shell's.
    "Claude Code settings permissions": (
        "claude-settings-unrestricted-shell",
        "claude-settings-mcp-auto-approve",
        "claude-settings-project-mcp-auto-start",
    ),
    "agent settings command keys": (
        "agent-settings-command-runs-local-script",
        "agent-settings-command-remote-exec",
    ),
    "agent hook files": (
        "agent-hook-runs-local-script",
        "agent-hook-remote-exec",
    ),
    "skill and subagent frontmatter": (
        "agent-frontmatter-command-runs-local-script",
        "agent-frontmatter-command-remote-exec",
        "claude-frontmatter-hook-auto-approves",
        # Scans the same skill/command bodies for ``!`cmd` `` / ```! load-time shell injection.
        "agent-skill-load-time-shell",
    ),
    "skill allowed-tools frontmatter": (
        "claude-skill-allowed-tools-auto-approve",
        "agent-allowlist-network-exfil-commands-skill",
        "agent-allowlist-webfetch-any-domain-skill",
    ),
    # gen_agent_settings_endpoint.py imports the opencode / Kilo path list from
    # gen_kilo_opencode_permission.py.
    "opencode and Kilo Code config files": (
        "kilo-opencode-permission-allow",
        "agent-settings-endpoint-override-opencode",
    ),
    "VS Code settings": (
        "vscode-chat-auto-approve",
        "agent-allowlist-network-exfil-commands-vscode",
        "agent-allowlist-webfetch-any-domain-vscode",
    ),
    # opencode and Kilo config files plus their agent and mode Markdown files.
    "opencode and Kilo permission allow lists": (
        "agent-allowlist-network-exfil-commands-opencode",
        "agent-allowlist-webfetch-any-domain-opencode",
    ),
    "docker compose files": (
        "mcp-server-bind-all-interfaces-config-compose",
        "vector-db-published-without-auth-compose",
        "mcp-container-host-root-mount-compose",
    ),
    "docker run command lines": (
        "mcp-server-bind-all-interfaces-config-docker-run",
        "vector-db-published-without-auth-docker-run",
    ),
}
# Regex rules that share a block of named groups (between the begin and end marker comments)
# keep it identical; build.py fails when the copies differ.
SHARED_REGEX = {
    # Which hosts count as remote for the vector database client rules.
    "vector DB remote host": (
        "vector-db-client-without-auth",
        "vector-db-client-without-auth-ts",
    ),
    # "Published on every host interface" for compose ports, and docker run command parsing.
    "compose published-port test": (
        "mcp-server-bind-all-interfaces-config-compose",
        "vector-db-published-without-auth-compose",
    ),
    "docker run command groups": (
        "mcp-server-bind-all-interfaces-config-docker-run",
        "vector-db-published-without-auth-docker-run",
    ),
    "docker run command start": (
        "mcp-server-bind-all-interfaces-config-docker-run",
        "vector-db-published-without-auth-docker-run",
    ),
    # Kubernetes Service exposure: LoadBalancer / NodePort, internal load balancers, source ranges.
    "kubernetes exposure groups": (
        "vector-db-published-without-auth-helm",
        "vector-db-published-without-auth-k8s",
    ),
    "shared command-position groups": (
        "ai-cli-bypass-flag-invocation",
        "ai-cli-default-auto-approve",
        "subagent-permission-mode-cli",
    ),
    "gha agent-CLI acting regex": (
        "gha-ai-agent-untrusted-trigger",
        "gha-ai-agent-checkout-pr-head",
    ),
    "claude-code-action acting test": (
        "gha-ai-agent-untrusted-trigger",
        "gha-ai-agent-open-to-non-writers",
    ),
    "run-gemini-cli acting test": (
        "gha-ai-agent-untrusted-trigger",
        "gha-ai-agent-checkout-pr-head",
    ),
    # Agent hooks (settings files and skill/subagent frontmatter) and Claude Code settings
    # commands judge a command string, and an exec-form program and argument, the same way.
    "repo-script command test": (
        "agent-hook-runs-local-script",
        "agent-settings-command-runs-local-script",
        "agent-frontmatter-command-runs-local-script",
    ),
    "remote download-and-run test": (
        "agent-hook-remote-exec",
        "agent-settings-command-remote-exec",
        "agent-frontmatter-command-remote-exec",
    ),
    "exec-form interpreters": (
        "agent-hook-runs-local-script",
        "agent-frontmatter-command-runs-local-script",
    ),
    "exec-form script argument": (
        "agent-hook-runs-local-script",
        "agent-frontmatter-command-runs-local-script",
    ),
    "exec-form shells": (
        "agent-hook-remote-exec",
        "agent-frontmatter-command-remote-exec",
    ),
    "exec-form package runners": (
        "agent-hook-remote-exec",
        "agent-frontmatter-command-remote-exec",
    ),
    "exec-form remote package spec": (
        "agent-hook-remote-exec",
        "agent-frontmatter-command-remote-exec",
    ),
    "MCP tool-description indicators": (
        "mcp-tool-description-instructions",
        "mcp-tool-description-instructions-ts",
    ),
    # Invisible characters and their thresholds; gen_mcp_hidden_unicode.py copies the block from
    # agent-instruction-hidden-unicode into the MCP description rules.
    "hidden Unicode characters": (
        "agent-instruction-hidden-unicode",
        "mcp-tool-description-hidden-unicode",
        "mcp-tool-description-hidden-unicode-ts",
    ),
    # Mermaid and KaTeX settings written as JavaScript text, in markup files and in Python
    # strings. Each rule repeats the block in its Mermaid and its KaTeX regex.
    "mermaid/katex config text": (
        "mermaid-or-katex-unsafe-config-markup",
        "mermaid-or-katex-unsafe-config-py",
    ),
    # Cursor autoRun classifier overrides: the rule repeats the block in its
    # allow_instructions and its block_instructions regex.
    "autoRun override test": (
        "cursor-permissions-allow-instructions",
    ),
    # The network programs an agent allow list shouldn't pre-approve, in every client's format.
    "network exfil programs": (
        "agent-allowlist-network-exfil-commands",
        "agent-allowlist-network-exfil-commands-cli",
        "agent-allowlist-network-exfil-commands-codex",
        "agent-allowlist-network-exfil-commands-opencode",
        "agent-allowlist-network-exfil-commands-skill",
        "agent-allowlist-network-exfil-commands-vscode",
        "agent-allowlist-network-exfil-commands-py",
        "agent-allowlist-network-exfil-commands-ts",
        "agent-allowlist-network-exfil-commands-cli-py",
        "agent-allowlist-network-exfil-commands-cli-ts",
    ),
    # Host patterns a fetch allow rule shouldn't cover: every host, a wildcard in the
    # registrable label, or a tunnel or free hosting domain.
    "web fetch any host": (
        "agent-allowlist-webfetch-any-domain",
        "agent-allowlist-webfetch-any-domain-cli",
        "agent-allowlist-webfetch-any-domain-cursor",
        "agent-allowlist-webfetch-any-domain-qwen",
        "agent-allowlist-webfetch-any-domain-skill",
        "agent-allowlist-webfetch-any-domain-vscode",
        "agent-allowlist-webfetch-any-domain-py",
        "agent-allowlist-webfetch-any-domain-ts",
        "agent-allowlist-webfetch-any-domain-cli-py",
        "agent-allowlist-webfetch-any-domain-cli-ts",
    ),
    # The "command does something dangerous" test shared by the load-time shell injection
    # rules (Claude Code ``!`cmd` ``/```!, opencode/Kilo ``!`cmd` ``, Gemini/Qwen `!{...}`).
    # agent-skill-load-time-shell holds two copies (block and inline branches).
    "load-time shell danger command": (
        "agent-skill-load-time-shell",
        "agent-skill-load-time-shell-toml",
        "agent-skill-load-time-shell-opencode",
        "agent-skill-load-time-shell-opencode-skill",
    ),
}
# Taint rules that share a block keep identical copies of it; build.py fails when they
# differ. Each entry names the rules, the field, and a slice of it: rules that read the same
# untrusted input share `pattern-sources` (plus any leading `pattern-sanitizers` that are part
# of the source, such as a schema that only admits safe values), and rules that guard the same
# sink with different sources share `pattern-sinks` and the remaining sanitizers. The field can
# also be a path into nested operators, given per rule when the rules nest the block
# differently: {"rule-id": ("pattern-either", 0, "patterns"), "other-id": ("patterns",)}.
SHARED_BLOCKS = {
    "MCP tool sources (Python)": (
        ("mcp-tool-arg-to-shell", "mcp-tool-arg-option-injection", "mcp-tool-arg-to-sql"),
        "pattern-sources", None, None),
    "agent tool sources (Python)": (
        ("agent-tool-arg-to-shell", "agent-tool-arg-option-injection", "agent-tool-arg-to-sql"),
        "pattern-sources", None, None),
    "MCP tool sources (TypeScript)": (
        ("mcp-tool-arg-to-shell-ts", "mcp-tool-arg-option-injection-ts", "mcp-tool-arg-to-sql-ts"),
        "pattern-sources", None, None),
    "MCP tool schema sanitizer (TypeScript)": (
        ("mcp-tool-arg-to-shell-ts", "mcp-tool-arg-option-injection-ts", "mcp-tool-arg-to-sql-ts"),
        "pattern-sanitizers", 0, 1),
    "MCP tool sources (Go)": (
        ("mcp-tool-arg-to-shell-go", "mcp-tool-arg-option-injection-go", "mcp-tool-arg-to-sql-go"),
        "pattern-sources", None, None),
    "MCP tool propagators (Go)": (
        ("mcp-tool-arg-to-shell-go", "mcp-tool-arg-option-injection-go", "mcp-tool-arg-to-sql-go"),
        "pattern-propagators", None, None),
    # The request's typed reads and the literal-label switch arm.
    "MCP tool request sanitizers (Go)": (
        ("mcp-tool-arg-to-shell-go", "mcp-tool-arg-option-injection-go", "mcp-tool-arg-to-sql-go"),
        "pattern-sanitizers", 0, 2),
    "tool-argument value sanitizers (Go)": (
        ("mcp-tool-arg-to-shell-go", "mcp-tool-arg-to-sql-go"), "pattern-sanitizers", 2, 6),
    "agent tool sources (TypeScript)": (
        ("agent-tool-arg-to-shell-ts", "agent-tool-arg-option-injection-ts", "agent-tool-arg-to-sql-ts"),
        "pattern-sources", None, None),
    "agent tool schema sanitizer (TypeScript)": (
        ("agent-tool-arg-to-shell-ts", "agent-tool-arg-option-injection-ts", "agent-tool-arg-to-sql-ts"),
        "pattern-sanitizers", 0, 1),
    "tool-argument shell sinks (Python)": (
        ("mcp-tool-arg-to-shell", "agent-tool-arg-to-shell"), "pattern-sinks", None, None),
    "tool-argument shell sanitizers (Python)": (
        ("mcp-tool-arg-to-shell", "agent-tool-arg-to-shell"), "pattern-sanitizers", None, None),
    "tool-argument option sinks (Python)": (
        ("mcp-tool-arg-option-injection", "agent-tool-arg-option-injection"), "pattern-sinks", None, None),
    "tool-argument option sanitizers (Python)": (
        ("mcp-tool-arg-option-injection", "agent-tool-arg-option-injection"), "pattern-sanitizers", None, None),
    "tool-argument shell sinks (TypeScript)": (
        ("mcp-tool-arg-to-shell-ts", "agent-tool-arg-to-shell-ts"), "pattern-sinks", None, None),
    "tool-argument shell sanitizers (TypeScript)": (
        ("mcp-tool-arg-to-shell-ts", "agent-tool-arg-to-shell-ts"), "pattern-sanitizers", 1, None),
    "tool-argument option sinks (TypeScript)": (
        ("mcp-tool-arg-option-injection-ts", "agent-tool-arg-option-injection-ts"), "pattern-sinks", None, None),
    "tool-argument option sanitizers (TypeScript)": (
        ("mcp-tool-arg-option-injection-ts", "agent-tool-arg-option-injection-ts"), "pattern-sanitizers", 1, None),
    "interpreter and write-then-run sinks (Python)": (
        ("llm-output-to-code-execution", "mcp-tool-arg-to-shell"), "pattern-sinks", -2, None),
    "SQL sinks (Python)": (
        ("llm-output-to-sql", "mcp-tool-arg-to-sql", "agent-tool-arg-to-sql"), "pattern-sinks", None, None),
    "SQL sanitizers (Python)": (
        ("llm-output-to-sql", "mcp-tool-arg-to-sql", "agent-tool-arg-to-sql"), "pattern-sanitizers", 0, 4),
    "SQL sinks (TypeScript)": (
        ("llm-output-to-sql-ts", "mcp-tool-arg-to-sql-ts", "agent-tool-arg-to-sql-ts"),
        "pattern-sinks", None, None),
    "SQL sanitizers (TypeScript)": (
        ("llm-output-to-sql-ts", "mcp-tool-arg-to-sql-ts", "agent-tool-arg-to-sql-ts"),
        "pattern-sanitizers", -6, None),
    "tool-argument SQL sanitizers (TypeScript)": (
        ("mcp-tool-arg-to-sql-ts", "agent-tool-arg-to-sql-ts"), "pattern-sanitizers", 1, None),
    "model-output sources (Python)": (
        ("llm-output-to-code-execution", "llm-output-to-sql", "llm-output-as-template"),
        "pattern-sources", None, None),
    "model-output sources (Python, HTML rule)": (
        ("llm-output-to-code-execution", "llm-output-rendered-as-html"), "pattern-sources", 0, 18),
    "model-output sources (TypeScript)": (
        ("llm-output-to-html-ts", "llm-output-to-code-execution-ts", "llm-output-to-sql-ts"),
        "pattern-sources", 0, 21),
    "model-output propagators (TypeScript)": (
        ("llm-output-to-html-ts", "llm-output-to-code-execution-ts", "llm-output-to-sql-ts"),
        "pattern-propagators", 0, 2),
    "model-output code-execution sinks (TypeScript)": (
        ("mcp-tool-arg-to-shell-ts", "llm-output-to-code-execution-ts"), "pattern-sinks", None, None),
    "model-output code-execution sanitizers (TypeScript)": (
        ("mcp-tool-arg-to-shell-ts", "llm-output-to-code-execution-ts"), "pattern-sanitizers", 1, None),
    "model-output sources (TypeScript, with agent SDKs)": (
        ("llm-output-to-code-execution-ts", "llm-output-to-vm2-sandbox", "llm-output-to-sql-ts",
         "llm-output-as-template-ts"),
        "pattern-sources", None, None),
    "model-output propagators (TypeScript, with agent SDKs)": (
        ("llm-output-to-code-execution-ts", "llm-output-to-vm2-sandbox", "llm-output-to-sql-ts",
         "llm-output-as-template-ts"),
        "pattern-propagators", None, None),
    "model-output value sanitizers (TypeScript)": (
        ("llm-output-to-code-execution-ts", "llm-output-to-vm2-sandbox", "llm-output-to-sql-ts",
         "llm-output-as-template-ts"),
        "pattern-sanitizers", 0, 6),
    "model-output sanitizers (TypeScript, code execution)": (
        ("llm-output-to-code-execution-ts", "llm-output-to-vm2-sandbox"), "pattern-sanitizers", None, None),
    "MCP HTTP import gate (TypeScript)": (
        ("mcp-server-exposed-without-auth-ts", "mcp-http-transport-without-host-validation-ts"), "patterns", 0, 1),
    "HTTP authentication signals (TypeScript)": (
        ("mcp-server-exposed-without-auth-ts", "mcp-http-transport-without-host-validation-ts",
         "a2a-server-without-auth-ts"), "patterns", -7, None),
    # The local-script rule adds a second branch (a Cursor worktree setup script path), so its
    # copy of the key list sits one level down.
    "agent settings keys that run a command": (
        ("agent-settings-command-runs-local-script", "agent-settings-command-remote-exec"),
        {"agent-settings-command-runs-local-script": ("pattern-either", 0, "patterns"),
         "agent-settings-command-remote-exec": ("patterns",)}, 0, 1),
    "model-output sources (TypeScript, rendering)": (
        ("llm-output-to-html-ts", "llm-markdown-remote-image-render"), "pattern-sources", None, None),
    "model-output propagators (TypeScript, rendering)": (
        ("llm-output-to-html-ts", "llm-markdown-remote-image-render"), "pattern-propagators", None, None),
    "model-output metadata sanitizers (TypeScript, rendering)": (
        ("llm-output-to-html-ts", "llm-markdown-remote-image-render"), "pattern-sanitizers", -2, None),
    "model-output sources (Python, rendering)": (
        ("llm-output-rendered-as-html", "llm-markdown-remote-image-render-py"), "pattern-sources", None, None),
    "model-output propagators (Python, rendering)": (
        ("llm-output-rendered-as-html", "llm-markdown-remote-image-render-py"), "pattern-propagators", None, None),
    "model-output non-model-value sanitizers (Python, rendering)": (
        ("llm-output-rendered-as-html", "llm-markdown-remote-image-render-py"), "pattern-sanitizers", -10, None),
    # gen_user_input_in_system_prompt.py and gen_fetched_content_in_system_prompt.py import these
    # from gen_secret_in_system_prompt.py; the user-input rules add LangChain template sinks
    # after them, which the fetched-content rules import in turn.
    "system-prompt sinks (Python)": (
        ("secret-in-system-prompt", "user-input-in-system-prompt", "fetched-content-in-system-prompt"),
        "pattern-sinks", 0, 10),
    "system-prompt sinks (TypeScript)": (
        ("secret-in-system-prompt-ts", "user-input-in-system-prompt-ts", "fetched-content-in-system-prompt-ts"),
        "pattern-sinks", 0, 7),
    "LangChain template sinks (Python)": (
        ("user-input-in-system-prompt", "fetched-content-in-system-prompt"), "pattern-sinks", 10, 14),
    "LangChain template sinks (TypeScript)": (
        ("user-input-in-system-prompt-ts", "fetched-content-in-system-prompt-ts"), "pattern-sinks", 7, 11),
    # gen_agent_memory_write_untrusted.py imports the fetched-content rules' sources (all but the
    # stuff-documents template source, which comes after them), propagators, and value sanitizer.
    "fetched-content sources (Python)": (
        ("fetched-content-in-system-prompt", "agent-memory-write-untrusted"), "pattern-sources", 0,
        gen_fetched_content_in_system_prompt.PY_SHARED_SOURCE_COUNT),
    "fetched-content sources (TypeScript)": (
        ("fetched-content-in-system-prompt-ts", "agent-memory-write-untrusted-ts"), "pattern-sources", 0,
        gen_fetched_content_in_system_prompt.TS_SHARED_SOURCE_COUNT),
    "fetched-content propagators (TypeScript)": (
        ("fetched-content-in-system-prompt-ts", "agent-memory-write-untrusted-ts"), "pattern-propagators", None, None),
    "fetched-content value sanitizers (Python)": (
        ("fetched-content-in-system-prompt", "agent-memory-write-untrusted"), "pattern-sanitizers", 0, 1),
    "fetched-content value sanitizers (TypeScript)": (
        ("fetched-content-in-system-prompt-ts", "agent-memory-write-untrusted-ts"), "pattern-sanitizers", 0, 1),
    # gen_client_message_roles.py, gen_user_content_to_fine_tuning.py, and
    # gen_langchain_load_untrusted_input.py import these from
    # gen_user_input_in_system_prompt.py; the client-message-roles rules add a message-list label
    # and role sanitizers after them.
    "request-data sources (Python)": (
        ("user-input-in-system-prompt", "client-message-roles-with-tools-py", "user-content-to-fine-tuning",
         "vector-filter-from-user-input", "llm-max-tokens-from-user-input", "langchain-load-untrusted-input"),
        "pattern-sources", 0, 3),
    "request-data sanitizers (Python)": (
        ("user-input-in-system-prompt", "client-message-roles-with-tools-py", "user-content-to-fine-tuning",
         "langchain-load-untrusted-input"),
        "pattern-sanitizers", 0, 7),
    "request-data sources (TypeScript)": (
        ("user-input-in-system-prompt-ts", "client-message-roles-with-tools", "user-content-to-fine-tuning-ts",
         "vector-filter-from-user-input-ts", "llm-max-tokens-from-user-input-ts", "langchain-load-untrusted-input-ts"),
        "pattern-sources", 0, 6),
    "request-data sanitizers (TypeScript)": (
        ("user-input-in-system-prompt-ts", "client-message-roles-with-tools", "user-content-to-fine-tuning-ts",
         "langchain-load-untrusted-input-ts"),
        "pattern-sanitizers", 0, 7),
    # gen_vector_filter_from_user_input.py imports the sanitizers before the lookup sanitizer,
    # which would clear the vector-store calls the vector-filter rules report.
    "request-data value sanitizers (Python)": (
        ("user-input-in-system-prompt", "vector-filter-from-user-input"), "pattern-sanitizers", 0, 6),
    "request-data value sanitizers (TypeScript)": (
        ("user-input-in-system-prompt-ts", "vector-filter-from-user-input-ts"), "pattern-sanitizers", 0, 6),
    # gen_llm_max_tokens_from_user_input.py imports the allowlist and format checks only: the
    # number-typed sanitizers after them would clear the values the max-tokens rules report.
    "request-data allowlist sanitizers (Python)": (
        ("user-input-in-system-prompt", "llm-max-tokens-from-user-input"), "pattern-sanitizers", 0, 3),
    "request-data allowlist sanitizers (TypeScript)": (
        ("user-input-in-system-prompt-ts", "llm-max-tokens-from-user-input-ts"), "pattern-sanitizers", 0, 3),
    # The Java rules: the three model-output rules read the same Spring AI and LangChain4j
    # sources, all four carry taint through lambdas the same way and share the value
    # sanitizers, and the output rules share the response-metadata sanitizer after them.
    "model-output sources (Java)": (
        ("llm-output-to-code-execution-java", "llm-output-to-sql-java", "llm-output-to-html-java"),
        "pattern-sources", None, None),
    "lambda propagators (Java)": (
        ("llm-output-to-code-execution-java", "llm-output-to-sql-java", "llm-output-to-html-java",
         "user-input-in-system-prompt-java"),
        "pattern-propagators", None, None),
    "value sanitizers (Java)": (
        ("llm-output-to-code-execution-java", "llm-output-to-sql-java", "llm-output-to-html-java",
         "user-input-in-system-prompt-java"),
        "pattern-sanitizers", 0, 5),
    "model-output metadata sanitizer (Java)": (
        ("llm-output-to-code-execution-java", "llm-output-to-sql-java", "llm-output-to-html-java"),
        "pattern-sanitizers", 5, 6),
    # The C# rules: the three model-output rules read the same Semantic Kernel,
    # Microsoft.Extensions.AI, and OpenAI .NET sources, all four carry taint through lambdas
    # the same way and share the value sanitizers, and the output rules share the
    # response-metadata sanitizer after them.
    "model-output sources (C#)": (
        ("llm-output-to-code-execution-csharp", "llm-output-to-sql-csharp", "llm-output-to-html-csharp"),
        "pattern-sources", None, None),
    "lambda propagators (C#)": (
        ("llm-output-to-code-execution-csharp", "llm-output-to-sql-csharp", "llm-output-to-html-csharp",
         "user-input-in-system-prompt-csharp"),
        "pattern-propagators", None, None),
    "value sanitizers (C#)": (
        ("llm-output-to-code-execution-csharp", "llm-output-to-sql-csharp", "llm-output-to-html-csharp",
         "user-input-in-system-prompt-csharp"),
        "pattern-sanitizers", 0, 8),
    "model-output metadata sanitizer (C#)": (
        ("llm-output-to-code-execution-csharp", "llm-output-to-sql-csharp", "llm-output-to-html-csharp"),
        "pattern-sanitizers", 8, 9),
    # gen_mcp_hidden_unicode.py copies the description surfaces from the instruction rules.
    "MCP description surfaces (Python)": (
        ("mcp-tool-description-instructions", "mcp-tool-description-hidden-unicode"), "patterns", 0, 1),
    "MCP description surfaces (TypeScript)": (
        ("mcp-tool-description-instructions-ts", "mcp-tool-description-hidden-unicode-ts"), "patterns", 0, 2),
    # gen_tool_returns_environment.py copies the tool-argument rules' sources and allowlist
    # sanitizers (the environment lookups a tool argument names), and their tool registration
    # shapes, which the returns-environment rules use as the sink's region.
    "tool-argument sources, returns-environment (Python)": (
        ("mcp-tool-arg-to-shell", "mcp-tool-returns-environment"), "pattern-sources", 0, 2),
    "agent tool-argument sources, returns-environment (Python)": (
        ("agent-tool-arg-to-shell", "agent-tool-returns-environment"), "pattern-sources", 0, 1),
    "tool-argument sources, returns-environment (TypeScript)": (
        ("mcp-tool-arg-to-shell-ts", "mcp-tool-returns-environment-ts"), "pattern-sources", 0, 1),
    "agent tool-argument sources, returns-environment (TypeScript)": (
        ("agent-tool-arg-to-shell-ts", "agent-tool-returns-environment-ts"), "pattern-sources", 0, 1),
    "tool-argument allowlist sanitizers, returns-environment (Python)": (
        ("mcp-tool-arg-to-shell", "agent-tool-arg-to-shell", "mcp-tool-returns-environment",
         "agent-tool-returns-environment"), "pattern-sanitizers", 0, 2),
    "tool-argument sanitizers, returns-environment (TypeScript)": (
        ("mcp-tool-arg-to-shell-ts", "mcp-tool-returns-environment-ts"), "pattern-sanitizers", 0, 3),
    "agent tool-argument sanitizers, returns-environment (TypeScript)": (
        ("agent-tool-arg-to-shell-ts", "agent-tool-returns-environment-ts"), "pattern-sanitizers", 0, 3),
    "MCP tool registration shapes (Python)": (
        ("mcp-tool-arg-to-shell", "mcp-tool-returns-environment"),
        {"mcp-tool-arg-to-shell": ("pattern-sources", 0, "patterns"),
         "mcp-tool-returns-environment": ("pattern-sinks", 0, "patterns")}, 0, 3),
    "MCP low-level call_tool handler shapes (Python)": (
        ("mcp-tool-arg-to-shell", "mcp-tool-returns-environment"),
        {"mcp-tool-arg-to-shell": ("pattern-sources", 1, "patterns"),
         "mcp-tool-returns-environment": ("pattern-sinks", 1, "patterns")}, 0, 1),
    "agent tool registration shapes (Python)": (
        ("agent-tool-arg-to-shell", "agent-tool-returns-environment"),
        {"agent-tool-arg-to-shell": ("pattern-sources", 0, "patterns"),
         "agent-tool-returns-environment": ("pattern-sinks", 0, "patterns")}, 0, 1),
}
GENERATED_NOTE = "<!-- Generated from rule metadata by scripts/build.py. Do not edit by hand. -->"


class Rule:
    def __init__(self, path: Path, body: dict):
        self.path = path
        self.body = body
        self.id = body.get("id", "")
        self.meta = body.get("metadata") or {}

    @property
    def rel(self) -> str:
        return self.path.relative_to(ROOT).as_posix()


def load_taxonomy() -> dict[str, dict]:
    taxonomy = yaml.safe_load(TAXONOMY.read_text())
    taxonomy["owasp-aisvs"] = yaml.safe_load(AISVS.read_text())
    taxonomy["mitre-atlas"] = yaml.safe_load(ATLAS.read_text())
    return taxonomy


def split_tag(tag: str) -> tuple[str, str]:
    ident, _, title = tag.partition(" - ")
    return ident.strip(), title.strip()


def find_fixtures(rule_path: Path) -> list[Path]:
    # opengrep test treats every <rule-id>.* file next to the rule as a fixture. YAML-language
    # rules use foo.test.yaml so the fixture is not mistaken for a rule file.
    return sorted(
        p for p in rule_path.parent.glob(f"{rule_path.stem}.*")
        if p != rule_path and (p.suffix not in (".yaml", ".yml")
                               or p.name.endswith((".test.yaml", ".test.yml")))
    )


def load_rules(errors: list[str]) -> list[Rule]:
    rules: list[Rule] = []
    for path in sorted(RULES_DIR.rglob("*.yaml")):
        if path.name.endswith(".test.yaml"):
            continue
        doc = yaml.safe_load(path.read_text())
        bodies = (doc or {}).get("rules") or []
        if len(bodies) != 1:
            errors.append(f"{path.relative_to(ROOT)}: expected exactly one rule per file")
            continue
        rules.append(Rule(path, bodies[0]))
    return rules


def validate(rules: list[Rule], taxonomy: dict, errors: list[str]) -> None:
    seen: dict[str, str] = {}
    for rule in rules:
        where = rule.rel
        if rule.id != rule.path.stem:
            errors.append(f"{where}: rule id {rule.id!r} must match the file name")
        if rule.id in seen:
            errors.append(f"{where}: duplicate rule id also in {seen[rule.id]}")
        seen[rule.id] = where
        if rule.body.get("severity") not in SEVERITIES:
            errors.append(f"{where}: severity must be one of {sorted(SEVERITIES)}")

        for key in REQUIRED_METADATA:
            if not rule.meta.get(key):
                errors.append(f"{where}: missing metadata.{key}")
        if "owasp" in rule.meta:
            errors.append(f"{where}: metadata.owasp is generated from the owasp-* fields; remove it")
        if rule.meta.get("category") != "security":
            errors.append(f"{where}: metadata.category must be 'security'")
        if rule.meta.get("pack-category") not in PACK_CATEGORIES:
            errors.append(f"{where}: metadata.pack-category must be one of {sorted(PACK_CATEGORIES)}")
        for key in ("confidence", "likelihood", "impact"):
            if rule.meta.get(key) not in LEVELS:
                errors.append(f"{where}: metadata.{key} must be HIGH, MEDIUM, or LOW")
        for cwe in rule.meta.get("cwe") or []:
            if not CWE_RE.match(str(cwe)):
                errors.append(f"{where}: CWE {cwe!r} must look like 'CWE-123: Title'")

        for field in OWASP_FIELDS:
            tags = rule.meta.get(field)
            if tags is None:
                continue
            if not isinstance(tags, list):
                errors.append(f"{where}: metadata.{field} must be a list")
                continue
            current = taxonomy[field]["current"]
            entries = {**taxonomy[field].get("previous", {}), **current}
            ids = []
            for tag in tags:
                ident, title = split_tag(str(tag))
                ids.append(ident)
                if ident not in entries:
                    errors.append(f"{where}: unknown {field} id {ident!r}")
                elif title != entries[ident]["title"]:
                    errors.append(f"{where}: {ident} title should be {entries[ident]['title']!r}")
            current_ids = [i for i in ids if i in current]
            if not current_ids:
                errors.append(f"{where}: metadata.{field} needs at least one id from the current edition")
            for ident in current_ids:
                compat = current[ident].get("compat")
                if compat and compat not in ids:
                    errors.append(f"{where}: {ident} requires compatibility tag {compat}")

        validate_aisvs(rule, taxonomy["owasp-aisvs"], errors)
        validate_atlas(rule, taxonomy["mitre-atlas"], errors)

        fixtures = find_fixtures(rule.path)
        if not fixtures:
            errors.append(f"{where}: missing fixture file next to the rule")
            continue
        # ruleid and ok cases must each appear somewhere in the rule's fixtures.
        text = "\n".join(f.read_text() for f in fixtures)
        if not re.search(rf"\bruleid:\s*{re.escape(rule.id)}\b", text):
            errors.append(f"{where}: fixtures need at least one 'ruleid: {rule.id}'")
        if not re.search(rf"\bok:\s*{re.escape(rule.id)}\b", text):
            errors.append(f"{where}: fixtures need at least one 'ok: {rule.id}'")


def validate_shared_paths(rules: list[Rule], errors: list[str]) -> None:
    by_id = {r.id: r for r in rules}
    for group, ids in SHARED_PATHS.items():
        missing = [i for i in ids if i not in by_id]
        if missing:
            errors.append(f"SHARED_PATHS[{group!r}] names unknown rules: {', '.join(missing)}")
            continue
        first = by_id[ids[0]]
        for other in (by_id[i] for i in ids[1:]):
            if other.body.get("paths") != first.body.get("paths"):
                errors.append(f"{other.rel}: paths differ from {first.rel}; the {group} rules "
                              "share one file list, so update them together")


def rule_strings(node) -> list[str]:
    # Every string in a rule body, so a shared block can sit in a nested metavariable-regex.
    if isinstance(node, str):
        return [node]
    if isinstance(node, dict):
        return [s for v in node.values() for s in rule_strings(v)]
    if isinstance(node, list):
        return [s for v in node for s in rule_strings(v)]
    return []


def shared_block(rule: Rule, group: str) -> str | None:
    # The begin marker is two comment lines (the second names the other rule) ending in "---".
    # A rule may hold several copies (one per regex); shared_block_copies checks they agree.
    copies = shared_block_copies(rule, group)
    return copies[0] if copies else None


def shared_block_copies(rule: Rule, group: str) -> list[str]:
    pattern = rf"# --- {re.escape(group)} \(begin\)[^\n]*\n[^\n]*---\n(.*?)# --- {re.escape(group)} \(end\) ---"
    return [m.group(1) for text in rule_strings(rule.body) for m in re.finditer(pattern, text, re.S)]


def validate_shared_regex(rules: list[Rule], errors: list[str]) -> None:
    by_id = {r.id: r for r in rules}
    for group, ids in SHARED_REGEX.items():
        missing = [i for i in ids if i not in by_id]
        if missing:
            errors.append(f"SHARED_REGEX[{group!r}] names unknown rules: {', '.join(missing)}")
            continue
        blocks = {i: shared_block(by_id[i], group) for i in ids}
        for i, block in blocks.items():
            if block is None:
                errors.append(f"{by_id[i].rel}: no '# --- {group} (begin)' / '(end)' markers")
            elif any(copy != block for copy in shared_block_copies(by_id[i], group)):
                errors.append(f"{by_id[i].rel}: its copies of the {group} differ from each "
                              "other; edit every copy together")
        first = blocks[ids[0]]
        for i in ids[1:]:
            if first is not None and blocks[i] is not None and blocks[i] != first:
                errors.append(f"{by_id[i].rel}: the {group} differ from {by_id[ids[0]].rel}; "
                              "edit both copies together")


def validate_shared_blocks(rules: list[Rule], errors: list[str]) -> None:
    by_id = {r.id: r for r in rules}
    for group, (ids, field, start, stop) in SHARED_BLOCKS.items():
        missing = [i for i in ids if i not in by_id]
        if missing:
            errors.append(f"SHARED_BLOCKS[{group!r}] names unknown rules: {', '.join(missing)}")
            continue
        def block(rule: Rule) -> list:
            path = field.get(rule.id, ()) if isinstance(field, dict) else (field,)
            node = rule.body
            for step in path:
                try:
                    node = node[step]
                except (KeyError, IndexError, TypeError):
                    return []
            return (node if isinstance(node, list) else [])[start:stop]

        first = by_id[ids[0]]
        shared = block(first)
        if not shared:
            errors.append(f"SHARED_BLOCKS[{group!r}]: {first.rel} has no {field} in that range")
        for other in (by_id[i] for i in ids[1:]):
            if block(other) != shared:
                errors.append(f"{other.rel}: the {group} differ from {first.rel}; they are "
                              "shared, so update them together")


def tag_list(rule: Rule, field: str, errors: list[str]) -> list[str]:
    tags = rule.meta.get(field)
    if tags is None:
        return []
    if not isinstance(tags, list) or not tags:
        errors.append(f"{rule.rel}: metadata.{field} must be a non-empty list")
        return []
    return [str(t) for t in tags]


def validate_aisvs(rule: Rule, aisvs: dict, errors: list[str]) -> None:
    # "v1.01-C10.3.3 - Secure Transport": AISVS's versioned citation form plus the section
    # title, since requirements have no titles of their own.
    prefix = f"v{aisvs['version']}-"
    requirements = {r: s for s, sec in aisvs["sections"].items() for r in sec["requirements"]}
    for tag in tag_list(rule, "owasp-aisvs", errors):
        ident, title = split_tag(tag)
        if not ident.startswith(prefix):
            errors.append(f"{rule.rel}: AISVS tag {ident!r} must cite version {prefix[:-1]}")
            continue
        section = requirements.get(ident.removeprefix(prefix))
        if section is None:
            errors.append(f"{rule.rel}: unknown AISVS requirement {ident!r}")
        elif title != aisvs["sections"][section]["title"]:
            errors.append(f"{rule.rel}: {ident} title should be {aisvs['sections'][section]['title']!r}")


def validate_atlas(rule: Rule, atlas: dict, errors: list[str]) -> None:
    for tag in tag_list(rule, "mitre-atlas", errors):
        ident, title = split_tag(tag)
        if ident not in atlas["techniques"]:
            errors.append(f"{rule.rel}: unknown ATLAS {atlas['version']} technique {ident!r}")
        elif title != atlas["techniques"][ident]:
            errors.append(f"{rule.rel}: {ident} title should be {atlas['techniques'][ident]!r}")


# PyYAML resolves scalars by YAML 1.1 rules and leaves a string unquoted when 1.1 would read it
# as a string, but OpenGrep's parser reads `Infinity`, `.inf`, `1e3`, `0o17`, and the like as
# numbers and then rejects a `pattern: Infinity` ("Expected a string value"). Quote any string
# another YAML parser could take for a number, boolean, or null.
NON_STRING_LOOKALIKE = re.compile(
    r"(?i)[-+]?(?:\.?inf(?:inity)?|\.?nan|\d[\d_]*(?:\.\d*)?(?:e[-+]?\d+)?|\.\d+(?:e[-+]?\d+)?"
    r"|0x[0-9a-f_]+|0o[0-7_]+|0b[01_]+)|true|false|yes|no|on|off|y|n|null|~|"
)


class AggregateDumper(yaml.SafeDumper):
    pass


def _represent_str(dumper: yaml.SafeDumper, value: str) -> yaml.ScalarNode:
    if NON_STRING_LOOKALIKE.fullmatch(value):
        return dumper.represent_scalar("tag:yaml.org,2002:str", value, style="'")
    return dumper.represent_str(value)


AggregateDumper.add_representer(str, _represent_str)


def render_aggregate(rules: list[Rule]) -> str:
    header = (
        "# Generated by scripts/build.py from rules/. Do not edit by hand.\n"
        "# Use with: opengrep scan --config rules.yaml <path>\n"
    )
    bodies = []
    for rule in sorted(rules, key=lambda r: r.id):
        body = copy.deepcopy(rule.body)
        # OpenGrep only carries the standard `owasp` and `cwe` fields into SARIF tags, so mirror
        # every OWASP tag, AISVS included, into `owasp`; consumers then see them as
        # "OWASP-LLM10:2026 - ..." tags. ATLAS is not OWASP, so it stays in rule metadata only.
        body["metadata"]["owasp"] = [t for f in (*OWASP_FIELDS, "owasp-aisvs") for t in rule.meta.get(f) or []]
        bodies.append(body)
    return header + yaml.dump(
        {"rules": bodies}, Dumper=AggregateDumper, sort_keys=False, width=100, allow_unicode=True
    )


def short_ids(tags: list[str] | None, current: dict) -> str:
    return ", ".join(split_tag(t)[0] for t in tags or [] if split_tag(t)[0] in current) or "—"


def render_rules_doc(rules: list[Rule], taxonomy: dict) -> str:
    lines = [GENERATED_NOTE, "", "# Rules", "", "Every rule in the pack, grouped by what it scans.", ""]
    for key, label in PACK_CATEGORIES.items():
        group = sorted((r for r in rules if r.meta.get("pack-category") == key), key=lambda r: r.id)
        lines.append(f"## {label}")
        lines.append("")
        if not group:
            lines += ["No rules yet.", ""]
            continue
        lines.append("| Rule | Languages | Severity | OWASP LLM | OWASP Agentic | OWASP MCP (beta) |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for r in group:
            lines.append(
                f"| [`{r.id}`](../{r.rel}) | {', '.join(r.body.get('languages', []))} "
                f"| {r.body.get('severity')} "
                f"| {short_ids(r.meta.get('owasp-llm'), taxonomy['owasp-llm']['current'])} "
                f"| {short_ids(r.meta.get('owasp-agentic'), taxonomy['owasp-agentic']['current'])} "
                f"| {short_ids(r.meta.get('owasp-mcp'), taxonomy['owasp-mcp']['current'])} |"
            )
        lines.append("")
    return "\n".join(lines)


def render_coverage_doc(rules: list[Rule], taxonomy: dict) -> str:
    lines = [
        GENERATED_NOTE,
        "",
        "# OWASP coverage",
        "",
        "How many rules map to each category of the OWASP LLM, Agentic, and MCP Top 10 lists. A rule",
        "can map to several categories, so the counts overlap. A dash means no rule maps there yet.",
        "",
    ]
    lines.append("| OWASP ID | Title | Rules |")
    lines.append("| --- | --- | --- |")
    for field in OWASP_FIELDS:
        for ident, entry in taxonomy[field]["current"].items():
            count = sum(
                1 for r in rules if ident in [split_tag(t)[0] for t in r.meta.get(field) or []]
            )
            title = entry["title"] + (" (beta)" if taxonomy[field].get("beta") else "")
            lines.append(f"| {ident} | {title} | {count or '—'} |")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    check = "--check" in sys.argv[1:]
    # Generated rule files first, so the rules loaded below are the generated ones.
    generated = {}
    owner = {}
    for gen in GENERATORS:
        for path, content in gen.render().items():
            generated[path] = content
            owner[path] = Path(gen.__file__).name
    stale_rules = [p for p, content in generated.items() if not p.exists() or p.read_text() != content]
    if not check:
        for path in stale_rules:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(generated[path])
            print(f"wrote {path.relative_to(ROOT)}")
    errors: list[str] = []
    taxonomy = load_taxonomy()
    rules = load_rules(errors)
    validate(rules, taxonomy, errors)
    validate_shared_paths(rules, errors)
    validate_shared_regex(rules, errors)
    validate_shared_blocks(rules, errors)
    if errors:
        print("\n".join(f"error: {e}" for e in errors), file=sys.stderr)
        return 1

    outputs = {
        AGGREGATE: render_aggregate(rules),
        RULES_DOC: render_rules_doc(rules, taxonomy),
        COVERAGE_DOC: render_coverage_doc(rules, taxonomy),
    }
    stale = [p for p, content in outputs.items() if not p.exists() or p.read_text() != content]
    if check:
        for path in stale_rules:
            print(f"error: {path.relative_to(ROOT)} differs from what scripts/{owner[path]} "
                  "generates; edit the script, then run python3 scripts/build.py", file=sys.stderr)
        for path in stale:
            print(f"error: {path.relative_to(ROOT)} is stale; run python3 scripts/build.py", file=sys.stderr)
        if not stale and not stale_rules:
            print(f"ok: {len(rules)} rules valid, generated files current")
        return 1 if stale or stale_rules else 0

    for path in stale:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(outputs[path])
        print(f"wrote {path.relative_to(ROOT)}")
    print(f"ok: {len(rules)} rules valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
