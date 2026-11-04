#!/usr/bin/env python3
"""Generate the mcp-config-hidden-path-command rule files from one set of path regexes.

The rules flag a stdio MCP server that runs a program from a hidden place under the user's home
directory: a dot-named folder directly inside another dot-named folder (~/.config/.cache/.sys/...),
or a dot-named script (~/.x/.server.py). The hidden path can be the command, a script in args, a
cwd the server then runs a relative script from, or a Node loader flag in env (NODE_OPTIONS
--require / --import / --loader / -r naming the file). That is the stdio shape of the August 2026
Deadbugz campaign, whose pull requests ran python on ~/.config/.cache/.sys/.deadbug-mcp.py.

cwd is read by Codex (TOML), VS Code (JSON + .code-workspace), Cline and Continue; Zed's
context-server schema has no cwd, so the cwd check is absent from the Zed-only path, and so is
Claude Code's (an inline subagent server takes .mcp.json's command, args and env; v2.1.310), so
the subagent front matter rule has no cwd check either.

A single dot folder under home is left alone: that is where real runners and scripts live
(~/.local/bin/uvx, ~/.nvm/versions/node/v22/bin/node, ~/.bun/bin/bun, ~/.cargo/bin,
~/.pyenv/shims, ~/.volta, ~/.claude/scripts/x.sh). So are virtualenvs and .local folders inside
a dot folder (~/.tools/.venv/bin/python, Doom Emacs's ~/.emacs.d/.local/), and dot files that
aren't scripts (--env-file ~/.config/x/.env).

The format scaffolding (file paths, server scopes, the TOML and JSONC extractors) comes from
gen_mcp_unpinned.py and gen_mcp_plaintext_secret.py, so every MCP config family scans the same
files and servers.

Edit this script, not the rule files. scripts/build.py regenerates them, and
scripts/build.py --check fails when a rule file differs from what this script produces.

Usage:
    python3 scripts/gen_mcp_hidden_path.py    # rewrite the rule files
"""

from __future__ import annotations

import sys
from pathlib import Path

from gen_mcp_plaintext_secret import TOML_Q, TOML_STRING, TOML_TABLES, YAML_SCALAR
from gen_mcp_unpinned import (JSON_PATHS, JSON_SCOPE, JSONC_ARGS, JSONC_LINES, JSONC_MCP,
                              JSONC_SERVER, JSONC_STRING, SUBAGENT_NOTE, SUBAGENT_PATHS,
                              SUBAGENT_REFS, SUBAGENT_TRUST, TOML_ENABLED, TOML_EXTRACT, TOML_PATHS,
                              TOML_PREFIX, TOML_SERVERS, WORKSPACE_PATHS, YAML_PATHS, ind, mvr,
                              pregex, subagent_patterns)

ROOT = Path(__file__).resolve().parent.parent
RULE_DIR = ROOT / "rules" / "agent-config" / "supply-chain"
RULE_ID = "mcp-config-hidden-path-command"

# ---- path regexes --------------------------------------------------------------------------

