#!/usr/bin/env python3
"""Generate the MCP tool auto-approval rules from one tool-name regex.

Committed agent config can approve MCP tool calls ahead of time, so the agent calls them without
asking. Each client spells it differently (verified 2026-10-23):

- Roo Code (v3.54.0): "alwaysAllow" in a server of .roo/mcp.json; "*" approves every tool.
- Kiro (docs): "autoApprove" in .kiro/settings/mcp.json; "*" approves every tool.
- Gemini CLI (v0.65.0): "trust": true on a server, tools.allowed entries mcp_<server>_* or
  mcp_*, every mcp.allowed entry, and mcp.autoAllowInHeadless, in a trusted folder's
  .gemini/settings.json.
- Codex (rust-v0.164.0): default_tools_approval_mode = "approve" on a server and
  approval_mode = "approve" on a tool, in a trusted project's .codex/config.toml.
- Claude Code (docs, 2.1.309): permissions.allow entries mcp__<server>, mcp__<server>__* and
  named tools, in project settings once the folder is trusted, and in a skill's or command's
  allowed-tools front matter, which folder trust never gates.
- Cursor (docs): Mcp(server:tool) entries in .cursor/cli.json permissions.allow, and
  "server:tool" entries in a repository's .cursor/permissions.json mcpAllowlist.

"Broad" means all of a server's tools (a "*" or a glob that isn't limited to read verbs, or a
whole-server entry), or a named tool whose name says it changes something: it writes, deletes,
sends, merges, deploys, or runs a command. A list of named read-only tools (read_file,
list_issues, get_*) is the near-miss left alone. TOOL below encodes that test.

Claude Code's enableAllProjectMcpServers and enabledMcpjsonServers approve starting project
servers rather than tool calls; claude-settings-project-mcp-auto-start covers them here because
it shares the settings files.

agent-tool-approval-disabled (+ -ts) uses the same test for the other agent SDKs' approval
switches: require_approval on OpenAI (and Azure AI Foundry) hosted MCP tools, the OpenAI Agents
SDK's hosted MCP helpers and approval callbacks, and LangChain / deepagents interrupt_on maps.

The MCP config rules take their file paths from gen_mcp_unpinned.py, so they scan the same
files as the other MCP config families.

Edit this script, not the rule files. scripts/build.py regenerates them, and
scripts/build.py --check fails when a rule file differs from what this script produces.

Usage:
    python3 scripts/gen_mcp_auto_approve.py    # rewrite the rule files
"""

from __future__ import annotations

import sys
from pathlib import Path

from gen_mcp_unpinned import JSON_PATHS, JSON_SCOPE, TOML_PATHS, ind, mvr, pregex

ROOT = Path(__file__).resolve().parent.parent
RULE_DIR = ROOT / "rules" / "agent-config" / "permissions"

# ---- the tool-name test --------------------------------------------------------------------

# Verbs that name a read: a tool whose name has one before any action word is left alone
# (get_workflow_run, list_runs, read_query), and so is a glob after one (get_*).
READ = ("get|list|read|search|find|query|describe|view|show|fetch|lookup|count|check|status"
        "|inspect|preview|explain|diff|log|whoami|ping|help|info|summarize|analyze|validate"
        "|lint|resolve|browse|download|export|retrieve|select|ask|discover")
# Words that name an action with effects: run a command or code, write, delete, send, merge,
# deploy, change state.
ACT = ("exec|execute|run|shell|command|cmd|bash|powershell|terminal|eval|evaluate|script|spawn"
       "|start|stop|kill|restart|interact|write|edit|create|update|delete|remove|rm|drop"
       "|truncate|insert|upsert|modify|patch|put|post|push|commit|merge|rebase|reset|deploy"
       "|publish|release|send|reply|email|move|rename|install|uninstall|apply|migrate|upload"
       "|transfer|approve|close|add|set|submit|trigger|dispatch|invoke|fork|assign|archive"
       "|cancel|revert|replace|append|save|import|mutate|manage|reassign|escalate|refund|charge"
       "|pay|purchase|grant|revoke|invite|share|enable|disable|suspend|block|unblock|lock|unlock"
       "|rollback|restore|scale|provision|destroy|terminate|purge|clear|wipe|quarantine")

# A word starts at the start, after a separator, or at a camelCase hump; it ends at a separator,
# the end, a hump, a digit or a glob, optionally after a plural s / es (runs, pushes).
TOOL_DEFINE = r"""(?(DEFINE)
  (?<ws> (?<![^"'_\-./: (*]) | (?<=[a-z0-9])(?=[A-Z]) )
  (?<we> (?: es | s )?+ (?= [\-_./: )*?"'A-Z0-9,\]] | \s | $ ) )
  (?<read> (?&ws) (?i:""" + READ + r""") (?&we) )
  (?<act> (?&ws) (?i:""" + ACT + r""") (?&we) )
)"""

# The tool part of an entry: a glob ("*", "*_file", "github_*") or an action word, unless a read
# word comes first. NAME is the set of characters a tool name may hold in that format.
def tool(name_chars):
    return rf"""(?: (?! (?&read) ) {name_chars} )*? (?: [*?] | (?&act) )"""


def rx(body):
    """A verbose regex with the tool-name groups defined."""
    return "(?x)\n" + TOOL_DEFINE + "\n" + body


# ---- shared rule text ----------------------------------------------------------------------

SYNC_NOTE = """# Generated by scripts/gen_mcp_auto_approve.py, which holds the tool-name test shared by the
# MCP auto-approval rules. Edit the script and run scripts/build.py; build.py --check fails if
# this file drifts.
"""

LLM = """      owasp-llm:
        - "LLM03:2026 - Excessive Agency"
        - "LLM06:2025 - Excessive Agency"
"""

APPROVE_METADATA = """    metadata:
      category: security
      subcategory: [audit]
      pack-category: agent-config
""" + LLM + """      owasp-agentic:
        - "ASI02 - Tool Misuse and Exploitation"
      owasp-mcp:
        - "MCP02:2025 - Privilege Escalation via Scope Creep"
      owasp-aisvs:
        - "v1.01-C9.2.1 - High-Impact Action Approval and Irreversibility Controls"
        - "v1.01-C9.5.1 - Agent Authorization, Delegation, and Continuous Enforcement"
      mitre-atlas:
        - "AML.T0053 - AI Agent Tool Invocation"
      cwe:
        - "CWE-250: Execution with Unnecessary Privileges"
      # Whole-server approvals are certain; a named tool is judged by the words in its name,
      # which can't see what a server's tool really does.
      confidence: MEDIUM
      likelihood: MEDIUM
      impact: HIGH
"""

COMMON_REFS = """        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP02-2025%E2%80%93Privilege-Escalation-via-Scope-Creep.md
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md
"""

WHY = """      A prompt injection in a file, issue, web page, or tool result the agent reads can then
      make it use those tools (push code, post messages, change records, run commands) with
      the developer's credentials, for everyone who opens the project. """

FIX = """Leave approval on for
      tools that change things, and pre-approve only named read-only tools (read_file,
      list_issues) or keep approvals in your own user settings."""


def header(rule_id, lang, regex_note=None, severity="WARNING"):
    s = f"rules:\n  - id: {rule_id}\n"
    if regex_note:
        s += regex_note
    s += ind(SYNC_NOTE, 4)
    s += f"    languages: [{lang}]\n    severity: {severity}\n"
    return s


def entry_branch(n, inside, key, regex, comment=None):
    """A JSON branch: a string in the array under key, inside the given objects, tested by
    regex. The finding lands on the string (a bare "$V" would also match the key)."""
    pad = " " * n
    out = f"{pad}# {comment}\n" if comment else ""
    out += f"{pad}- patterns:\n"
    for p in inside:
        out += f"{pad}    - pattern-inside: '{p}'\n"
    out += f"{pad}    - pattern: '\"{key}\": [..., \"$V\", ...]'\n"
    if regex:
        out += mvr("$V", regex, n + 4, literal=True)
    out += f"{pad}    - focus-metavariable: $V\n"
    return out


