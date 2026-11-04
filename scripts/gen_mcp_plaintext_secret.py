#!/usr/bin/env python3
"""Generate the mcp-config-plaintext-secret rule files from one set of regexes.

The JSON (most MCP clients), YAML (Continue), TOML (Codex), VS Code workspace-file and Claude
Code subagent front matter rules judge a value with the same credential regexes, written once
here. The file paths come from gen_mcp_unpinned.py, so this
family and mcp-config-unpinned-package* always scan the same MCP config files. Only the
scaffolding that finds a server's strings and key-value pairs differs per format.

Edit this script, not the rule files. scripts/build.py regenerates them, and
scripts/build.py --check fails when a rule file differs from what this script produces.

Usage:
    python3 scripts/gen_mcp_plaintext_secret.py    # rewrite the rule files
"""

from __future__ import annotations

import sys
from pathlib import Path

from gen_mcp_unpinned import (JSON_PATHS, JSON_SCOPE, JSONC_MCP, JSONC_PAIR, JSONC_STRING,
                              JSONC_LINES_NB, JSONC_WALK, SUBAGENT_NOTE, SUBAGENT_PATHS,
                              SUBAGENT_REFS, TOML_PATHS, WORKSPACE_PATHS,
                              WORKSPACE_REGEX_NOTE, YAML_PATHS, ind, mvr, pregex,
                              subagent_patterns)

ROOT = Path(__file__).resolve().parent.parent
RULE_DIR = ROOT / "rules" / "agent-config" / "secrets"

# ---- shared regex pieces -------------------------------------------------------------------

# Words that mark a key, flag, or query parameter as holding a credential. Matched at the end
# of the name, so GITHUB_TOKEN, clientSecret and STRIPE_SECRET_KEY match but TOKEN_URL,
# MAX_TOKENS and SECRET_KEY_PATH don't. gen_secret_in_system_prompt.py builds its own
# (longer) list of credential names on top of this one, so the two can't drift.
SECRET_WORD = (r"token|secret|secret[_-]?key|password|passwd|api[_-]?key|apikey|access[_-]?key"
               r"|private[_-]?key|auth[_-]?key|service[_-]?role[_-]?key")