DEFINE = r"""(?(DEFINE)
  # A path separator: / or \, which JSON, TOML basic strings and YAML double-quoted strings
  # write doubled. A backslash before a quote escapes the quote (bash -c "node \"$HOME/...\"").
  (?<sep> / | \\{1,2}+(?!["']) )
  # One path segment. Spaces are allowed; ; & | and ` end it, as in a shell line.
  (?<seg> [^/\\"'\n;&|`]++ )
  # A hidden (dot-named) segment, not . or ..
  (?<hid> \. [^./\\"'\s;&|`] [^/\\"'\n;&|`]*+ )
  # Dot folders that legitimately sit in another one: virtualenvs (~/.mcp-tools/.venv/bin/python)
  # and .local, which tools mirror inside their own folder (Doom Emacs's ~/.emacs.d/.local/,
  # a dotfiles checkout's ~/.dotfiles/.local/bin/).
  (?<usual> \.venv[\w.-]*+ | \.virtualenvs?+ | \.local )
  # The user's home directory, however the config spells it: ~, $HOME and ${HOME} (Claude
  # Code, Gemini CLI), ${env:HOME} and ${userHome} (VS Code), %USERPROFILE% (Windows),
  # $env:USERPROFILE (PowerShell), or a literal /Users/<name>, /home/<name>, C:\Users\<name>.
  (?<home> (?: ~[\w.-]*+
      | \$HOME\b | \$\{HOME\} | \$\{env:(?:HOME|USERPROFILE)\} | \$env:(?:HOME|USERPROFILE)\b
      | \$\{userHome\} | (?i:%HOMEDRIVE%)?+(?i:%HOMEPATH%)
      | (?i:%(?:USERPROFILE|APPDATA|LOCALAPPDATA)%)
      | (?:/mnt/[A-Za-z]|[A-Za-z]:)?+ (?&sep) (?:Users|home) (?&sep) [^/\\"'\n;&|`]++
      | /root | /var/root )
    (?=(?&sep)|["']?+$) )
  # A script or program file name ending.
  (?<ext> \. (?i: py[cwz]? | [cm]?js | [cm]?ts | jsx | tsx | sh | bash | zsh | ksh | fish
    | psm?1 | bat | cmd | vbs | exe | com | scr | rb | pl | php | lua | jar | wasm | so | dylib
    | dll | bin | run | appimage | command ) )
  # Where a script name ends inside a longer string.
  (?<end> (?= [\s"'\\,;)&|`\]] | $ ) )
  # A path starts the string, or follows a space, quote, = ( , ; & | ` or [.
  (?<start> (?<! [^\s"'=(,;&|`\[] ) )
)"""

# A script under home, anywhere in a string: the whole argument, --script=..., or a word of a
# shell line (bash -c "python3 ~/.config/.cache/.sys/.x.py").
ARG_BODY = r"""(?&start) (?&home) (?&sep) (?: (?&seg) (?&sep) )*?
(?: # A dot folder directly inside another dot folder (not one of those), then the script.
    (?&hid) (?&sep) (?! (?&usual) (?&sep) ) (?&hid) (?&sep) (?: (?&seg) (?&sep) )*+
    [^/\\"'\s;&|`]*? (?&ext) (?&end)
    # A dot-named script. File names hold no spaces here, so prose (copy it to ~/.mcp.json
    # and run setup.ps1) doesn't read as one.
  | \. [^./\\"'\s;&|`] [^/\\"'\s;&|`]*? (?&ext) (?&end) )"""

# The command is the program itself, so any file name counts.
CMD_BODY = r"""["']?+ (?&home) (?&sep) (?: (?&seg) (?&sep) )*?
(?: (?&hid) (?&sep) (?! (?&usual) (?&sep) ) (?&hid) (?&sep) (?: (?&seg) (?&sep) )*+ (?&seg)
  | (?&hid) ) ["']?+ $"""

ARG = rf"""(?x)
{DEFINE}
^ .*? {ARG_BODY}"""

CMD = rf"""(?x)
{DEFINE}
# The whole command is the path, or the command is a shell line that runs such a script.
^ (?: {CMD_BODY}
  | .*? {ARG_BODY} )"""

# A Codex server's command, from $SRV (see gen_mcp_unpinned.TOML_EXTRACT); binds V.
TOML_CMD = (r"""(?ms)\A(?=[ \t]*""" + TOML_PREFIX + r""").*?(?:^|[{,])[ \t]*\k<P>command[ \t]*=[ \t]*"""
            + TOML_Q)
# A code-workspace server's command, outside comments; binds V.
JSONC_CMD = r'''\A''' + JSONC_LINES + r'''"command"\s*+:\s*+"(?<V>(?:[^"\\\n]|\\.)*+)"'''

# A working directory (cwd) that is a hidden home folder: a dot folder directly inside another
# one (~/.config/.cache/.sys). A single dot folder (~/.cache, ~/.config) is an ordinary place
# and stays quiet, so the server is only flagged when the folder itself is hidden-in-hidden and
# a relative script is run from it (CWD + REL together).
CWD_DIR = r"""(?x)
{DEFINE}
^ ["']?+ (?&home) (?&sep) (?: (?&seg) (?&sep) )*?
(?&hid) (?&sep) (?! (?&usual) (?&sep) ) (?&hid) (?&sep)?+ ["']?+ $""".replace("{DEFINE}", DEFINE)