# ---- mcp-config-auto-approve (JSON) --------------------------------------------------------

# An entry of a per-server list (Roo alwaysAllow, Kiro autoApprove): "*", a glob, or an action.
LIST_ENTRY = rx(r"""^ \s*+ """ + tool(r"""[^*?"]"""))
# Gemini tools.allowed: mcp_* (every MCP tool), mcp_<server>_* (a whole server), or a named
# action tool. One underscore after mcp, so Claude's mcp__ names don't count here.
GEMINI_ALLOWED = rx(r"""^ \s*+ mcp_ (?!_) """ + tool(r"""[^*?"]"""))

JSON_MESSAGE = """    message: >-
      This MCP config lets the agent call a server's tools without asking. "*" in Roo Code's
      alwaysAllow or Kiro's autoApprove approves every tool of the server, and a listed tool
      whose name says it writes, deletes, sends, merges, or runs something approves that
      action. In Gemini CLI, "trust": true skips every confirmation for the server, and so do
      tools.allowed entries such as "mcp_github_*" (or "mcp_*" for all servers), any
      mcp.allowed entry (which also approves the server's tools, not only its connection), and
      mcp.autoAllowInHeadless in non-interactive runs. Roo Code applies alwaysAllow once the
      user turns on auto-approval for MCP, and Gemini CLI applies a project's settings once
      the folder is trusted.
""" + WHY + FIX + "\n"


def json_rule():
    s = header("mcp-config-auto-approve", "json") + JSON_MESSAGE + JSON_PATHS
    s += "    pattern-either:\n"
    # Per-server keys.
    s += "      # Per-server keys: an alwaysAllow / autoApprove entry, or Gemini CLI's trust.\n"
    s += "      - patterns:\n" + ind(JSON_SCOPE, 4)
    s += """          - pattern-either:
              - patterns:
                  - pattern: '"$K": [..., "$V", ...]'
                  - metavariable-regex:
                      metavariable: $K
                      regex: ^"(?:alwaysAllow|autoApprove)"$
"""
    s += mvr("$V", LIST_ENTRY, 18, literal=True)
    s += """                  - focus-metavariable: $V
              # Gemini CLI drops trust from extension manifests (gemini-extension.json, which
              # has a top-level "version"; settings files don't).
              - patterns:
                  - pattern: '"trust": true'
                  - pattern-not-inside: '{..., "version": $VER, ...}'
"""
    s += "      # Gemini CLI settings outside the servers.\n"
    s += entry_branch(6, ['"tools": {...}'], "allowed", GEMINI_ALLOWED,
                      "tools.allowed: a whole server, every MCP tool, or a named action tool. "
                      "\"*\" is\n      # gemini-settings-unrestricted-shell's.")
    s += entry_branch(6, [], "allowedTools", GEMINI_ALLOWED,
                      "The settings v1 name, which Gemini CLI 0.23 and earlier read.")
    s += entry_branch(6, ['"mcp": {...}'], "allowed", None,
                      "mcp.allowed: each entry approves that server's tools (\"*\": every server's).")
    s += """      - patterns:
          - pattern-inside: '"mcp": {...}'
          - pattern: '"autoAllowInHeadless": true'
"""
    s += APPROVE_METADATA
    s += "      technology: [mcp, roo-code, kiro, gemini-cli]\n"
    s += "      references:\n" + COMMON_REFS + """        - https://github.com/RooCodeInc/Roo-Code/blob/v3.54.0/src/services/mcp/McpHub.ts
        - https://github.com/RooCodeInc/Roo-Code/blob/v3.54.0/src/core/auto-approval/index.ts
        - https://kiro.dev/docs/mcp/configuration/
        - https://github.com/google-gemini/gemini-cli/blob/v0.65.0/packages/core/src/policy/config.ts
        - https://github.com/google-gemini/gemini-cli/blob/v0.65.0/docs/tools/mcp-server.md
"""
    return s


# ---- mcp-config-auto-approve-toml (Codex) --------------------------------------------------

TOML_KEY = r"""(?: "[^"\n]*" | '[^'\n]*' | [\w-]+ )"""
TOML_DOT = r"""[ \t]*\.[ \t]*"""
APPROVE = r"""[ \t]*=[ \t]*(?:"approve"|'approve')"""
# A whole table, header to the next header, for tables under mcp_servers; and the lines before
# the first header.
TOML_TABLE = (r"""(?m)^[ \t]*\[[ \t]*mcp_servers(?:(?:""" + TOML_DOT + TOML_KEY.replace(" ", "")
              + r""")*)[ \t]*\][ \t]*(?:\#[^\n]*)?\n(?<TABLE>(?:(?![ \t]*\[)[^\n]*(?:\n|\z))*)""")
TOML_PREAMBLE = r"""\A(?<TABLE>(?:(?![ \t]*\[)[^\n]*(?:\n|\z))*)"""
# Walks a line over plain text and whole strings, stopping at a # comment.
TOML_WALK = r"""(?:^|\G)(?:[^"'\#\n]|"(?:[^"\\\n]|\\.)*+"|'[^'\n]*+')*?"""

# A tool's approval_mode = "approve", where the line names the tool $T: dotted
# (tools.<T>.approval_mode, <T>.approval_mode) or inline (<T> = { approval_mode = "approve" }).
TOML_DOTTED = (r"""(?m)""" + TOML_WALK + r"""(?<![\w"'-])(?<A>(?<T>""" + TOML_KEY.replace(" ", "")
               + r""")""" + TOML_DOT + r"""approval_mode""" + APPROVE + ")")
TOML_INLINE = (r"""(?m)""" + TOML_WALK + r"""(?<![\w"'-])(?<A>(?<T>""" + TOML_KEY.replace(" ", "")
               + r""")[ \t]*=[ \t]*\{[^{}\n]*?(?<![\w-])approval_mode""" + APPROVE + ")")

TOOL_NAME = rx(r"""^ ["']?+ """ + tool(r"""[^*?"']"""))

TOML_MESSAGE = """    message: >-
      This Codex config lets the agent call MCP tools without asking. default_tools_approval_mode
      = "approve" approves every tool of the server, and approval_mode = "approve" on a tool
      whose name says it writes, deletes, sends, merges, or runs something approves that
      action (Codex rust-v0.164.0, in a trusted project's .codex/config.toml). Codex writes
      approval_mode = "approve" back into the project file when someone picks "always allow",
      so these lines reach the repository without anyone deciding to share them.
""" + WHY + """Use "auto" (asks
      unless the tool says it is read-only and harmless) or "writes", approve only read-only
      tools, and keep personal approvals in ~/.codex/config.toml.
"""