DEFINE = r"""(?(DEFINE)
  # Placeholder text that people paste instead of a value, and the marker words of a planted
  # decoy (a leak probe's sk-bait-...-CANARY). Not "fake": the pack's own fixtures mark their
  # positives with FAKE.
  (?<ph> (?i: x{4} | your | placeholder | changeme | change[_-]me | replace[_-]?me | redacted
    | dummy | example | canary | bait | decoy | honeytoken | \*{3} ) )
  # An opaque literal: 16+ token characters with a letter and a digit, no placeholder text.
  # Template syntax (${VAR}, ${env:VAR}, ${input:id}, ${{ secrets.X }}, $VAR, %VAR%) contains
  # characters outside this set, so it never qualifies.
  (?<oc> [A-Za-z0-9._~+/=-] )
  (?<opq> (?=(?&oc)*[0-9]) (?=(?&oc)*[A-Za-z]) (?!(?&oc)*?(?&ph)) (?&oc){16,}+ (?!(?&oc)) )
  # Credential formats with a fixed, documented prefix (sources in the rule's references).
  (?<known> (?:
      gh[pousr]_[A-Za-z0-9_]{36,}                       # GitHub PAT, OAuth, app tokens
    | github_pat_[A-Za-z0-9_]{50,}                      # GitHub fine-grained PAT
    | A(?:KIA|SIA|BIA|CCA)(?!I(?:OSFODNN7|44QH8DHB)EXAMPLE)[A-Z0-9]{16} # AWS key ID, not the docs' examples
    | xox[bpe]-[A-Za-z0-9-]{20,} | xoxe\.x(?:oxb|oxp|app)-[A-Za-z0-9-]{20,}
    | xapp-[A-Za-z0-9-]{20,} | xwfp-[A-Za-z0-9-]{20,}  # Slack bot, user, refresh, app, workflow
    | hooks\.slack\.com/services/[A-Za-z0-9_-]+/[A-Za-z0-9_-]+/[A-Za-z0-9]{16,} # Slack webhook
    | sk-(?=[A-Za-z0-9_-]*[0-9])[A-Za-z0-9_-]{20,}      # OpenAI, Anthropic, OpenRouter (sk-or-v1-)
    | [rs]k_(?:live|test)_[A-Za-z0-9]{20,}              # Stripe secret and restricted (not pk_)
    | AIza[0-9A-Za-z_-]{35}                             # Google API key
    | gl(?:pat|oas|dt|rt|rtr|cbt|ptt|ft|imt|agent|wt|soat|ffct)-[A-Za-z0-9_.-]{20,} # GitLab
    | hf_[A-Za-z0-9]{30,}                               # Hugging Face
    | npm_[A-Za-z0-9]{36,}                              # npm
    | ntn_[A-Za-z0-9]{40,} | secret_[A-Za-z0-9]{32,}    # Notion (current, legacy)
    | lin_(?:api|oauth)_[A-Za-z0-9]{40,}                # Linear
    | sbp_[A-Za-z0-9]{40,} | sb_secret_[A-Za-z0-9_-]{20,} # Supabase (not sb_publishable_)
    | sntryu_[a-f0-9]{64} | sntrys_[A-Za-z0-9+/=_]{40,} # Sentry user, org (not DSNs)
    | ATAT[A-Za-z0-9_=-]{40,}                           # Atlassian API token
    | r8_[A-Za-z0-9]{37}                                # Replicate
    | tvly-(?=[A-Za-z0-9_-]*[0-9])[A-Za-z0-9_-]{20,}    # Tavily
    | fc-[a-f0-9]{32}                                   # Firecrawl
    | pplx-[A-Za-z0-9]{32,}                             # Perplexity (model names have hyphens)
    | gsk_[A-Za-z0-9]{40,}                              # Groq
    | do[opr]_v1_[A-Za-z0-9]{32,}                       # DigitalOcean
    | shp(?:at|ca|pa|ss)_[A-Za-z0-9]{32,}               # Shopify tokens and app secret
    | SG\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}        # SendGrid
    | pypi-[A-Za-z0-9_-]{50,}                           # PyPI
    | glsa_[A-Za-z0-9]{32}_[A-Fa-f0-9]{8} | glc_[A-Za-z0-9+/=_-]{32,} # Grafana
    | vc[pirak]_[A-Za-z0-9]{24,}                        # Vercel
    | cf(?:k|ut|at|ast)_[A-Za-z0-9]{40,}                # Cloudflare
  ) (?![A-Za-z0-9_-]) )
)"""

# Credential-shaped text that can sit anywhere in a longer string: a known credential format,
# a literal Bearer or Basic credential, or a URL with a secret query parameter or a password
# before the host. gen_secret_in_system_prompt.py reuses it (with DEFINE) for prompt text.
EMBEDDED = rf"""    # A known credential format, anywhere in the string (also inside a JSON-encoded header
    # map or a bash -c line).
    (?<![A-Za-z0-9_]) (?![A-Za-z0-9_.-]*?(?&ph)) (?&known)
    # Authorization: Bearer / Basic with a literal credential.
  | (?<![A-Za-z0-9_-]) (?i:bearer|basic) [ \t]+ (?&opq) (?=["'\\\s,;}}]|$)
    # https://host/mcp?api_key=... (Smithery, Tavily and others document this shape).
  | (?i:https?|wss?):// [^\s"'?\#\\]* \? (?:[^\s"'\#\\]*&)?
    (?:[\w.-]*?(?i:{SECRET_WORD}|auth)|(?i:key)) = (?&opq) (?=[&\#"'\\\s]|$)
    # scheme://user:password@host, unless the host is this machine.
  | (?<![A-Za-z0-9+.-]) [A-Za-z][A-Za-z0-9+.-]*:// [^\s"'/:@?\#\\]+ :
    (?!(?i:password|passwd|pass|secret|pwd|changeme)@) (?![^\s"'/@?\#\\]*(?&ph))
    [^\s"'/@?\#\\$%{{}}<>*]+ @
    (?=[^\s"'/:?\#\\@]*\.) (?!(?i:localhost|127\.|0\.0\.0\.0|host\.docker\.internal)[:/?\#"'\\\s]?)
    (?![^\s"'/:?\#\\@]*\.(?i:local|localhost)(?:[:/?\#"'\\\s]|$))"""