# A relative path to a script or program file, run against cwd: not home, not absolute, not a
# drive, not an option flag, not an npm scope or a package spec. The extension is required, so
# a package name (@scope/x@1.2.3, pkg==1.2.3, helpdesk-mcp) or a bare directory (./docs) is
# left alone.
REL = r"""(?x)
{DEFINE}
^ ["']?+
(?! (?&home) | (?&sep) | [A-Za-z]:(?&sep) | [-@] )
[^"'\n]*? (?&ext) ["']?+ $""".replace("{DEFINE}", DEFINE)

# A Node interpreter-loader option in an env value that names a hidden home script: NODE_OPTIONS
# (or any value) carrying --require / -r / --import / --loader / --experimental-loader pointing
# at a dot-in-dot or dot-named file under home. The flag must name the file, so PYTHONPATH and
# other directory lists (no flag) stay quiet.
ENV_LOADER = r"""(?x)
{DEFINE}
^ .*? (?<![\w-]) (?: --(?:require|import|loader|experimental-loader) | -r ) [=\s]++ ["']?+
{ARG_BODY}""".replace("{DEFINE}", DEFINE).replace("{ARG_BODY}", ARG_BODY)

# The bodies of CWD_DIR / REL without the whole-value anchors, to embed inside the regex
# scanners that read one server's text ($SRV in the TOML and workspace rules).
CWD_DIR_INNER = (r"""(?&home) (?&sep) (?: (?&seg) (?&sep) )*?"""
                 r""" (?&hid) (?&sep) (?! (?&usual) (?&sep) ) (?&hid) (?&sep)?+""")
REL_INNER = r"""(?! (?&home) | (?&sep) | [A-Za-z]:(?&sep) | [-@] ) [^"'\n]*? (?&ext)"""
ENV_LOADER_INNER = (r"""(?<![\w-]) (?: --(?:require|import|loader|experimental-loader) | -r )"""
                    r""" [=\s]++ ["']?+ """ + ARG_BODY)

# A Codex server's text ($SRV) whose cwd is a hidden home folder and which runs a relative
# script (as the command or an args element). Binds V to the cwd value, for focus.
TOML_CWD = (r"""(?msx)
{DEFINE}
\A
(?= (?s:.*?) (?:^|[{,]) [ \t]* (?:[\w".'-]+ [ \t]* \. [ \t]*)? cwd [ \t]* = [ \t]*
    (?<Q>["']) (?<V> {CWD} ) \k<Q> )
(?= (?s:.*?) (?: command [ \t]* = [ \t]* | [\[,] [ \t]* (?:\#[^\n]*\n[ \t]*)? )
    (?<R>["']) {REL} \k<R> )"""
    .replace("{DEFINE}", DEFINE).replace("{CWD}", CWD_DIR_INNER).replace("{REL}", REL_INNER))

# A Codex server's text ($SRV) with an env value that carries a Node loader flag to a hidden
# home script. env is written inline (env = { NODE_OPTIONS = "..." }) or as a sub-table
# ([mcp_servers.<name>.env]); both arrive here through TOML_TABLES' $TABLE.
TOML_ENV = (r"""(?msx)
{DEFINE}
(?s:.*?) (?<Q>["']) (?<V> [^"'\n]*? {ENV} ) \k<Q>"""
    .replace("{DEFINE}", DEFINE).replace("{ENV}", ENV_LOADER_INNER.replace("^ .*?", "")))

# The JSONC (code-workspace) twins, read over one server object ($SRV).
JSONC_CWD = (r"""(?x)
{DEFINE}
\A (?= """ + JSONC_LINES + r""" "cwd" \s*+:\s*+ "(?<V> {CWD} )" )
(?= """ + JSONC_LINES + r""" "(?:command|args)" \s*+:\s*+ (?s:.*?) "{REL}" )""")
JSONC_CWD = (JSONC_CWD.replace("{DEFINE}", DEFINE).replace("{CWD}", CWD_DIR_INNER)
             .replace("{REL}", REL_INNER))