def toml_rule():
    note = "    # Regex, not a parser: OpenGrep has no TOML support.\n"
    s = header("mcp-config-auto-approve-toml", "regex", note) + TOML_MESSAGE + TOML_PATHS
    s += "    pattern-either:\n"
    # Whole server.
    s += "      # default_tools_approval_mode = \"approve\": every tool of the server.\n"
    for table, comment in ((TOML_TABLE, "In an [mcp_servers...] table."),
                           (TOML_PREAMBLE, "Before the first table: mcp_servers.<name>... keys.")):
        s += f"      # {comment}\n      - patterns:\n"
        s += pregex(table, 10)
        line = (r"""(?m)""" + TOML_WALK + r"""(?<![\w-])(?<A>default_tools_approval_mode""" + APPROVE + ")")
        if table is TOML_PREAMBLE:
            line = r"""(?m)^[ \t]*mcp_servers""" + TOML_DOT + r"""[^\n]*?(?<![\w-])(?<A>default_tools_approval_mode""" + APPROVE + ")"
        s += """          - metavariable-pattern:
              metavariable: $TABLE
              language: regex
              patterns:
"""
        s += pregex(line, 16)
        s += "          - focus-metavariable: $A\n"
    # Named tools.
    s += "      # approval_mode = \"approve\" on a tool whose name is an action.\n"
    s += "      # [mcp_servers.<server>.tools.<tool>] names the tool in the header.\n"
    s += "      - patterns:\n"
    s += pregex(r"""(?m)^[ \t]*\[[ \t]*mcp_servers""" + TOML_DOT + TOML_KEY.replace(" ", "")
                + TOML_DOT + r"""tools""" + TOML_DOT + r"""(?<T>""" + TOML_KEY.replace(" ", "")
                + r""")[ \t]*\][ \t]*(?:\#[^\n]*)?\n(?<TABLE>(?:(?![ \t]*\[)[^\n]*(?:\n|\z))*)""", 10)
    s += mvr("$T", TOOL_NAME, 10, literal=True)
    s += """          - metavariable-pattern:
              metavariable: $TABLE
              language: regex
              patterns:
"""
    s += pregex(r"""(?m)^[ \t]*(?<A>approval_mode""" + APPROVE + ")", 16)
    s += "          - focus-metavariable: $A\n"
    for table, comment in ((TOML_TABLE, "Dotted or inline tool keys in an [mcp_servers...] table."),
                           (TOML_PREAMBLE, "... or before the first table, on mcp_servers.<name> lines.")):
        s += f"      # {comment}\n      - patterns:\n"
        s += pregex(table, 10)
        s += """          - metavariable-pattern:
              metavariable: $TABLE
              language: regex
              patterns:
                - pattern-either:
"""
        for line in (TOML_DOTTED, TOML_INLINE):
            if table is TOML_PREAMBLE:
                # Only mcp_servers.<name>... lines count before the first table.
                line = line.replace("(?m)", "(?m)(?=^[ \\t]*mcp_servers" + TOML_DOT + ")", 1)
            s += pregex(line, 20)
        s += mvr("$T", TOOL_NAME, 16, literal=True)
        s += "          - focus-metavariable: $A\n"
    s += APPROVE_METADATA
    s += "      technology: [mcp, codex]\n"
    s += "      references:\n" + COMMON_REFS + """        - https://github.com/openai/codex/blob/rust-v0.164.0/codex-rs/config/src/mcp_types.rs
        - https://github.com/openai/codex/blob/rust-v0.164.0/codex-rs/core/src/mcp_tool_call.rs
        - https://learn.chatgpt.com/docs/extend/mcp?surface=cli
"""
    return s


# ---- Claude Code settings ------------------------------------------------------------------

# The same file list as claude-settings-unrestricted-shell (build.py SHARED_PATHS).
CLAUDE_PATHS = """    paths:
      include:
        - ".claude/settings.json"
        - ".claude/settings.local.json"
        - "managed-settings.json"
"""

# mcp__<server> (all its tools), mcp__<server>__* or a glob not limited to read verbs, or a
# named action tool. The server segment must be glob-free: Claude Code skips mcp__* and "*" in
# allow rules, and skips rules with parentheses in settings files.
CLAUDE_ENTRY_BODY = (r"""mcp__ (?: (?!__) [^*?()\s,"'\]] )++ (?: (?![_\w-]) | __ """
                     + tool(r"""[^*?()\s,"'\]]""") + r""" )""")
CLAUDE_ENTRY = rx(r"""^ \s*+ """ + CLAUDE_ENTRY_BODY + r""" (?! [^"]*\( )""")

CLAUDE_MESSAGE = """    message: >-
      This Claude Code allow rule lets the agent call MCP tools without asking. "mcp__github"
      or "mcp__github__*" approves every tool of that server, and a named tool whose name says
      it writes, deletes, sends, merges, or runs something ("mcp__github__merge_pull_request")
      approves that action. Project settings apply once someone trusts the folder, so the rule
      reaches everyone who works in the repository.
""" + WHY + FIX + "\n"


def claude_rule():
    s = header("claude-settings-mcp-auto-approve", "json") + CLAUDE_MESSAGE + CLAUDE_PATHS
    s += """    patterns:
      - pattern-inside: '"permissions": {...}'
      - pattern-inside: '"allow": [...]'
      - pattern: '"$V"'
"""
    s += mvr("$V", CLAUDE_ENTRY, 6, literal=True)
    s += APPROVE_METADATA
    s += "      technology: [claude-code, mcp]\n"
    s += "      references:\n" + COMMON_REFS + """        - https://code.claude.com/docs/en/permissions
        - https://code.claude.com/docs/en/settings-reference
"""
    return s


AUTOSTART_MESSAGE = """    message: >-
      This Claude Code setting starts the project's .mcp.json servers without asking.
      Claude Code normally asks before it uses each project server; enableAllProjectMcpServers
      approves every server in the file, and enabledMcpjsonServers approves the named ones,
      and a committed .claude/settings.json applies both once someone trusts the folder.
      A pull request that adds a server to .mcp.json, or changes the command of an approved
      one, then runs that program on every developer's machine at the next session, with
      their credentials and the agent's tool access. Remove these keys from committed settings
      and let each developer approve servers, which Claude Code records in their own
      .claude/settings.local.json.
"""

AUTOSTART_METADATA = """    metadata:
      category: security
      subcategory: [audit]
      pack-category: agent-config
      owasp-llm:
        - "LLM04:2026 - Supply Chain"
        - "LLM03:2025 - Supply Chain"
      owasp-agentic:
        - "ASI04 - Agentic Supply Chain Vulnerabilities"
        - "ASI05 - Unexpected Code Execution (RCE)"
      owasp-mcp:
        - "MCP04:2025 - Software Supply Chain Attacks & Dependency Tampering"
        - "MCP09:2025 - Shadow MCP Servers"
      owasp-aisvs:
        - "v1.01-C10.4.7 - Schema, Message, and Input Validation"
        - "v1.01-C10.1.2 - Component Integrity"
      mitre-atlas:
        - "AML.T0010.005 - AI Supply Chain Compromise: AI Agent Tool"
      cwe:
        - "CWE-829: Inclusion of Functionality from Untrusted Control Sphere"
      confidence: HIGH
      likelihood: MEDIUM
      impact: HIGH
      technology: [claude-code, mcp]
      references:
        - https://code.claude.com/docs/en/settings-reference
        - https://code.claude.com/docs/en/mcp
        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP09-2025%E2%80%93Shadow-MCP-Servers.md
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM04_SupplyChain.md
"""


def autostart_rule():
    s = header("claude-settings-project-mcp-auto-start", "json") + AUTOSTART_MESSAGE + CLAUDE_PATHS
    s += """    pattern-either:
      - pattern: '"enableAllProjectMcpServers": true'
      # A non-empty list, or one name as a string (Claude Code 2.1.299 reads both).
      - pattern: '"enabledMcpjsonServers": [$FIRST, ...]'
      - patterns:
          - pattern: '"enabledMcpjsonServers": "$NAME"'
          - metavariable-regex:
              metavariable: $NAME
              regex: \\S
"""
    s += AUTOSTART_METADATA
    return s


# ---- Claude Code skill and command front matter --------------------------------------------

SKILL_PATHS = """    paths:
      include:
        # Skills (project, personal, plugin) and commands, which Claude Code runs as skills.
        - "SKILL.md"
        - ".claude/commands/**"
        - "commands/**/*.md"
"""