# Any string in a server entry: EMBEDDED, or a flag, KEY=value, or "Header: value" string that
# carries a credential.
VALUE = rf"""(?x)
{DEFINE}
^ .*? (?:
{EMBEDDED}
    # --api-key=..., GITHUB_TOKEN=... (docker -e), X-API-Key: ... (mcp-remote --header).
  | ^ ["']? (?: --?[\w-]*?(?i:{SECRET_WORD})
      | (?:--?e(?:nv)?[= ])? [A-Za-z_][\w.-]*?(?i:{SECRET_WORD}) ) = (?&opq) ["']? $
  | ^ ["']? [\w-]*?(?i:{SECRET_WORD}|authorization) [ \t]*:[ \t]* (?&opq) ["']? $
)"""

# A key that names a credential: env var, header, or OAuth field.
KEY = rf"""(?i)^["']?[\w.-]*?(?:{SECRET_WORD}|authorization|(?<![a-z0-9])pat)["']?$"""

# A command-line flag that takes a credential as its next argument (--token, --access-token).
FLAG = rf"""(?i)^["']?--?[\w-]*?(?:{SECRET_WORD})["']?$"""

# The whole value is an opaque literal: not a path, a file name, or an env var name (the
# value of Codex env_http_headers and similar indirections).
LITERAL = rf"""(?x)
{DEFINE}
^ ["']?
(?! [/~] | \.\.?/ )
(?! (?:[A-Z0-9]*_)+[A-Z0-9]* ["']? $ )
(?! .* \.(?i:json|pem|key|p12|pfx|crt|cer|txt|ya?ml|env|toml|cfg|ini|conf) ["']? $ )
(?&opq) ["']? $"""

# A VS Code input declared as a password with a literal default.
INPUT_DEFAULT = r"""(?x)
^ ["']? (?! [^"']*? (?: \$\{ | (?i: x{4} | your | placeholder | changeme | redacted ) ) )
[^\s"'$]{8,} ["']? $"""

# YAML: $V is a single scalar, not a mapping or sequence node.
YAML_SCALAR = r"""^(?:"[^\n]*"|'[^\n]*'|(?![-?:]\s|[\[{|>&*!%@`])(?:(?!:(?:\s|$)|\s\#)[^\n])*)$"""

# ---- format scaffolding --------------------------------------------------------------------

SYNC_NOTE = """# Generated by scripts/gen_mcp_plaintext_secret.py, which holds the credential regexes shared
# by the mcp-config-plaintext-secret rules for JSON, Continue YAML, Codex TOML, VS Code
# workspace files and Claude Code subagent front matter, and takes the file paths from
# scripts/gen_mcp_unpinned.py. Edit the script and run scripts/build.py; build.py --check fails
# if this file drifts.
"""

# Why it matters, shared by the messages; each adds its client's fix.
WHY = """      Bearer header, or a secret in the server URL). Everyone and every tool that opens the
      project can read this file; it gets committed, copied, and pasted into issues, and it sits
      in the agent's workspace, where a prompt-injected agent can read the credential and send
      it out. Such tokens are usually long-lived and carry the developer's full access. Revoke
      and rotate this credential, then load it at run time instead:
"""

JSON_MESSAGE = ("""    message: >-
      This MCP server entry holds a literal credential (an API key, access token, password,
""" + WHY + """      ${VAR} in Claude Code and Gemini CLI, ${env:VAR} in Cursor and Windsurf, an ${input:id}
      with "password": true and no default in VS Code, or the client's OAuth login.
""")

YAML_MESSAGE = ("""    message: >-
      This Continue MCP server holds a literal credential (an API key, access token, password,
""" + WHY + """      reference a secret with ${{ secrets.NAME }}, or ${{ inputs.NAME }} in a block.
""")