# ---- rule text -----------------------------------------------------------------------------

MESSAGE = """    message: >-
      This MCP server runs a program from a hidden place in the user's home directory: a
      dot-named folder inside another one (~/.config/.cache/.sys/), or a dot-named script,
      named in the command, in an argument, as a cwd the server then runs a relative script
      from, or through a Node loader flag in env (NODE_OPTIONS --require/--import). The config
      can't install that file and nothing in the project shows what it does, so the server is
      whatever someone put at that path, hidden from a plain directory listing, and it runs
      with the developer's credentials and the agent's tool access. In August 2026 the Deadbugz
      campaign opened pull requests adding a stdio server that ran python on
      ~/.config/.cache/.sys/.deadbug-mcp.py. Don't merge a server that points at a file nobody
      can review: run it from a pinned package (npx "pkg@1.2.3", uvx "pkg==1.2.3") or from a
      script committed to this repository, and keep personal servers in user-level config.
"""

SYNC_NOTE = """# Generated by scripts/gen_mcp_hidden_path.py, which holds the path regexes shared by the
# mcp-config-hidden-path-command rules for JSON, Continue YAML, Codex TOML, VS Code workspace
# files and Claude Code subagent front matter, and takes the file paths from
# scripts/gen_mcp_unpinned.py. Edit the script and run scripts/build.py; build.py --check fails
# if this file drifts.
"""

SUBAGENT_MESSAGE = """    message: >-
      This subagent's inline MCP server runs a program from a hidden place in the user's home
      directory: a dot-named folder inside another one (~/.config/.cache/.sys/), or a
      dot-named script, named in the command, in an argument, or through a Node loader flag in
      env (NODE_OPTIONS --require/--import). The file can't install that program and nothing in the project
      shows what it does, so the server is whatever someone put at that path, hidden from a
      plain directory listing, and it runs with the developer's credentials and the agent's
      tool access.
""" + SUBAGENT_TRUST + """      In August 2026 the Deadbugz campaign opened pull requests adding a stdio server that ran
      python on ~/.config/.cache/.sys/.deadbug-mcp.py. Don't merge a server that points at a
      file nobody can review: run it from a pinned package (npx "pkg@1.2.3", uvx
      "pkg==1.2.3") or from a script committed to this repository, and keep personal servers
      in ~/.claude/agents/ or user-level config.
"""

TECHNOLOGY = {
    "json": "[mcp, claude-code, claude-desktop, cursor, vscode, cline, windsurf, gemini-cli, continue, zed]",
    "yaml": "[mcp, continue]",
    "toml": "[mcp, codex]",
    "workspace": "[mcp, vscode]",
    "subagent": "[mcp, claude-code]",
}

COMMON_REFS = """        - https://www.pillar.security/blog/deadbugz-currently-active-mcp-supply-chain-campaign
        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP04-2025%E2%80%93Software-Supply-Chain-Attacks%26Dependency-Tampering.md
        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP09-2025%E2%80%93Shadow-MCP-Servers.md
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM04_SupplyChain.md
"""

FORMAT_REFS = {
    "json": """        - https://code.claude.com/docs/en/mcp
        - https://cursor.com/docs/context/mcp
        - https://code.visualstudio.com/docs/copilot/reference/mcp-configuration
        - https://code.visualstudio.com/docs/reference/variables-reference
        - https://docs.devin.ai/desktop/cascade/mcp
        - https://geminicli.com/docs/tools/mcp-server/
        - https://docs.cline.bot/mcp/configuring-mcp-servers
        - https://docs.continue.dev/customize/deep-dives/mcp
        - https://github.com/zed-industries/zed/blob/v1.25.2/crates/settings_content/src/project.rs
""",
    "yaml": """        - https://docs.continue.dev/customize/deep-dives/mcp
        - https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/packages/config-yaml/src/schemas/mcp/index.ts
""",
    "toml": """        - https://learn.chatgpt.com/docs/extend/mcp?surface=cli
        - https://github.com/openai/codex/blob/342ed69a174c206c1de52a59491b131e0753cfa5/codex-rs/config/src/mcp_types.rs
""",
    "workspace": """        - https://code.visualstudio.com/docs/copilot/reference/mcp-configuration
        - https://code.visualstudio.com/docs/reference/variables-reference
        - https://github.com/microsoft/vscode/blob/1.143.1/src/vs/platform/mcp/common/mcpResourceScannerService.ts
""",
    "subagent": SUBAGENT_REFS,
}