# An unrestricted shell, the same entries claude-settings-unrestricted-shell flags in settings
# (keep the two in step): Bash, Bash(*), Bash(:*), a rule that starts with a wildcard, or an
# open wildcard (:* or *) right after an interpreter or shell, alone or with its code flag
# (Bash(node:*), Bash(python3 *)), after a runner that launches one (Bash(uv run python:*)), or
# after a command runner on its own (Bash(npx *), Bash(sudo *)). Claude Code docs, 2026-10-28:
# :* and a trailing space-* are the same wildcard, and * matches any text, spaces included.
SHELL_DEFINE = r"""(?(DEFINE)
  (?<sh_interp> (?i: bash | sh | zsh | dash | ksh | mksh | fish | csh | tcsh | pwsh
      | powershell | node | nodejs | deno | bun | tsx | ts-node | python | pypy | py
      | ruby | perl | php | lua | luajit | rscript | osascript | tclsh )
    (?: \d++ (?: \.\d++ )*+ )?+ (?i: \.exe )?+ )
  (?<sh_codeflag> -c | -e | -E | -p | -r | --eval | --print | --command | (?i: -command )
    | eval | run | x )
  (?<sh_run> (?: npx | bunx | pnpx | uvx | env | xargs | sudo | doas | exec | eval
      | npm \s++ (?: exec | x ) | (?: pnpm | yarn ) \s++ (?: exec | dlx )
      | (?: uv | poetry | pipenv | devbox | pipx ) \s++ run | bundle \s++ exec
      | mise \s++ (?: exec | x ) | direnv \s++ exec )
    (?: \s++ --?[\w-]++ )*+ )
  (?<sh_runner> npm | pnpm | yarn | uv | poetry | pipenv | devbox | pipx | bundle | mise
    | direnv )
  (?<sh_path> (?: [^\s()*:'"]* [/\\] )?+ )
  (?<sh_open> \s*+ :\* | \s*+ \* [^)]* )
)"""
SHELL_ENTRY = r"""Bash (?: \( \s*+ (?:
    :\* | \* [^)]*
  | (?: (?&sh_path) (?&sh_run) \s++ )? (?&sh_path) (?&sh_interp) (?: \s++ (?&sh_codeflag) )? (?&sh_open)
  | (?&sh_path) (?: (?&sh_run) | (?&sh_runner) ) (?&sh_open)
)? \s*+ \) )?"""

# One entry of an allowed-tools value (a space- or comma-separated string, a flow list, or a
# block list): an MCP approval as above, or an unrestricted shell as above.
SKILL_ENTRY = rx(SHELL_DEFINE + r"""
(?<! [\w(:*-] )
(?: """ + CLAUDE_ENTRY_BODY + r""" [^\s,"'\]]*+
  | """ + SHELL_ENTRY + r""" )
(?= [\s,"'\]] | $ )""")

SKILL_MESSAGE = """    message: >-
      This skill's allowed-tools front matter lets the agent use broad tools without asking
      while the skill runs: "mcp__github" or "mcp__github__*" approves every tool of that MCP
      server, a named MCP tool whose name says it writes, deletes, sends, merges, or runs
      something approves that action, and Bash, Bash(*), Bash(:*), or an open prefix on an
      interpreter, shell, or command runner (Bash(node:*), Bash(python3 *), Bash(npx *)),
      which approves node -e, python3 -c, or bash -c with any code, approves every shell
      command. Claude Code applies a project skill's allowed-tools even in a folder nobody
      has trusted, including claude -p runs, and the skill decides when it is invoked.
""" + WHY + """List only the
      specific tools the skill needs (Bash(npm test), Bash(node scripts/build.js),
      mcp__github__get_issue), and let
      everything else ask.
"""


def skill_rule():
    s = header("claude-skill-allowed-tools-auto-approve", "regex",
               "    # Regex: the front matter of a Markdown file.\n") + SKILL_MESSAGE + SKILL_PATHS
    s += """    patterns:
      # The front matter: from a leading --- line to the next --- line.
      - pattern-regex: \\A(?:\\x{FEFF})?---[ \\t]*\\r?\\n(?s:.*?)\\r?\\n---[ \\t]*(?:\\r?\\n|\\z)
      # The allowed-tools key and its value: the rest of the line, then indented or list lines.
      - pattern-regex: (?m)^allowed-tools[ \\t]*:[^\\r\\n]*(?:\\r?\\n(?:[ \\t]+[^\\r\\n]*|-[ \\t][^\\r\\n]*|[ \\t]*(?=\\r?\\n)))*
"""
    s += pregex(SKILL_ENTRY, 6)
    s += APPROVE_METADATA.replace(
        """      owasp-agentic:
        - "ASI02 - Tool Misuse and Exploitation"
""", """      owasp-agentic:
        - "ASI02 - Tool Misuse and Exploitation"
        - "ASI05 - Unexpected Code Execution (RCE)"
""")
    s += "      technology: [claude-code, mcp]\n"
    s += "      references:\n" + COMMON_REFS + """        - https://code.claude.com/docs/en/skills
        - https://code.claude.com/docs/en/permissions
"""
    return s


# ---- Cursor --------------------------------------------------------------------------------

CURSOR_PATHS = """    paths:
      include:
        # Cursor CLI: permissions.allow in the project file, and the global file in dotfiles
        # repos or when CURSOR_CONFIG_DIR points at a repo folder.
        - ".cursor/cli.json"
        - ".cursor/cli-config.json"
        - "cursor/cli-config.json"
        # Cursor IDE and CLI: mcpAllowlist; a repository's file is concatenated with the user's
        # (~/.cursor/permissions.json, which a dotfiles repository keeps plain or chezmoi-named).
        - ".cursor/permissions.json"
        - "cursor/permissions.json"
        - "dot_cursor/permissions.json"
"""

# Mcp(server:tool) and "server:tool": any server ("*") is fine as long as the tool part is not
# broad, so Mcp(*:search) stays quiet and Mcp(*:*) or Mcp(datadog:*) does not.
CURSOR_CLI = rx(r"""^ \s*+ Mcp \( \s*+ [^:)]*+ : \s*+ """ + tool(r"""[^*?:)]"""))
CURSOR_ALLOWLIST = rx(r"""^ \s*+ [^:"]*+ : \s*+ """ + tool(r"""[^*?:"]"""))

CURSOR_MESSAGE = """    message: >-
      This Cursor permission lets the agent call MCP tools without asking. Mcp(*:*) in
      .cursor/cli.json, or "*:*" in .cursor/permissions.json mcpAllowlist, approves every MCP
      tool; Mcp(github:*) or "github:*" approves every tool of that server; and a named tool
      whose name says it writes, deletes, sends, merges, or runs something approves that
      action. A repository's .cursor/permissions.json is concatenated with each user's own.
""" + WHY + FIX + "\n"


def cursor_rule():
    s = header("cursor-mcp-auto-approve", "json") + CURSOR_MESSAGE + CURSOR_PATHS
    s += "    pattern-either:\n"
    s += entry_branch(6, ['"permissions": {...}'], "allow", CURSOR_CLI,
                      "Cursor CLI: Mcp(server:tool) in permissions.allow.")
    s += entry_branch(6, [], "mcpAllowlist", CURSOR_ALLOWLIST,
                      "permissions.json: \"server:tool\" in mcpAllowlist.")
    s += APPROVE_METADATA
    s += "      technology: [cursor, mcp]\n"
    s += "      references:\n" + COMMON_REFS + """        - https://cursor.com/docs/cli/reference/permissions
        - https://cursor.com/docs/reference/permissions
"""
    return s


# ---- Claude Agent SDK code -----------------------------------------------------------------

# The SDK passes allowedTools / allowed_tools to Claude Code as allow rules, so the same
# entries count (TS SDK 0.3.309, Python SDK 0.2.173; agent-sdk/permissions docs).
SDK_DIR = {"ts": ROOT / "rules" / "typescript" / "permissions",
           "py": ROOT / "rules" / "python" / "permissions"}