WORKSPACE_MESSAGE = ("""    message: >-
      This VS Code workspace file's MCP configuration holds a literal credential (an API key,
      access token, password,
""" + WHY + """      an ${input:id} with "password": true and no default, ${env:VAR}, or the server's OAuth
      login.
""")

SUBAGENT_MESSAGE = ("""    message: >-
      This subagent's inline MCP server holds a literal credential (an API key, access token,
      password,
""" + WHY + """      reference by name (mcpServers: [name]) a server each developer configures with their own
      credential outside the repository, or use the server's OAuth login.
""")

TOML_MESSAGE = ("""    message: >-
      This Codex MCP server holds a literal credential (an API key, access token, password,
""" + WHY + """      env_vars = ["NAME"] forwards a variable to a stdio server, bearer_token_env_var and
      env_http_headers (header name to variable name) cover HTTP servers, or use Codex's OAuth
      login.
""")


def value_branches(fmt, n):
    """The three value checks for one server's strings, keys, and args."""
    pad = " " * n
    out = ""
    if fmt == "json":
        out += f"{pad}# Any string in the entry (env, headers, args, url, auth, oauth).\n"
        out += f"{pad}- patterns:\n{pad}    - pattern: '\"$V\"'\n"
        out += mvr("$V", VALUE, n + 4, literal=True)
        out += f"{pad}# A key that names a credential, with an opaque literal value.\n"
        out += f"{pad}- patterns:\n{pad}    - pattern: '\"$K\": \"$V\"'\n"
        out += mvr("$K", KEY, n + 4, literal=True)
        out += mvr("$V", LITERAL, n + 4, literal=True)
        out += f"{pad}# A credential flag and its value as two args: \"--access-token\", \"...\".\n"
        out += f"{pad}- patterns:\n{pad}    - pattern-inside: '\"args\": [..., \"$F\", \"$V\", ...]'\n"
        out += f"{pad}    - pattern: '\"$V\"'\n"
        out += mvr("$F", FLAG, n + 4, literal=True)
        out += mvr("$V", LITERAL, n + 4, literal=True)
    elif fmt == "yaml":
        out += f"{pad}# Any scalar in the entry (env, requestOptions.headers, apiKey, args, url).\n"
        out += f"{pad}- patterns:\n{pad}    - pattern: $V\n"
        out += mvr("$V", YAML_SCALAR, n + 4, literal=True)
        out += mvr("$V", VALUE, n + 4, literal=True)
        out += f"{pad}# A key that names a credential, with an opaque literal value.\n"
        out += f"{pad}- patterns:\n{pad}    - pattern: '$K: $V'\n"
        out += mvr("$K", KEY, n + 4, literal=True)
        out += mvr("$V", LITERAL, n + 4, literal=True)
        out += f"{pad}# A credential flag and its value as two args: --access-token, \"...\".\n"
        out += f"{pad}- patterns:\n{pad}    - pattern-inside: 'args: [..., $F, $V, ...]'\n"
        out += f"{pad}    - pattern: $V\n"
        out += mvr("$F", FLAG, n + 4, literal=True)
        out += mvr("$V", LITERAL, n + 4, literal=True)
    elif fmt == "jsonc":  # inside a metavariable-pattern over the workspace file's mcp block
        out += f"{pad}# Each string, outside comments: env, headers, args, url, and input defaults.\n"
        out += f"{pad}- patterns:\n" + pregex(JSONC_STRING, n + 4)
        out += mvr("$V", VALUE, n + 4, literal=True)
        out += f"{pad}# \"key\": \"value\", where the key names a credential.\n"
        out += f"{pad}- patterns:\n" + pregex(JSONC_PAIR, n + 4)
        out += mvr("$K", KEY, n + 4, literal=True)
        out += mvr("$V", LITERAL, n + 4, literal=True)
        out += f"{pad}# A credential flag and its value as two array elements.\n"
        out += f"{pad}- patterns:\n" + pregex(JSONC_FLAG_PAIR, n + 4)
        out += mvr("$F", FLAG, n + 4, literal=True)
        out += mvr("$V", LITERAL, n + 4, literal=True)
        out += f"{pad}# A VS Code password input with a literal default.\n"
        out += f"{pad}- patterns:\n" + pregex(JSONC_PASSWORD_DEFAULT, n + 4)
        out += mvr("$V", INPUT_DEFAULT, n + 4, literal=True)
    else:  # toml, inside a metavariable-pattern over one server's text
        out += f"{pad}# Each string, outside comments: \"basic\" (with escapes) or 'literal'.\n"
        out += f"{pad}- patterns:\n"
        out += f"{pad}    - pattern-regex: {TOML_STRING}\n"
        out += mvr("$V", VALUE, n + 4, literal=True)
        out += f"{pad}# key = \"value\", also inside an inline table (env = {{ KEY = \"...\" }}).\n"
        out += f"{pad}- patterns:\n"
        out += f"{pad}    - pattern-regex: {TOML_PAIR}\n"
        out += mvr("$K", KEY, n + 4, literal=True)
        out += mvr("$V", LITERAL, n + 4, literal=True)
        out += f"{pad}# A credential flag and its value as two array elements.\n"
        out += f"{pad}- patterns:\n"
        out += f"{pad}    - pattern-regex: {TOML_FLAG_PAIR}\n"
        out += mvr("$F", FLAG, n + 4, literal=True)
        out += mvr("$V", LITERAL, n + 4, literal=True)
    return out