SUFFIX = {"json": "", "yaml": "-yaml", "toml": "-toml", "workspace": "-workspace",
          "subagent": "-subagent"}


def metadata(fmt):
    return f"""    metadata:
      category: security
      subcategory: [audit]
      pack-category: agent-config
      owasp-llm:
        - "LLM04:2026 - Supply Chain"
        - "LLM03:2025 - Supply Chain"
      owasp-agentic:
        - "ASI04 - Agentic Supply Chain Vulnerabilities"
      owasp-mcp:
        - "MCP04:2025 - Software Supply Chain Attacks & Dependency Tampering"
        - "MCP09:2025 - Shadow MCP Servers"
      owasp-aisvs:
        - "v1.01-C10.1.1 - Component Integrity"
      mitre-atlas:
        - "AML.T0010.005 - AI Supply Chain Compromise: AI Agent Tool"
      cwe:
        - "CWE-829: Inclusion of Functionality from Untrusted Control Sphere"
      # In about 2,300 home paths from public MCP configs (GitHub code search, 2026-10-23),
      # programs sat in one dot folder (~/.local/bin, ~/.nvm, ~/.claude/scripts); a dot
      # folder inside another was a virtualenv or Doom Emacs's .local, both excluded. Other
      # tools that nest dot folders would still match, so check where the file came from.
      confidence: MEDIUM
      likelihood: MEDIUM
      impact: HIGH
      technology: {TECHNOLOGY[fmt]}
      references:
""" + COMMON_REFS + FORMAT_REFS[fmt]


def header(fmt, lang):
    s = f"rules:\n  - id: {RULE_ID}{SUFFIX[fmt]}\n"
    if lang == "regex":
        s += ("    # Regex, not a parser: OpenGrep has no TOML support.\n" if fmt == "toml" else
              "    # Regex, not JSON: OpenGrep's JSON parser skips *.code-workspace files (unknown\n"
              "    # extension), even when paths.include names them.\n")
    elif fmt == "subagent":
        s += SUBAGENT_NOTE
    s += ind(SYNC_NOTE, 4)
    s += f"    languages: [{lang}]\n    severity: WARNING\n"
    s += SUBAGENT_MESSAGE if fmt == "subagent" else MESSAGE
    return s


def json_rule():
    s = header("json", "json") + JSON_PATHS + "    patterns:\n" + JSON_SCOPE
    s += "      - pattern-either:\n"
    s += "          # The program the client starts.\n"
    s += "          - patterns:\n              - pattern: '\"command\": \"$V\"'\n"
    s += mvr("$V", CMD, 14, literal=True)
    s += "          # A script the program is given.\n"
    s += "          - patterns:\n              - pattern-inside: '\"args\": [...]'\n"
    s += "              - pattern: '\"$V\"'\n"
    s += mvr("$V", ARG, 14, literal=True)
    s += "          # cwd is a hidden home folder and a relative program is the command.\n"
    s += "          - patterns:\n"
    s += "              - pattern-inside: '{..., \"command\": \"$R\", ...}'\n"
    s += "              - pattern: '\"cwd\": \"$V\"'\n"
    s += mvr("$V", CWD_DIR, 14, literal=True)
    s += mvr("$R", REL, 14, literal=True)
    s += "          # cwd is a hidden home folder and a relative script in args is run from it.\n"
    s += "          - patterns:\n"
    s += "              - pattern-inside: '{..., \"args\": [..., \"$R\", ...], ...}'\n"
    s += "              - pattern: '\"cwd\": \"$V\"'\n"
    s += mvr("$V", CWD_DIR, 14, literal=True)
    s += mvr("$R", REL, 14, literal=True)
    s += "          # A Node loader flag in env names a hidden home script.\n"
    s += "          - patterns:\n              - pattern-inside: '\"env\": {...}'\n"
    s += "              - pattern: '\"$K\": \"$V\"'\n"
    s += mvr("$V", ENV_LOADER, 14, literal=True)
    s += "      - focus-metavariable: $V\n" + metadata("json")
    return s