SDK_MESSAGE = """    message: >-
      This Claude Agent SDK allow list lets the agent call MCP tools without any check.
      "mcp__github" or "mcp__github__*" approves every tool of that server, including tools
      the server adds later, and a named tool whose name says it writes, deletes, sends,
      merges, or runs something ("mcp__review__run_command") approves that action. The SDK
      applies {key} entries as Claude Code allow rules before {callback} runs, so
      nothing reviews those calls. A prompt injection in a file, issue, web page, or tool
      result the agent reads can then make it use those tools (push code, post messages,
      change records, run commands) with this process's credentials. Allow named read-only
      tools, and decide on tools that change things in {callback} or a PreToolUse hook (for
      example, allow writes only to the repository being worked on).
"""

# A named list is an allow list unless its name says otherwise.
SDK_NAME = r"(?i)^(?![\w.]*(?:disallow|deny|denied|block|forbid|exclude))[\w.]*allow"


def sdk_metadata(lang):
    meta = APPROVE_METADATA.replace(
        """      # Whole-server approvals are certain; a named tool is judged by the words in its name,
      # which can't see what a server's tool really does.
      confidence: MEDIUM""",
        """      # A headless SDK app has to allow the tools it uses, and in-process tools are the
      # app's own code; whole-server and action-tool approvals are still the calls that
      # nobody reviews, but more of them are deliberate than in shared config.
      confidence: LOW""")
    return meta + "      technology: [claude-agent-sdk, anthropic, mcp]\n" + "      references:\n" + COMMON_REFS + (
        """        - https://code.claude.com/docs/en/agent-sdk/permissions
        - https://code.claude.com/docs/en/agent-sdk/mcp
""" + ("""        - https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk/v/0.3.309
""" if lang == "ts" else """        - https://github.com/anthropics/claude-agent-sdk-python/blob/v0.2.173/src/claude_agent_sdk/_internal/transport/subprocess_cli.py
"""))


def sdk_ts_rule():
    s = header("agent-sdk-mcp-auto-approve-ts", "typescript, javascript")
    s += SDK_MESSAGE.replace("{key}", "allowedTools").replace("{callback}", "canUseTool")
    s += """    patterns:
      - pattern-either:
          # allowedTools: [...] in query options, a subagent, or a helper's options object.
          - pattern: '{..., allowedTools: [..., "$V", ...], ...}'
          # A list kept in a named const (ALLOWED_TOOLS, allowedMcpTools) and passed in.
          - patterns:
              - pattern-either:
                  - pattern: const $NAME = [..., "$V", ...]
                  - pattern: 'const $NAME: $T = [..., "$V", ...]'
                  - pattern: let $NAME = [..., "$V", ...]
              - metavariable-regex:
                  metavariable: $NAME
"""
    s += f"                  regex: {SDK_NAME}\n"
    s += """      # Bypass mode approves everything already; agent-sdk-bypass-permissions-ts reports it.
      - pattern-not-inside: '{..., permissionMode: <... "bypassPermissions" ...>, ...}'
      - focus-metavariable: $V
"""
    s += mvr("$V", CLAUDE_ENTRY, 6, literal=True)
    s += sdk_metadata("ts")
    return s


def sdk_py_rule():
    s = header("agent-sdk-mcp-auto-approve", "python")
    s += SDK_MESSAGE.replace("{key}", "allowed_tools").replace("{callback}", "can_use_tool")
    s += """    patterns:
      - pattern-either:
          # ClaudeAgentOptions(allowed_tools=[...]), the older ClaudeCodeOptions, a helper's
          # keyword, dataclasses.replace(), or an options dict.
          - pattern: $FN(..., allowed_tools=[..., "$V", ...], ...)
          - pattern: '{..., "allowed_tools": [..., "$V", ...], ...}'
          # A list kept in a named constant (ALLOWED_TOOLS) and passed in.
          - patterns:
              - pattern-either:
                  - pattern: $NAME = [..., "$V", ...]
                  - pattern: '$NAME: $T = [..., "$V", ...]'
              - metavariable-regex:
                  metavariable: $NAME
"""
    s += f"                  regex: {SDK_NAME}\n"
    s += """      # Bypass mode approves everything already; agent-sdk-bypass-permissions reports it.
      - pattern-not-inside: $FN(..., permission_mode="bypassPermissions", ...)
      - focus-metavariable: $V
"""
    s += mvr("$V", CLAUDE_ENTRY, 6, literal=True)
    s += sdk_metadata("py")
    return s


# ---- agent-tool-approval-disabled (OpenAI hosted MCP, OpenAI Agents SDK, LangChain HITL) ----

# Human approval switched off for tools in the other agent SDKs (verified 2026-10-24):
#
# - OpenAI Responses API hosted MCP tools ({"type": "mcp", ...}; openai 3.37.0 on PyPI, 7.43.0
#   on npm): require_approval is "always", "never", or {"always" / "never": {"tool_names": [...],
#   "read_only": bool}}. The API asks for approval when it is left out; "never" turns that off.
#   allowed_tools (a list, or {"tool_names", "read_only"}) limits which tools the model sees.
#   Azure AI Projects (2.9.0) MCPTool(server_label=..., require_approval=...) for Foundry agents
#   has the same fields, with MCPToolRequireApproval / MCPToolFilter objects for the filters.
# - Azure AI Agents (azure-ai-agents 1.2.0b6, @azure/ai-agents 1.2.0-beta.2; the 1.1.0 releases
#   have no MCP): McpTool / MCPTool defaults to "always", and set_approval_mode("never") /
#   setApprovalMode("never") or a per-tool {never: {tool_names}} (MCPApprovalPerTool) turns it
#   off; the run-time MCPToolResource takes the same require_approval.
# - Microsoft Agent Framework (agent-framework-openai 1.17.0, agent-framework-foundry 1.15.0,
#   and HostedMCPTool in the agent-framework-core 1.0.0 betas): approval_mode="never_require"
#   becomes require_approval "never" and {"never_require_approval": [...]} a never-filter;
#   no approval_mode leaves the API default. Its local MCP tools never ask by default.
# - OpenAI Agents SDK: Python HostedMCPTool(tool_config={...}) passes that dict to the API
#   (openai-agents 0.24.0) and takes on_approval_request, a callback that answers each approval
#   request with {"approve": bool}. JS hostedMcpTool({serverLabel, serverUrl, requireApproval,
#   onApproval, allowedTools}) (@openai/agents-core 0.21.0) sends require_approval "never" when
#   requireApproval is left out, so a call without it is the same as "never".
#   The local MCPServer classes (Python require_approval=, default None = no approval) and
#   function tools (needs_approval, default False) never ask unless told to, so an explicit
#   "never" there changes nothing and isn't reported.
# - LangChain HumanInTheLoopMiddleware(interrupt_on={tool: True | False | config})
#   (langchain 1.4.7 / langchain 1.5.19 humanInTheLoopMiddleware({interruptOn})): False
#   auto-approves the tool, and so does a config whose `when` predicate returns False. deepagents
#   (0.7.32 / 1.15.1) takes the same map in create_deep_agent(interrupt_on=...) and in each
#   subagent; a user entry overrides the interrupt the agent's filesystem permissions generate,
#   and a subagent's own map replaces the one it would inherit.
#
# Tool names go through the same TOOL test as the MCP auto-approval rules: a never-filter or
# allowed_tools list of read-only names (list_invoices, read_wiki_structure) is the near-miss,
# and so is require_approval "never" on a public documentation server whose tools only search
# and read public docs (the OpenAI MCP guide's own example skips approval for one).