# TOML string and pair scanners. Each walks a line from its start (or, through \G, from the
# previous match) over plain text and whole strings and stops at a # comment, so a match never
# starts inside a string or a comment, and every string or pair on a line is found.
TOML_Q = r"""(?<Q>["'])(?<V>(?:(?!\k<Q>)[^\\\n]|\\.)*+)\k<Q>"""
TOML_WALK = r"""(?m)(?:^|\G)(?:[^"'\#\n]|"(?:[^"\\\n]|\\.)*+"|'[^'\n]*+')*?"""
TOML_STRING = TOML_WALK + TOML_Q
TOML_PAIR = (TOML_WALK + r"""(?:^|(?<=[{,]))[ \t]*(?<K>"[^"\n]*"|'[^'\n]*'|[\w.-]+)[ \t]*=[ \t]*"""
             + TOML_Q)
TOML_FLAG_PAIR = TOML_WALK + r"""(?<F>"--?[\w-]+"|'--?[\w-]+')[ \t]*,\s*""" + TOML_Q

# The JSONC (code-workspace) twins.
JSONC_FLAG_PAIR = JSONC_WALK + r'''(?<F>"--?[\w-]+")[ \t]*+,\s*+"(?<V>(?:[^"\\\n]|\\.)*+)"'''
# Input objects are flat: { "type": ..., "id": ..., "password": true, "default": "..." }.
JSONC_PASSWORD_DEFAULT = (JSONC_WALK + r'''\{(?=''' + JSONC_LINES_NB + r'''"password"\s*+:\s*+true\b)'''
                          + JSONC_LINES_NB + r'''"default"\s*+:\s*+"(?<V>(?:[^"\\\n]|\\.)*+)"''')

REFS_COMMON = """        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP01-2025-Token-Mismanagement-and-Secret-Exposure.md
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM02_SensitiveInformationDisclosure.md
"""

REFS_TOKENS = """        - https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github#githubs-token-formats
        - https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_identifiers.html#identifiers-unique-ids
        - https://docs.slack.dev/authentication/tokens
        - https://docs.gitlab.com/security/tokens/
        - https://docs.stripe.com/keys
        - https://supabase.com/docs/guides/api/api-keys
        - https://docs.sentry.io/security-legal-pii/security/token-formats/
"""