def yaml_checks(n, cwd=True):
    """The YAML checks, as pattern-either branches at indent n (Continue and subagents)."""
    pad = " " * n
    out = f"{pad}# The program the client starts.\n"
    out += f"{pad}- patterns:\n{pad}    - pattern: 'command: $V'\n"
    out += mvr("$V", YAML_SCALAR, n + 4, literal=True)
    out += mvr("$V", CMD, n + 4, literal=True)
    out += f"{pad}# A script the program is given.\n"
    out += f"{pad}- patterns:\n{pad}    - pattern-inside: 'args: [...]'\n"
    out += f"{pad}    - pattern: $V\n"
    out += mvr("$V", YAML_SCALAR, n + 4, literal=True)
    out += mvr("$V", ARG, n + 4, literal=True)
    if cwd:
        out += yaml_cwd_checks(n)
    out += f"{pad}# A Node loader flag in env names a hidden home script.\n"
    out += f"{pad}- patterns:\n"
    out += f"{pad}    - pattern-inside: |\n{pad}        env: $E\n{pad}        ...\n"
    out += (f"{pad}    - metavariable-pattern:\n{pad}        metavariable: $E\n"
            f"{pad}        patterns:\n{pad}          - pattern: $V\n")
    out += mvr("$V", YAML_SCALAR, n + 10, literal=True)
    out += mvr("$V", ENV_LOADER, n + 10, literal=True)
    return out


def yaml_cwd_checks(n):
    pad = " " * n
    out = f"{pad}# cwd is a hidden home folder and a relative program is the command.\n"
    out += f"{pad}- patterns:\n"
    out += f"{pad}    - pattern-inside: |\n{pad}        command: $R\n{pad}        ...\n"
    out += f"{pad}    - pattern: 'cwd: $V'\n"
    out += mvr("$R", YAML_SCALAR, n + 4, literal=True)
    out += mvr("$R", REL, n + 4, literal=True)
    out += mvr("$V", YAML_SCALAR, n + 4, literal=True)
    out += mvr("$V", CWD_DIR, n + 4, literal=True)
    out += f"{pad}# cwd is a hidden home folder and a relative script in args is run from it.\n"
    out += f"{pad}- patterns:\n"
    out += f"{pad}    - pattern-inside: |\n{pad}        args: $A\n{pad}        ...\n"
    out += (f"{pad}    - metavariable-pattern:\n{pad}        metavariable: $A\n"
            f"{pad}        patterns:\n{pad}          - pattern: $R\n")
    out += mvr("$R", YAML_SCALAR, n + 10, literal=True)
    out += mvr("$R", REL, n + 10, literal=True)
    out += f"{pad}    - pattern: 'cwd: $V'\n"
    out += mvr("$V", YAML_SCALAR, n + 4, literal=True)
    out += mvr("$V", CWD_DIR, n + 4, literal=True)
    return out


def yaml_rule():
    s = header("yaml", "yaml") + YAML_PATHS
    s += "    patterns:\n      - pattern-inside: 'mcpServers: [...]'\n      - pattern-either:\n"
    s += yaml_checks(10)
    s += "      - focus-metavariable: $V\n" + metadata("yaml")
    return s


def subagent_rule():
    s = header("subagent", "generic") + SUBAGENT_PATHS + subagent_patterns(yaml_checks(16, cwd=False))
    s += "      - focus-metavariable: $V\n" + metadata("subagent")
    return s