# One entry of a read-only list: a quoted name that TOOL doesn't flag.
RO_ENTRY = r"""["'`] (?! """ + tool(r"""[^*?"'`\n]""") + r""" ) [^"'`\n]*+ ["'`]"""
# At least one name: an empty list means every tool in Azure AI Agents' McpTool.
RO_SKIP = r"""(?: \s++ | , | \#[^\n]*+ | //[^\n]*+ )"""
RO_LIST = (r"""\[ """ + RO_SKIP + r"""*+ """ + RO_ENTRY + r""" (?: """ + RO_SKIP + r""" | """
           + RO_ENTRY + r""" )*+ \]""")
# allowed_tools that only reach read-only tools: a list of read-only names, the same list under
# tool_names / toolNames, or a filter with read_only / readOnly set (a dict, a JS object, or
# Azure's MCPToolFilter(...)).
READ_ONLY_TOOLS = rx(r"""^ (?: """ + RO_LIST + r"""
  | \{ \s*+ ["']?+ (?:tool_names|toolNames) ["']?+ \s*+ : \s*+ """ + RO_LIST + r""" \s*+ ,?+ \s*+ \}
  | \{ [^{}]*? ["']?+ (?:read_only|readOnly) ["']?+ \s*+ : \s*+ (?:True|true) \b [^{}]*+ \}
  | [\w.]++ \( \s*+ tool_names \s*+ = \s*+ """ + RO_LIST + r""" \s*+ ,?+ \s*+ \)
  | [\w.]++ \( [^()]*? \b read_only \s*+ = \s*+ True \b [^()]*+ \)
  ) $""")
# Public documentation servers whose tools only search and read public docs.
DOCS_HOSTS = (r"(?:gitmcp[.]io|mcp[.]deepwiki[.]com|learn[.]microsoft[.]com[/]api[/]mcp"
              r"|developers[.]openai[.]com[/]mcp|mcp[.]context7[.]com|docs[.][a-z0-9.-]+)")
# A string or a constant that resolves to one (no backslashes: see CONTRIBUTING).
DOCS_URL = "=~/^https?:[/][/]" + DOCS_HOSTS + "(?:[/:?#]|$)/"
# The raw text of an f-string or template literal with a run-time part.
DOCS_URL_RAW = r"^(?:[fFrRuU]{0,2})?[\"'`]https?://" + DOCS_HOSTS + r"(?:[/:?#\"'`$]|$)"
# A HITL map key (quoted in Python, bare or quoted in JS) whose name says the tool acts. A glob
# key is just a name there, so globs don't count.
HITL_KEY = rx(r"""^ ["'`]?+ (?: (?! (?&read) ) [^"'`*?] )*? (?&act)""")

APPROVAL_MESSAGE = """    message: >-
      Human approval is switched off for tools this agent can call: {what}. The model's
      tool calls then run with nobody checking them, so a prompt injection in a document,
      ticket, email, web page, or tool result the model reads can make it take those
      actions (send messages, change or delete records, move money, push code) with the
      app's credentials. Keep approval on for tools that change things: leave
      require_approval at "always" (or list only read-only tools under "never"), limit
      allowed_tools to read-only tools, set interrupt_on entries for acting tools to True,
      and make approval callbacks decide from the tool name and arguments instead of
      approving everything.
"""

APPROVAL_METADATA = """    metadata:
      category: security
      subcategory: [audit]
      pack-category: ai-code
""" + LLM + """      owasp-agentic:
        - "ASI09 - Human-Agent Trust Exploitation"
        - "ASI02 - Tool Misuse and Exploitation"
      owasp-aisvs:
        - "v1.01-C9.2.1 - High-Impact Action Approval and Irreversibility Controls"
      mitre-atlas:
        - "AML.T0053 - AI Agent Tool Invocation"
      cwe:
        - "CWE-862: Missing Authorization"
      # The setting is certain; whether the server's tools act is judged from allowed_tools,
      # never-filters, and tool names, which can't see what an unlisted server tool does.
      confidence: MEDIUM
      likelihood: MEDIUM
      impact: HIGH
"""

APPROVAL_REFS = """      references:
        - https://github.com/GenAI-Security-Project/GenAI-Security-Corpus/blob/main/corpus/agentic-top10/2026-final/OWASP-Top-10-for-Agentic-Applications-2026-v1.0.pdf
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md
        - https://developers.openai.com/api/docs/guides/tools-connectors-mcp
"""