METADATA = """    metadata:
      category: security
      subcategory: [vuln]
      pack-category: agent-config
      owasp-llm:
        - "LLM02:2026 - Sensitive Information Disclosure"
        - "LLM02:2025 - Sensitive Information Disclosure"
      owasp-agentic:
        - "ASI03 - Identity and Privilege Abuse"
      owasp-mcp:
        - "MCP01:2025 - Token Mismanagement & Secret Exposure"
      owasp-aisvs:
        - "v1.01-C9.5.4 - Agent Authorization, Delegation, and Continuous Enforcement"
      mitre-atlas:
        - "AML.T0083 - Credentials from AI Agent Configuration"
      cwe:
        - "CWE-798: Use of Hard-coded Credentials"
        - "CWE-312: Cleartext Storage of Sensitive Information"
      # Values must be a documented credential format, a literal Bearer/Basic credential, or
      # an opaque 16+ character literal (letters and digits) under a key or flag that names
      # a secret; placeholders and template references never match.
      confidence: HIGH
      likelihood: MEDIUM
      impact: HIGH
"""

# A root object holding one server (Continue's one-server JSON files) can also be remote.
JSON_ROOT_URL = """          # ... and that server can be a remote one with a url instead of a command.
          - patterns:
              - pattern-inside: '{..., "url": $X, ...}'
              - pattern-not-inside: '"$K": {..., "url": $Y, ...}'
              - pattern-not-inside: '[..., {..., "url": $Y, ...}, ...]'
"""


# Text that belongs to MCP servers in a Codex config.toml: binds $TABLE. gen_mcp_remote_host.py
# imports it, so both families read the same tables.
TOML_TABLES = r"""      # $TABLE is text that belongs to MCP servers.
      - pattern-either:
          # [mcp_servers], [mcp_servers.<name>] and its sub-tables ([mcp_servers.<name>.env],
          # .http_headers, .oauth), each up to the next table header. env_http_headers maps a
          # header to a variable name, so its table is skipped.
          - pattern-regex: (?m)^[ \t]*\[(?![^\]\n]*\benv_http_headers\b)[ \t]*mcp_servers(?:[ \t]*\.[ \t]*(?:"[^"\n]*"|'[^'\n]*'|[\w-]+))*[ \t]*\][ \t]*(?:\#[^\n]*)?\n(?<TABLE>(?:(?![ \t]*\[)[^\n]*(?:\n|\z))*)
          # Dotted keys outside those tables: mcp_servers.<name>.env = { ... }.
          - pattern-regex: (?m)^[ \t]*mcp_servers[ \t]*\.(?![^\n=]*\benv_http_headers\b)(?<TABLE>[^\n]*)
"""


def json_rule():
    s = "rules:\n  - id: mcp-config-plaintext-secret\n"
    s += ind(SYNC_NOTE.format(a="-toml", b="-yaml"), 4)
    s += "    languages: [json]\n    severity: ERROR\n" + JSON_MESSAGE
    s += JSON_PATHS
    s += "    patterns:\n      - pattern-either:\n"
    s += "          - patterns:\n"
    s += ind(JSON_SCOPE, 8) + ind(JSON_ROOT_URL, 8)
    s += "              - pattern-either:\n"
    s += value_branches("json", 18)
    s += """          # VS Code inputs: a password input with a literal default, or any default that is a
          # known credential.
          - patterns:
              - pattern-inside: '"inputs": [...]'
              - pattern-either:
                  - patterns:
                      - pattern-inside: '{..., "password": true, ...}'
                      - pattern: '"default": "$V"'
"""
    s += mvr("$V", INPUT_DEFAULT, 22, literal=True)
    s += """                  - patterns:
                      - pattern: '"default": "$V"'
"""
    s += mvr("$V", VALUE, 22, literal=True)
    s += "      - focus-metavariable: $V\n"
    s += METADATA
    s += "      technology: [mcp, claude-code, claude-desktop, cursor, vscode, cline, windsurf, gemini-cli, continue]\n"
    s += "      references:\n" + REFS_COMMON + """        - https://code.claude.com/docs/en/mcp
        - https://code.visualstudio.com/docs/copilot/reference/mcp-configuration
        - https://cursor.com/docs/context/mcp
        - https://github.com/google-gemini/gemini-cli/blob/09d81bf116b6f0ef084731dc996aa9d56438bb70/packages/core/src/config/config.ts
        - https://docs.continue.dev/customize/deep-dives/mcp
""" + REFS_TOKENS
    return s