def toml_rule():
    s = header("toml", "regex") + TOML_PATHS + "    patterns:\n      - pattern-either:\n"
    # Branch 1: command, args and cwd, scoped to one server's keys ($SRV).
    s += "          # The command, a script in args, or a hidden-home cwd with a relative script.\n"
    s += "          - patterns:\n"
    s += ind(TOML_SERVERS, 8)
    s += """              # Drops candidate matches that bound no server; without it the metavariable-pattern
              # below reports "$SRV is not in scope" as an engine error.
              - metavariable-regex:
                  metavariable: $SRV
                  regex: (?s).
              # enabled = false: Codex skips the server (for dotted keys, only that server's key counts).
              - metavariable-regex:
                  metavariable: $SRV
                  regex: {TOML_ENABLED}
              - metavariable-pattern:
                  metavariable: $SRV
                  language: regex
                  patterns:
                    - pattern-either:
                        # The program the client starts.
                        - patterns:
""".replace("{TOML_ENABLED}", TOML_ENABLED)
    s += pregex(TOML_CMD, 28)
    s += mvr("$V", CMD, 28, literal=True)
    s += """                        # A script the program is given: each string in args, outside comments.
                        - patterns:
                            - pattern-regex: {TOML_EXTRACT}
                            - metavariable-pattern:
                                metavariable: $ARGS
                                language: regex
                                patterns:
""".replace("{TOML_EXTRACT}", TOML_EXTRACT)
    s += pregex(TOML_STRING, 34)
    s += mvr("$V", ARG, 34, literal=True)
    s += "                        # cwd is a hidden home folder and a relative script runs from it.\n"
    s += pregex(TOML_CWD, 24)
    # Branch 2: a Node loader flag in env, inline or in an [mcp_servers.<name>.env] sub-table.
    s += "          # A Node loader flag in env names a hidden home script.\n"
    s += "          - patterns:\n"
    s += ind(TOML_TABLES, 8)
    s += """              - metavariable-pattern:
                  metavariable: $TABLE
                  language: regex
                  patterns:
"""
    s += pregex(TOML_ENV, 22)
    s += "      - focus-metavariable: $V\n" + metadata("toml")
    return s


def workspace_rule():
    s = header("workspace", "regex") + WORKSPACE_PATHS + "    patterns:\n" + pregex(JSONC_MCP, 6)
    s += """      - metavariable-pattern:
          metavariable: $MCP
          language: regex
          patterns:
            # $SRV is one server object.
"""
    s += pregex(JSONC_SERVER, 12)
    s += """            - metavariable-pattern:
                metavariable: $SRV
                language: regex
                patterns:
                  - pattern-either:
                      # The program the client starts.
                      - patterns:
"""
    s += pregex(JSONC_CMD, 26)
    s += mvr("$V", CMD, 26, literal=True)
    s += """                      # A script the program is given: each string in args, outside comments.
                      - patterns:
"""
    s += pregex(JSONC_ARGS, 26)
    s += """                          - metavariable-pattern:
                              metavariable: $ARGS
                              language: regex
                              patterns:
"""
    s += pregex(JSONC_STRING, 32)
    s += mvr("$V", ARG, 32, literal=True)
    s += "                      # cwd is a hidden home folder and a relative script runs from it.\n"
    s += pregex(JSONC_CWD, 22)
    s += "                      # A Node loader flag in env names a hidden home script.\n"
    s += "                      - patterns:\n"
    s += pregex(JSONC_STRING, 26)
    s += mvr("$V", ENV_LOADER, 26, literal=True)
    s += "      - focus-metavariable: $V\n" + metadata("workspace")
    return s


def render() -> dict[Path, str]:
    """The rule files and the content this script generates for each."""
    return {
        RULE_DIR / f"{RULE_ID}.yaml": json_rule(),
        RULE_DIR / f"{RULE_ID}-yaml.yaml": yaml_rule(),
        RULE_DIR / f"{RULE_ID}-toml.yaml": toml_rule(),
        RULE_DIR / f"{RULE_ID}-workspace.yaml": workspace_rule(),
        RULE_DIR / f"{RULE_ID}-subagent.yaml": subagent_rule(),
    }


def main() -> int:
    for path, content in render().items():
        if not path.exists() or path.read_text() != content:
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