def approval_py_rule():
    s = header("agent-tool-approval-disabled", "python", severity="WARNING")
    s += APPROVAL_MESSAGE.replace("{what}", (
        'require_approval "never" on a hosted MCP server (OpenAI Responses API, Agents SDK\n'
        "      HostedMCPTool, Azure AI Foundry MCPTool, Azure AI Agents McpTool\n"
        "      set_approval_mode, or Microsoft Agent Framework approval_mode \"never_require\"),\n"
        "      a never-filter or LangChain /\n"
        "      deepagents interrupt_on entry that auto-approves a tool whose name says it writes,\n"
        "      sends, deletes, or runs something, or an on_approval_request callback that\n"
        "      approves every call"))
    s += """    patterns:
      - pattern-either:
          # require_approval "never" on an MCP tool dict or a keyword-built one (dict(...),
          # Mcp(...), Azure AI Projects MCPTool(...)). server_label is required, so it marks a
          # hosted MCP tool.
          - patterns:
              - pattern-either:
                  - pattern: '{..., "type": "mcp", ..., "require_approval": $RA, ...}'
                  - pattern: '{..., "server_label": $L, ..., "require_approval": $RA, ...}'
                  - pattern: $F(..., server_label=$L, ..., require_approval=$RA, ...)
              - metavariable-regex:
                  metavariable: $RA
                  regex: ^[^{\\[]
              - metavariable-pattern:
                  metavariable: $RA
                  pattern: '"never"'
              - focus-metavariable: $RA
          # Azure AI Agents McpTool (default "always") switched to "never", unless the McpTool
          # it is called on reaches only read-only tools or a documentation server.
          - patterns:
              - pattern: $M.set_approval_mode($RA)
              - metavariable-regex:
                  metavariable: $RA
                  regex: ^[^{\\[]
              - metavariable-pattern:
                  metavariable: $RA
                  pattern: '"never"'
              - pattern-not-inside:
                  patterns:
                    - pattern-either:
                        - pattern: |
                            $M = McpTool(..., allowed_tools=$AT, ...)
                            ...
                        - pattern: |
                            $M = McpTool($L2, $U2, $AT, ...)
                            ...
"""
    s += mvr("$AT", READ_ONLY_TOOLS, 20, literal=True)
    s += """              - pattern-not-inside:
                  patterns:
                    - pattern-either:
                        - pattern: |
                            $M = McpTool(..., server_url=$U, ...)
                            ...
                        - pattern: |
                            $M = McpTool($L2, $U, ...)
                            ...
"""
    s += mvr("$U", DOCS_URL_RAW, 20, literal=True)
    s += """              - focus-metavariable: $RA
          # {"never": {"tool_names": [...]}} listing a tool that acts.
          - patterns:
              - pattern-either:
                  - pattern-inside: '{..., "require_approval": $X, ...}'
                  - pattern-inside: $F(..., require_approval=$X, ...)
                  - pattern-inside: $M.set_approval_mode($X)
              - pattern-either:
                  - pattern: '{..., "never": {..., "tool_names": [..., "$V", ...], ...}, ...}'
                  # Azure: MCPToolRequireApproval(never=MCPToolFilter(tool_names=[...])), and
                  # MCPApprovalPerTool(never=MCPToolList(tool_names=[...])) in Azure AI Agents.
                  - pattern: '$G(..., never=$H(..., tool_names=[..., "$V", ...], ...), ...)'
              - focus-metavariable: $V
"""
    s += mvr("$V", LIST_ENTRY, 14, literal=True)
    s += """          # Microsoft Agent Framework: HostedMCPTool (1.0 betas) and the clients' get_mcp_tool()
          # map approval_mode "never_require" to require_approval "never", and
          # never_require_approval names to a never-filter.
          - patterns:
              - pattern-either:
                  - pattern: HostedMCPTool(..., approval_mode=$AM, ...)
                  - pattern: $P.HostedMCPTool(..., approval_mode=$AM, ...)
                  - pattern: get_mcp_tool(..., approval_mode=$AM, ...)
                  - pattern: $P.get_mcp_tool(..., approval_mode=$AM, ...)
              - metavariable-regex:
                  metavariable: $AM
                  regex: ^[^{\\[]
              - metavariable-pattern:
                  metavariable: $AM
                  pattern: '"never_require"'
              - focus-metavariable: $AM
          - patterns:
              - pattern-either:
                  - pattern-inside: HostedMCPTool(..., approval_mode=$X, ...)
                  - pattern-inside: $P.HostedMCPTool(..., approval_mode=$X, ...)
                  - pattern-inside: get_mcp_tool(..., approval_mode=$X, ...)
                  - pattern-inside: $P.get_mcp_tool(..., approval_mode=$X, ...)
              - pattern: '{..., "never_require_approval": [..., "$V", ...], ...}'
              - focus-metavariable: $V
"""
    s += mvr("$V", LIST_ENTRY, 14, literal=True)
    s += """          # on_approval_request that approves every call: a lambda, or a function whose body
          # has no condition before it returns {"approve": True}.
          - patterns:
              - pattern-inside: $T(..., on_approval_request=$CB, ...)
              - pattern: 'lambda $...P: {..., "approve": True, ...}'
          # A file-wide region from each def to the call costs too much on long modules, so
          # the file passing a callback by name is the gate: {"approve": ...} is the SDK's
          # MCPToolApprovalFunctionResult.
          - patterns:
              - pattern-regex: (?s)\\A(?=.*?\\bon_approval_request\\s*+=\\s*+[A-Za-z_]).*
              - pattern: 'return {..., "approve": True, ...}'
              - pattern-either:
                  - pattern-inside: |
                      def $FN(...):
                        ...
                  - pattern-inside: |
                      async def $FN(...):
                        ...
              - pattern-not-inside: |
                  def $FN(...):
                    ...
                    if $C:
                      ...
                    ...
              - pattern-not-inside: |
                  async def $FN(...):
                    ...
                    if $C:
                      ...
                    ...
              - pattern-not-inside: |
                  def $FN(...):
                    ...
                    raise $E
                    ...
              - pattern-not-inside: |
                  async def $FN(...):
                    ...
                    raise $E
                    ...
          # interrupt_on entries (HumanInTheLoopMiddleware, create_deep_agent, a subagent dict)
          # set to False or to a config whose `when` always returns False.
          - patterns:
              - pattern-either:
                  - pattern: '$F(..., interrupt_on={..., $K: False, ...}, ...)'
                  - pattern: '$F(..., interrupt_on={..., $K: {..., "when": lambda $...P: False, ...}, ...}, ...)'
                  - pattern: 'HumanInTheLoopMiddleware({..., $K: False, ...}, ...)'
                  - pattern: '{..., "interrupt_on": {..., $K: False, ...}, ...}'
                  - pattern: '{..., "interrupt_on": {..., $K: {..., "when": lambda $...P: False, ...}, ...}, ...}'
                  # A map kept in a variable or constant and passed in later.
                  - patterns:
                      - pattern-regex: (?s)\\A(?=.*?\\binterrupt_on\\b|.*?HumanInTheLoopMiddleware\\().*
                      - pattern-either:
                          - pattern: '$NAME = {..., $K: False, ...}'
                          - pattern: '$NAME: $TY = {..., $K: False, ...}'
                      - pattern-either:
                          - pattern-inside: |
                              $NAME = {..., $K2: False, ...}
                              ...
                              $F(..., interrupt_on=$NAME, ...)
                          - pattern-inside: |
                              $NAME = {..., $K2: False, ...}
                              ...
                              HumanInTheLoopMiddleware($NAME, ...)
                          - pattern-inside: |
                              $NAME = {..., $K2: False, ...}
                              ...
                              {..., "interrupt_on": $NAME, ...}
              - focus-metavariable: $K
"""
    s += mvr("$K", HITL_KEY, 14, literal=True)
    s += py_exclusions()
    s += APPROVAL_METADATA
    s += "      technology: [openai, openai-agents, langchain, langgraph, deepagents, mcp]\n"
    s += APPROVAL_REFS + """        - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/types/responses/tool_param.py
        - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/tool.py
        - https://github.com/langchain-ai/langchain/blob/langchain%3D%3D1.4.7/libs/langchain_v1/langchain/agents/middleware/human_in_the_loop.py
        - https://pypi.org/project/deepagents/0.7.32/
        - https://pypi.org/project/azure-ai-projects/2.9.0/
        - https://pypi.org/project/azure-ai-agents/1.2.0b6/
        - https://pypi.org/project/agent-framework-core/1.0.0b251016/
        - https://pypi.org/project/agent-framework-openai/1.17.0/
"""
    return s


def py_exclusions():
    """The near-misses, as the whole tool dict or keyword call (checked before focus)."""
    s = """      # Only read-only tools are reachable, or the server is a public documentation server.
      - pattern-not-inside:
          patterns:
            - pattern-either:
                - pattern: '{..., "allowed_tools": $AT, ...}'
                - pattern: $F(..., allowed_tools=$AT, ...)
"""
    s += mvr("$AT", READ_ONLY_TOOLS, 12, literal=True)
    s += f"""      - pattern-not-inside: '{{..., "server_url": "{DOCS_URL}", ...}}'
      - pattern-not-inside: '$F(..., server_url="{DOCS_URL}", ...)'
      - pattern-not-inside: '$F(..., url="{DOCS_URL}", ...)'
      - pattern-not-inside:
          patterns:
            - pattern-either:
                - pattern: '{{..., "server_url": $U, ...}}'
                - pattern: $F(..., server_url=$U, ...)
                - pattern: $F(..., url=$U, ...)
"""
    s += mvr("$U", DOCS_URL_RAW, 12, literal=True)
    return s