def yaml_rule():
    s = "rules:\n  - id: mcp-config-plaintext-secret-yaml\n"
    s += ind(SYNC_NOTE.format(a="", b="-toml"), 4)
    s += "    languages: [yaml]\n    severity: ERROR\n" + YAML_MESSAGE
    s += YAML_PATHS
    s += "    patterns:\n      - pattern-inside: 'mcpServers: [...]'\n      - pattern-either:\n"
    s += value_branches("yaml", 10)
    s += "      - focus-metavariable: $V\n"
    s += METADATA
    s += "      technology: [mcp, continue]\n"
    s += "      references:\n" + REFS_COMMON + """        - https://docs.continue.dev/customize/deep-dives/mcp
        - https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/packages/config-yaml/src/schemas/mcp/index.ts
""" + REFS_TOKENS
    return s


def toml_rule():
    s = "rules:\n  - id: mcp-config-plaintext-secret-toml\n"
    s += "    # Regex, not a parser: OpenGrep has no TOML support.\n"
    s += ind(SYNC_NOTE.format(a="", b="-yaml"), 4)
    s += "    languages: [regex]\n    severity: ERROR\n" + TOML_MESSAGE
    s += TOML_PATHS
    s += r"""    patterns:
"""
    s += TOML_TABLES + r"""      - metavariable-pattern:
          metavariable: $TABLE
          language: regex
          patterns:
            - pattern-either:
"""
    s += value_branches("toml", 16)
    s += "      - focus-metavariable: $V\n"
    s += METADATA
    s += "      technology: [mcp, codex]\n"
    s += "      references:\n" + REFS_COMMON + """        - https://learn.chatgpt.com/docs/extend/mcp?surface=cli
        - https://github.com/openai/codex/blob/342ed69a174c206c1de52a59491b131e0753cfa5/codex-rs/config/src/mcp_types.rs
""" + REFS_TOKENS
    return s


def workspace_rule():
    s = "rules:\n  - id: mcp-config-plaintext-secret-workspace\n" + WORKSPACE_REGEX_NOTE
    s += ind(SYNC_NOTE, 4)
    s += "    languages: [regex]\n    severity: ERROR\n" + WORKSPACE_MESSAGE
    s += WORKSPACE_PATHS + "    patterns:\n" + pregex(JSONC_MCP, 6)
    s += """      - metavariable-pattern:
          metavariable: $MCP
          language: regex
          patterns:
            - pattern-either:
"""
    s += value_branches("jsonc", 16)
    s += "      - focus-metavariable: $V\n"
    s += METADATA
    s += "      technology: [mcp, vscode]\n"
    s += "      references:\n" + REFS_COMMON + """        - https://code.visualstudio.com/docs/copilot/reference/mcp-configuration
        - https://github.com/microsoft/vscode/blob/1.143.1/src/vs/platform/mcp/common/mcpResourceScannerService.ts
""" + REFS_TOKENS
    return s


def subagent_rule():
    s = "rules:\n  - id: mcp-config-plaintext-secret-subagent\n" + SUBAGENT_NOTE
    s += ind(SYNC_NOTE, 4)
    s += "    languages: [generic]\n    severity: ERROR\n" + SUBAGENT_MESSAGE
    s += SUBAGENT_PATHS + subagent_patterns(value_branches("yaml", 16))
    s += "      - focus-metavariable: $V\n"
    s += METADATA
    s += "      technology: [mcp, claude-code]\n"
    s += "      references:\n" + REFS_COMMON + SUBAGENT_REFS + REFS_TOKENS
    return s


def render() -> dict[Path, str]:
    """The rule files and the content this script generates for each."""
    return {
        RULE_DIR / "mcp-config-plaintext-secret.yaml": json_rule(),
        RULE_DIR / "mcp-config-plaintext-secret-yaml.yaml": yaml_rule(),
        RULE_DIR / "mcp-config-plaintext-secret-toml.yaml": toml_rule(),
        RULE_DIR / "mcp-config-plaintext-secret-workspace.yaml": workspace_rule(),
        RULE_DIR / "mcp-config-plaintext-secret-subagent.yaml": subagent_rule(),
    }


def main() -> int:
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in render().items():
        if not path.exists() or path.read_text() != content:
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