def approval_ts_rule():
    s = header("agent-tool-approval-disabled-ts", "typescript, javascript", severity="WARNING")
    s += APPROVAL_MESSAGE.replace("{what}", (
        'require_approval "never" on a hosted MCP server (OpenAI Responses API), an OpenAI\n'
        "      Agents SDK hostedMcpTool() without requireApproval (it defaults to \"never\") or with\n"
        '      "never", Azure AI Agents MCPTool.setApprovalMode("never"), a never-filter or LangChain / deepagents interruptOn entry that\n'
        "      auto-approves a tool whose name says it writes, sends, deletes, or runs something,\n"
        "      or an onApproval callback that approves every call"))
    s += """    patterns:
      - pattern-either:
          # require_approval "never" on a Responses API MCP tool object.
          - patterns:
              - pattern-either:
                  - pattern: '{..., type: "mcp", ..., require_approval: $RA, ...}'
                  - pattern: '{..., server_label: $L, ..., require_approval: $RA, ...}'
              - metavariable-regex:
                  metavariable: $RA
                  regex: ^[^{\\[]
              - metavariable-pattern:
                  metavariable: $RA
                  pattern: '"never"'
              - focus-metavariable: $RA
          # requireApproval "never": hostedMcpTool() options, an Azure AI Agents MCP tool
          # resource, or MCPTool.setApprovalMode() (Azure AI Agents, default "always").
          - patterns:
              - pattern-either:
                  - pattern: '{..., serverLabel: $L, ..., requireApproval: $RA, ...}'
              - metavariable-regex:
                  metavariable: $RA
                  regex: ^[^{\\[]
              - metavariable-pattern:
                  metavariable: $RA
                  pattern: '"never"'
              - focus-metavariable: $RA
          # Azure AI Agents MCPTool (default "always") switched to "never", unless the MCPTool
          # it is called on reaches only read-only tools or a documentation server.
          - patterns:
              - pattern: $M.setApprovalMode($RA)
              - metavariable-regex:
                  metavariable: $RA
                  regex: ^[^{\\[]
              - metavariable-pattern:
                  metavariable: $RA
                  pattern: '"never"'
              - pattern-not-inside:
                  patterns:
                    - pattern: |
                        const $M = new MCPTool($L2, $U2, $AT, ...);
                        ...
"""
    s += mvr("$AT", READ_ONLY_TOOLS, 20, literal=True)
    s += """              - pattern-not-inside:
                  patterns:
                    - pattern: |
                        const $M = new MCPTool($L2, $U, ...);
                        ...
"""
    s += mvr("$U", DOCS_URL_RAW, 20, literal=True)
    s += """              - focus-metavariable: $RA
          # hostedMcpTool({...}) without requireApproval sends "never".
          - patterns:
              - pattern-either:
                  - pattern-inside: hostedMcpTool($OPTS)
                  - pattern-inside: $NS.hostedMcpTool($OPTS)
              - pattern: '{..., serverLabel: $L, ...}'
              - pattern-not: '{..., requireApproval: $X, ...}'
              - pattern-not: '{..., ...$SPREAD, ...}'
          # The same, with shared options spread in from a const object in this file that sets
          # no requireApproval either. Other spreads (a parameter, an import) may carry it.
          - patterns:
              - pattern-either:
                  - pattern-inside: hostedMcpTool($OPTS)
                  - pattern-inside: $NS.hostedMcpTool($OPTS)
              - pattern: '{..., serverLabel: $L, ...}'
              - pattern-inside: '{..., ...$D, ...}'
              - pattern-inside: |
                  const $D = $DOBJ;
                  ...
              # A bare object pattern parses as a block inside metavariable-pattern, so test the
              # const's text: an object literal with no requireApproval key and no spread.
              - metavariable-regex:
                  metavariable: $DOBJ
                  regex: '^\\{(?![\\s\\S]*\\brequireApproval\\b)(?![\\s\\S]*\\.\\.\\.)'
              - pattern-not: '{..., requireApproval: $X, ...}'
              - pattern-not: '{..., ...$OTHER, ..., ...$D, ...}'
              - pattern-not: '{..., ...$D, ..., ...$OTHER, ...}'
          # A never-filter listing a tool that acts.
          - patterns:
              - pattern-either:
                  - pattern: '{..., require_approval: {..., never: {..., tool_names: [..., "$V", ...], ...}, ...}, ...}'
                  - pattern: '{..., requireApproval: {..., never: {..., toolNames: [..., "$V", ...], ...}, ...}, ...}'
                  - pattern: '$M.setApprovalMode({..., never: {..., toolNames: [..., "$V", ...], ...}, ...})'
              - focus-metavariable: $V
"""
    s += mvr("$V", LIST_ENTRY, 14, literal=True)
    s += """          # onApproval that approves every call.
          - patterns:
              - pattern-either:
                  - pattern-inside: 'hostedMcpTool({..., onApproval: $CB, ...})'
                  - pattern-inside: '$NS.hostedMcpTool({..., onApproval: $CB, ...})'
              - pattern-either:
                  - pattern: '($...P) => ({..., approve: true, ...})'
                  - pattern: 'async ($...P) => ({..., approve: true, ...})'
                  - pattern: '($...P) => { return {..., approve: true, ...}; }'
                  - pattern: 'async ($...P) => { return {..., approve: true, ...}; }'
          - patterns:
              - pattern-either:
                  - pattern-inside: |
                      function $FN(...) { return {..., approve: true, ...}; }
                      ...
                  - pattern-inside: |
                      async function $FN(...) { return {..., approve: true, ...}; }
                      ...
                  - pattern-inside: |
                      const $FN = ($...P) => ({..., approve: true, ...});
                      ...
                  - pattern-inside: |
                      const $FN = async ($...P) => ({..., approve: true, ...});
                      ...
              - pattern-either:
                  - pattern: 'hostedMcpTool({..., onApproval: $FN, ...})'
                  - pattern: '$NS.hostedMcpTool({..., onApproval: $FN, ...})'
          # interruptOn entries (humanInTheLoopMiddleware, createDeepAgent, a subagent) set to
          # false or to a config whose `when` always returns false.
          - patterns:
              - pattern-either:
                  - pattern: '{..., interruptOn: {..., $K: false, ...}, ...}'
                  - pattern: '{..., interruptOn: {..., $K: {..., when: ($...P) => false, ...}, ...}, ...}'
                  - patterns:
                      - pattern-inside: |
                          const $NAME = {...};
                          ...
                          <... {..., interruptOn: $NAME, ...} ...>;
                      - pattern-either:
                          - pattern: 'const $NAME = {..., $K: false, ...};'
                          - pattern: 'const $NAME: $TY = {..., $K: false, ...};'
              - focus-metavariable: $K
"""
    s += mvr("$K", HITL_KEY, 14, literal=True)
    s += """      # Only read-only tools are reachable, or the server is a public documentation server.
      - pattern-not-inside:
          patterns:
            - pattern-either:
                - pattern: '{..., allowed_tools: $AT, ...}'
                - pattern: '{..., allowedTools: $AT, ...}'
"""
    s += mvr("$AT", READ_ONLY_TOOLS, 12, literal=True)
    s += f"""      - pattern-not-inside: '{{..., server_url: "{DOCS_URL}", ...}}'
      - pattern-not-inside: '{{..., serverUrl: "{DOCS_URL}", ...}}'
      - pattern-not-inside:
          patterns:
            - pattern-either:
                - pattern: '{{..., server_url: $U, ...}}'
                - pattern: '{{..., serverUrl: $U, ...}}'
"""
    s += mvr("$U", DOCS_URL_RAW, 12, literal=True)
    s += APPROVAL_METADATA
    s += "      technology: [openai, openai-agents, langchainjs, deepagents, mcp, node]\n"
    s += APPROVAL_REFS + """        - https://www.npmjs.com/package/openai/v/7.43.0
        - https://github.com/openai/openai-agents-js/blob/v0.21.0/packages/agents-core/src/tool.ts
        - https://github.com/openai/openai-agents-js/blob/v0.21.0/packages/agents-core/src/utils/mcpApproval.ts
        - https://www.npmjs.com/package/langchain/v/1.5.19
        - https://www.npmjs.com/package/deepagents/v/1.15.1
        - https://www.npmjs.com/package/@azure/ai-agents/v/1.2.0-beta.2
"""
    return s


def render() -> dict[Path, str]:
    """The rule files and the content this script generates for each."""
    return {
        RULE_DIR / "mcp-config-auto-approve.yaml": json_rule(),
        RULE_DIR / "mcp-config-auto-approve-toml.yaml": toml_rule(),
        RULE_DIR / "claude-settings-mcp-auto-approve.yaml": claude_rule(),
        RULE_DIR / "claude-settings-project-mcp-auto-start.yaml": autostart_rule(),
        RULE_DIR / "claude-skill-allowed-tools-auto-approve.yaml": skill_rule(),
        RULE_DIR / "cursor-mcp-auto-approve.yaml": cursor_rule(),
        SDK_DIR["ts"] / "agent-sdk-mcp-auto-approve-ts.yaml": sdk_ts_rule(),
        SDK_DIR["py"] / "agent-sdk-mcp-auto-approve.yaml": sdk_py_rule(),
        SDK_DIR["ts"] / "agent-tool-approval-disabled-ts.yaml": approval_ts_rule(),
        SDK_DIR["py"] / "agent-tool-approval-disabled.yaml": approval_py_rule(),
    }


def main() -> int:
    for path, content in render().items():
        if not path.exists() or path.read_text() != content:
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
