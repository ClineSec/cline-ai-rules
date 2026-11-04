#!/usr/bin/env python3
"""Generate the mcp-filesystem-root-too-broad and mcp-container-host-root-mount rule files from
one set of root, runner and docker mount regexes.

mcp-container-host-root-mount flags any other MCP server container (and, in compose files, any
MCP service, the filesystem server's included) with one of the folders below bind-mounted into
it; see the section of that name near the end.

The rules flag an MCP filesystem server whose allowed directory is the whole disk (/, C:\\, a
WSL drive such as /mnt/c), every user's home (/Users, /home), or one user's whole home (~,
${HOME}, %USERPROFILE%, /Users/<name>, /home/<name>, C:\\Users\\<name>, /root), or a filesystem
server container with one of those folders bind-mounted into it.

Servers (verified 2026-10-23):
- @modelcontextprotocol/server-filesystem 2.0.0 (npm, bin mcp-server-filesystem; the
  mcp/filesystem Docker image): every command-line argument is an allowed directory, and the
  server expands ~ and ~/ itself (src/filesystem/index.ts, path-utils.ts at tag v2.0.0). A bare
  drive letter (C:) is normalized to the drive root on Windows. A client on the 2025-era protocol
  that supports MCP Roots replaces these directories with its own roots; on protocol 2026-07-28
  the command line is the whole allow-list.
- mark3labs/mcp-filesystem-server v0.11.1 (bin mcp-filesystem-server, image
  ghcr.io/mark3labs/mcp-filesystem-server): every argument is an allowed directory (main.go).
- rust-mcp-filesystem (rust-mcp-stack, commit ef47973): positional ALLOWED_DIRECTORIES after
  its options (src/cli.rs). Not on npm, so only its binary name is matched.

Home-directory and user-name variables count only where the client that reads the file expands
them (HOME_VARS, USER_VARS, checked 2026-10-25), so the JSON twins are split by client
(JSON_GROUPS): Claude Code and the Copilot CLI take ${HOME} and ${HOME:-default}; VS Code and
Cursor ${env:HOME} and ${userHome}; Cline, Windsurf and Roo Code ${env:HOME}; Gemini CLI $HOME,
${HOME} and ${HOME:-default}; Claude Desktop, Zed, Continue and Kiro none. The workspace rule
takes VS Code's; Codex, Continue YAML and subagent servers none. %USERPROFILE% (cmd /c) counts
everywhere, and a shell line adds its own ($HOME, ${HOME}, $env:USERPROFILE).

A folder inside the home directory (~/projects/app, /Users/<name>/Desktop), the workspace
(${workspaceFolder}, .), and shared folders (/Users/Shared, C:\\Users\\Public) are left alone.

The format scaffolding (file paths, server scopes, the TOML and JSONC extractors, the runner and
family builders, and the subagent front matter scaffolding) comes from gen_mcp_unpinned.py, so
every MCP config family scans the same files and servers. The subagent rule runs the Continue
YAML checks on a subagent's front matter mcpServers block.

Edit this script, not the rule files. scripts/build.py regenerates them, and
scripts/build.py --check fails when a rule file differs from what this script produces.

Usage:
    python3 scripts/gen_mcp_filesystem_root.py    # rewrite the rule files
"""

from __future__ import annotations

import sys
from pathlib import Path

from gen_mcp_unpinned import (DOCKER_OPTS, G, JSON_PATHS, JSON_SCOPE, JSONC_MCP, JSONC_SERVER, JSONC_STRING,
                              SHELL_CMD, START, SUBAGENT_NOTE, SUBAGENT_PATHS, SUBAGENT_REFS,
                              TOML_ENABLED, TOML_PATHS, TOML_SERVERS, WORKSPACE_PATHS, YAML_PATHS,
                              cmd, family, ind, mvr, pregex, runner, subagent_patterns)

ROOT = Path(__file__).resolve().parent.parent
RULE_DIR = ROOT / "rules" / "agent-config" / "permissions"
RULE_ID = "mcp-filesystem-root-too-broad"

# ---- root regexes --------------------------------------------------------------------------


# The home-directory variables each client expands in a server's args (checked 2026-10-25). The
# server itself expands only ~, so a variable the client leaves alone reaches it as a literal
# folder name that doesn't exist. %USERPROFILE% is expanded by cmd /c, the usual way npx runs on
# Windows, and counts everywhere.
HOME_VARS = {
    # Claude Code (.mcp.json and its other files: ${VAR} and ${VAR:-default}, docs "Environment
    # variable expansion"); VS Code expands ${VAR} in a workspace-root .mcp.json and in the
    # Copilot CLI's mcp-config.json (1.143.1, workspaceDotMcpDiscovery.ts and
    # nativeMcpDiscoveryAdapters.ts).
    "claude": r"""\$\{ (?:HOME|USERPROFILE) (?: :- [^}]*+ )?+ \} |""",
    # VS Code configuration variables (mcp.json, dev containers, .code-workspace) and Cursor
    # (mcp.json): ${env:...} and ${userHome}.
    "vscode": r"""\$\{env: (?:HOME|USERPROFILE) \} | \$\{userHome\} |""",
    # Cline (envExpansion.ts), Windsurf / Devin Desktop (mcp_config.json docs) and Roo Code
    # (injectVariables in utils/config.ts): ${env:...} only.
    "cline": r"""\$\{env: (?:HOME|USERPROFILE) \} |""",
    # Gemini CLI v0.65.0 (envVarResolver.ts, applied to settings.json and gemini-extension.json,
    # array elements included): $VAR, ${VAR} and ${VAR:-default}.
    "gemini": r"""\$ (?:HOME|USERPROFILE) \b | \$\{ (?:HOME|USERPROFILE) (?: :- [^}]*+ )?+ \} |""",
    # Claude Desktop, Zed (v1.25.3 stdio_transport.rs passes literal args), Continue, Kiro (its
    # ${VAR} is documented for env only, after approval), Codex, and subagent servers pass args
    # as written.
    "none": "",
    # Compose interpolates $HOME and ${HOME}, with or without a default (${HOME:-/root}).
    "compose": r"""\$HOME\b | \$\{ (?:HOME|USERPROFILE) (?: :?[-?] [^}]*+ )?+ \} |""",
    # A shell line (bash -c, pwsh -Command) expands its own variables, on top of the client's.
    "shell": r"""\$HOME\b | \$\{ (?:HOME|USERPROFILE) \} | \$env: (?:HOME|USERPROFILE) \b
    | \$\{env: (?:HOME|USERPROFILE) \} |""",
}

# The same for a user name in /home/<name> or C:\Users\<name>: an unexpanded $USER is a literal
# folder name, so a $ name counts only in the forms the client expands.
USER_VARS = {
    "claude": r"""\$\{ (?:USER|USERNAME) (?: :- [^}]*+ )?+ \}""",
    "vscode": r"""\$\{env: (?:USER|USERNAME) \}""",
    "cline": r"""\$\{env: (?:USER|USERNAME) \}""",
    "gemini": r"""\$ (?:USER|USERNAME) \b | \$\{ (?:USER|USERNAME) (?: :- [^}]*+ )?+ \}""",
    "none": r"""(?!)""",
    "compose": r"""\$ (?:USER|USERNAME) \b | \$\{ (?:USER|USERNAME) (?: :?[-?] [^}]*+ )?+ \}""",
    "shell": r"""\$ (?:USER|USERNAME) \b | \$\{ (?:USER|USERNAME) \} | \$env: (?:USER|USERNAME) \b
    | \$\{env: (?:USER|USERNAME) \}""",
}


def fs_define(shell: bool, home_vars: str) -> str:
    """Named groups shared by every branch. In a shell line a user name ends at whitespace; in
    a config element it may hold inner spaces (C:\\Users\\John Smith). home_vars names the
    client's HOME_VARS entry; a shell line adds the shell's own."""
    if shell:
        uname = r"""[^/\\"'\s,\[\]:\#;&|`$]++"""
        homevars = HOME_VARS["shell"] + HOME_VARS[home_vars]
        uservars = USER_VARS["shell"] + " | " + USER_VARS[home_vars]
    else:
        uname = r"""[^/\\"'\s,\[\]:\#$]++ (?: [ \t]++ [^/\\"'\s,\[\]:\#]++ )*+"""
        homevars = HOME_VARS[home_vars]
        uservars = USER_VARS[home_vars]
    uname = f"(?: {uservars} | {uname} )"
    return r"""
  # A path separator: / or \, which JSON, TOML basic strings and YAML double-quoted strings
  # write doubled. A single backslash before " escapes the quote (src=\"$PWD\" in a shell line).
  (?<ps> / | \\\\ | \\(?!") )
  # One user's folder name. Shared folders (/Users/Shared, C:\Users\Public) aren't a home.
  (?<uname> (?! (?i: Shared | Public | Default | Default\x20User | All\x20Users ) (?! [\w.-] ) )
    UNAME )
  # The user's whole home directory, however the config spells it.
  (?<home> ~ | HOMEVARS (?i: %USERPROFILE% | %HOMEDRIVE%%HOMEPATH% )
    | (?: /mnt/[A-Za-z] | [A-Za-z]: )?+ (?&ps) (?i: users | home ) (?&ps) (?&uname)
    | /root | /var/root )
  # An allowed directory that is a home, every user's home (/Users, /home), a drive (C:, C:\,
  # WSL's /mnt/c), or the root (/), with or without a trailing separator.
  (?<root> (?: (?&home) | (?: /mnt/[A-Za-z] | [A-Za-z]: )?+ (?&ps) (?i: users | home )
      | /mnt/[A-Za-z] | [A-Za-z]: ) (?&ps)?+
    | (?&ps)++ )
  # The filesystem server named in a runner's arguments: the npm package (or its npm: spec for
  # deno), a bin name (also an older npm copy published as mcp-server-filesystem; a scoped name
  # such as @other/mcp-server-filesystem is another package), the Go module, or a local
  # build's dist/index.js.
  (?<fspkg> (?:npm:)?+ @modelcontextprotocol/server-filesystem (?: @[^"'\s,\]]*+ )?+
    | github\.com/mark3labs/mcp-filesystem-server (?: @[^"'\s,\]]*+ )?+
    | (?: (?!@) [^"'\r\n,\]]* (?&ps) )? (?: mcp-server-filesystem | mcp-filesystem-server | rust-mcp-filesystem )
      (?: @[^"'\s,\]]*+ | \.cmd | \.exe )?+
    | [^"'\r\n,\]]*? (?&ps) (?: @modelcontextprotocol (?&ps) server-filesystem
      | servers (?&ps) src (?&ps) filesystem ) (?&ps) dist (?&ps) index\.js )
  # The filesystem server's container image, with an optional tag or digest.
  (?<image> (?: (?: (?:docker\.io|index\.docker\.io)/ )?+ mcp/filesystem
    | ghcr\.io/mark3labs/mcp-filesystem-server ) (?: :[\w.-]++ )?+ (?: @sha256:[0-9a-fA-F]++ )?+ )""".replace(
        "UNAME", uname).replace("HOMEVARS", homevars)


# A whole element that is a broad root. A plain YAML ~ is null, not a string, so a bare tilde
# needs quotes.
ROOT_EL = r"""(?&o) (?! (?<!["'])~(?&c) ) (?<ROOT>(?&root)) (?&c)"""

def pkg_re(v):
    return rf"""(?sx)
(?(DEFINE)
{G}
{fs_define(False, v)}
)
{START}
# The runner's own options (-y, cmd's /c npx, deno's run -A) come before the package; every
# element after it is an allowed directory.
(?: (?&el) (?&nx) )*?
(?=(?&o)(?&fspkg)(?&c)) (?&el) (?&nx)
(?: (?&el) (?&nx) )*?
{ROOT_EL}"""

# The server's own binary is the command: every argument is a directory (rust-mcp-filesystem's
# options are flags or tool names, never a root).
def bin_re(v):
    return rf"""(?sx)
(?(DEFINE)
{G}
{fs_define(False, v)}
)
{START}
(?: (?&el) (?&nx) )*?
{ROOT_EL}"""

# A host folder bind-mounted with docker run: -v / --volume <host>:<container>, or --mount
# type=bind,src=<host>,dst=<container>. docker doesn't expand ~ (only a shell does), so a ~
# source is left alone. (?| ... ) lets both alternatives capture ROOT. mcp-container-host-root-mount
# shares it.
DOCKER_MOUNT = r"""(?| (?: (?=(?&o)(?:-v|--volume)(?&c)) (?&el) (?&nx) (?&o) | (?&o)--volume= )
    (?!~) (?<ROOT>(?&root)) (?=:)
  | (?: (?=(?&o)--mount(?&c)) (?&el) (?&nx) (?&o) | (?&o)--mount= )
    (?: [^"'\s\]\#]*? , )?? (?i:src|source)= (?!~) (?<ROOT>(?&root)) (?= [,"'\s\]] | \z ) )"""

# A later element that is the filesystem server's image.
FS_IMAGE_LATER = r"""(?s:.*?) (?&nx) (?&o) (?&image) (?&c)"""

# docker run before the filesystem image, with a host folder bind-mounted. Arguments after the
# image are paths inside the container, so a / there is the container's own root.
def docker_re(v):
    return rf"""(?sx)
(?(DEFINE)
{G}
{fs_define(False, v)}
)
{START}
(?: (?&el) (?&nx) )*?
{DOCKER_MOUNT}
(?= {FS_IMAGE_LATER} )"""

# The same shapes inside one shell line: "bash", ["-c", "npx -y pkg@1.2.3 ~"].
_SHELL_DEFINE = r"""(?x)
(?(DEFINE)
{FS}
  # One shell word, with any quoted parts (JSON text escapes a quote as \").
  (?<w> (?: \\?+["'] [^"'\r\n\\]*+ \\?+["'] | [^\s;&|`()<>"'\\] )++ )
  (?<we> (?= [\s;&|)`] | \\?+["'] | $ ) )
  (?<docker> (?<! [\w.-] ) (?:docker|podman) (?:\.exe)?+ [ \t]++ (?:container [ \t]++)?+ run (?&we)
    (?: [ \t]++ (?&w) )*? [ \t]++ )
  # The rest of a mount word, then the filesystem image as a later word.
  (?<imagelater> [^\s;&|]*+ (?: [ \t]++ (?&w) )*? [ \t]++ (?:\\?+["'])?+ (?&image) (?&we) )
)
.*?
"""


def shell_define(v):
    """The shell groups, with the shell's own home variables plus the client's (v)."""
    return _SHELL_DEFINE.replace("{FS}", fs_define(True, v))


SHELL_MOUNT_V = r"""(?&docker) (?:-v|--volume) (?: [ \t]++ | = ) (?:\\?+["'])?+ (?<ROOT>(?&root)) (?=:)"""
SHELL_MOUNT_M = r"""(?&docker) --mount (?: [ \t]++ | = ) (?:\\?+["'])?+ (?: [^\s"',;&|\\]*? , )??
    (?i:src|source)= (?<ROOT>(?&root)) (?= [,\s;&|"'\\] | $ )"""
def shell_re(v):
    return shell_define(v) + r"""(?| (?<! [^\s"'=] ) (?&fspkg) (?&we) (?: [ \t]++ (?&w) )*?
    [ \t]++ (?:\\?+["'])?+ (?<ROOT>(?&root)) (?:\\?+["'])?+ (?= [\s;&|)`] | $ )
  | """ + SHELL_MOUNT_V + r""" (?=(?&imagelater))
  | """ + SHELL_MOUNT_M + r""" (?=(?&imagelater)) )"""

PKG_CMD = cmd("npx|bunx|pnpx|npm|pnpm|yarn|bun|node|nodejs|deno|cmd|go")
BIN_CMD = cmd("mcp-server-filesystem|mcp-filesystem-server|rust-mcp-filesystem")
DOCKER_CMD = cmd("docker|podman", r"(?:\.exe)?")

# ---- format scaffolding --------------------------------------------------------------------

def string_branch(fmt, shell_re, n):
    """Within the args of a server whose command is a shell, a string holding the line."""
    pad = " " * n
    if fmt == "json":
        out = f"{pad}- patterns:\n"
        out += f"{pad}    - pattern-inside: '{{..., \"command\": \"$CMD\", ...}}'\n"
        out += mvr("$CMD", SHELL_CMD, n + 4, literal=True)
        out += f"{pad}    - pattern-inside: '\"args\": [...]'\n"
        out += f"{pad}    - pattern: '\"$S\"'\n"
        out += mvr("$S", shell_re, n + 4, literal=True)
        return out
    if fmt == "yaml":
        out = f"{pad}- patterns:\n"
        out += f"{pad}    - pattern-inside: |\n{pad}        command: $CMD\n{pad}        ...\n"
        out += mvr("$CMD", SHELL_CMD, n + 4, literal=True)
        out += f"{pad}    - pattern-inside: 'args: [...]'\n"
        out += f"{pad}    - pattern: '\"$S\"'\n"
        out += mvr("$S", shell_re, n + 4, literal=True)
        return out
    # toml / jsonc: the runner extracts $CMD and $ARGS from one server.
    out = runner(fmt, SHELL_CMD, None, n)
    strings = (JSONC_STRING.replace("<V>", "<S>"),) if fmt == "jsonc" else (
        r'''"(?<S>(?:[^"\\\n]|\\.)*)"''', r"""'(?<S>[^'\n]*)'""")
    out += f"{pad}    - metavariable-pattern:\n"
    out += f"{pad}        metavariable: $ARGS\n"
    out += f"{pad}        language: regex\n"
    out += f"{pad}        patterns:\n"
    if len(strings) == 1:
        out += pregex(strings[0], n + 10)
    else:
        out += f"{pad}          - pattern-either:\n"
        for s in strings:
            out += pregex(s, n + 14)
    # $S is only visible to conditions inside the metavariable-pattern that binds it.
    out += mvr("$S", shell_re, n + 10, literal=True)
    return out


# The home variables each format's client expands (see HOME_VARS). JSON files are split by
# client (JSON_GROUPS). A subagent's servers are checked with the Continue YAML branches, so
# they share "none".
FORMAT_VARS = {"jsonc": "vscode", "yaml": "none", "toml": "none"}


def families(fmt, n, v=None):
    pad = " " * n
    v = v or FORMAT_VARS[fmt]
    out = family(fmt, [
        "A package runner (npx, bunx, pnpx, npm exec, pnpm/yarn dlx, bun x, deno, go run, cmd /c",
        "npx) or node on a local build: every element after the server is an allowed directory.",
    ], [(PKG_CMD, None)], pkg_re(v), n)
    out += family(fmt, [
        "The server's own binary, installed globally: every argument is an allowed directory.",
    ], [(BIN_CMD, None)], bin_re(v), n)
    out += family(fmt, [
        "The server's container with a host folder bind-mounted: docker run -v <host>:<path>,",
        "or --mount type=bind,src=<host>,dst=<path>.",
    ], [(DOCKER_CMD, None)], docker_re(v), n)
    out += f"{pad}# A shell given the whole command line: \"bash\", [\"-c\", \"npx -y pkg@1.2.3 ~\"]. The\n"
    out += f"{pad}# shell expands $HOME itself.\n"
    out += string_branch(fmt, shell_re(v), n)
    return out


# ---- rule text -----------------------------------------------------------------------------

MESSAGE = """    message: >-
      This MCP filesystem server may read and write the whole disk or a whole home directory:
      an allowed directory of /, a drive such as C:\\, /Users or /home, or one user's home (~,
      the HOME or USERPROFILE variable, /Users/<name>, /home/<name>), or that folder
      bind-mounted into the server's container. Its tools (read_text_file, write_file,
      edit_file, move_file, search_files) then reach SSH keys, cloud and package-registry
      credentials, shell profiles, other repositories, and the agent's own config, and a prompt
      injection in any file, issue, or web page the agent reads can make it read those files
      into the conversation or plant a command in a shell profile. Pass only the folders the
      agent needs (the project folder, a scratch folder), and mount only those into the
      container, read-only where the agent only reads.
"""

SYNC_NOTE = """# Generated by scripts/gen_mcp_filesystem_root.py, which holds the root and runner regexes
# shared by the mcp-filesystem-root-too-broad rules for JSON, Continue YAML, Codex TOML, VS Code
# workspace files and Claude Code subagents, and takes the file paths from
# scripts/gen_mcp_unpinned.py. Edit the script and run scripts/build.py; build.py --check fails
# if this file drifts.
"""

TECHNOLOGY = {
    "json": "[mcp, claude-code, vscode, copilot-cli]",
    "json-vscode": "[mcp, vscode, cursor]",
    "json-cline": "[mcp, cline, windsurf, roo-code]",
    "json-gemini": "[mcp, gemini-cli]",
    "json-literal": "[mcp, claude-desktop, zed, continue, kiro]",
    "yaml": "[mcp, continue]",
    "toml": "[mcp, codex]",
    "workspace": "[mcp, vscode]",
    "subagent": "[mcp, claude-code]",
}

COMMON_REFS = """        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP02-2025%E2%80%93Privilege-Escalation-via-Scope-Creep.md
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md
        - https://github.com/modelcontextprotocol/servers/blob/v2.0.0/src/filesystem/README.md
        - https://github.com/modelcontextprotocol/servers/blob/v2.0.0/src/filesystem/index.ts
        - https://github.com/modelcontextprotocol/servers/blob/v2.0.0/src/filesystem/path-utils.ts
        - https://hub.docker.com/r/mcp/filesystem
        - https://github.com/mark3labs/mcp-filesystem-server/blob/v0.11.1/main.go
        - https://github.com/rust-mcp-stack/rust-mcp-filesystem/blob/ef4797360ea03eec5375e03a6f10d092dfc6a5e0/src/cli.rs
"""

FORMAT_REFS = {
    "json": """        - https://code.claude.com/docs/en/mcp
        - https://github.com/microsoft/vscode/blob/1.143.1/src/vs/workbench/contrib/mcp/common/discovery/workspaceDotMcpDiscovery.ts
        - https://github.com/microsoft/vscode/blob/1.143.1/src/vs/workbench/contrib/mcp/common/discovery/nativeMcpDiscoveryAdapters.ts
""",
    "json-vscode": """        - https://code.visualstudio.com/docs/reference/variables-reference
        - https://code.visualstudio.com/docs/copilot/reference/mcp-configuration
        - https://cursor.com/docs/context/mcp
""",
    "json-cline": """        - https://github.com/cline/cline/blob/ac996847bd81bc3de4b12939d5a55a718a0d2c55/apps/vscode/src/utils/envExpansion.ts
        - https://docs.devin.ai/desktop/cascade/mcp
        - https://github.com/RooCodeInc/Roo-Code/blob/b867ec9145750d0ae1ff7f02d35406e9bf2a0b16/src/utils/config.ts
""",
    "json-gemini": """        - https://github.com/google-gemini/gemini-cli/blob/v0.65.0/docs/reference/configuration.md
        - https://github.com/google-gemini/gemini-cli/blob/v0.65.0/packages/cli/src/utils/envVarResolver.ts
""",
    "json-literal": """        - https://github.com/zed-industries/zed/blob/v1.25.3/crates/context_server/src/transport/stdio_transport.rs
        - https://kiro.dev/docs/mcp/configuration/
        - https://docs.continue.dev/customize/deep-dives/mcp
""",
    "yaml": """        - https://docs.continue.dev/customize/deep-dives/mcp
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

SUFFIX = {"json": "", "json-vscode": "-vscode", "json-cline": "-cline", "json-gemini": "-gemini",
          "json-literal": "-literal", "yaml": "-yaml", "toml": "-toml", "workspace": "-workspace",
          "subagent": "-subagent"}


def metadata(fmt):
    return f"""    metadata:
      category: security
      subcategory: [audit]
      pack-category: agent-config
      owasp-llm:
        - "LLM03:2026 - Excessive Agency"
        - "LLM06:2025 - Excessive Agency"
      owasp-agentic:
        - "ASI02 - Tool Misuse and Exploitation"
      owasp-mcp:
        - "MCP02:2025 - Privilege Escalation via Scope Creep"
      owasp-aisvs:
        - "v1.01-C9.3.1 - Component Isolation and Tool Authorization"
      mitre-atlas:
        - "AML.T0053 - AI Agent Tool Invocation"
        - "AML.T0037 - Data from Local System"
      cwe:
        - "CWE-250: Execution with Unnecessary Privileges"
      # A match always grants the whole disk or a whole home. A client on the 2025-era protocol
      # that supports MCP Roots replaces server-filesystem's directories with its own roots
      # (server-filesystem 2.0.0 README), so on those clients the grant may not take effect.
      confidence: MEDIUM
      likelihood: MEDIUM
      impact: HIGH
      technology: {TECHNOLOGY[fmt]}
      references:
""" + COMMON_REFS + FORMAT_REFS[fmt]


def header(fmt, lang, k):
    s = f"rules:\n  - id: {k['id']}{SUFFIX[fmt]}\n"
    if fmt == "toml":
        s += "    # Regex, not a parser: OpenGrep has no TOML support.\n"
    elif fmt == "workspace":
        s += ("    # Regex, not JSON: OpenGrep's JSON parser skips *.code-workspace files (unknown\n"
              "    # extension), even when paths.include names them.\n")
    elif fmt == "subagent":
        s += SUBAGENT_NOTE
    s += ind(k["sync"], 4)
    s += f"    languages: [{lang}]\n    severity: WARNING\n" + k["message"]
    return s


# The JSON MCP config files (gen_mcp_unpinned.JSON_PATHS), split by the clients that read each
# one, because they expand different variables in a server's args (HOME_VARS). Each entry: the
# format key, the HOME_VARS entry, a note, the includes, and the excludes. A file another
# client also reads (.mcp.json: Claude Code and VS Code) takes the forms both expand. Bare
# names match at any depth, so a name that more than one group would match (mcp.json in .roo/,
# .kiro/settings/ and .continue/mcpServers/) is excluded where it doesn't belong.
CONTINUE_JSON = ".continue/mcpServers/**"
JSON_GROUPS = [
    ("json", "claude", "Claude Code (${VAR}, ${VAR:-default}), VS Code's workspace-root .mcp.json, and\n"
     "the Copilot CLI's mcp-config.json (VS Code 1.143.1 expands ${VAR} there like the Copilot\n"
     "runtime).",
     [".mcp.json", ".claude.json", "managed-mcp.json", ".claude-plugin/plugin.json",
      ".claude-plugin/marketplace.json", "mcp-config.json"], [CONTINUE_JSON]),
    ("json-vscode", "vscode", "VS Code (.vscode/mcp.json, the user mcp.json, dev containers) and Cursor\n"
     "(.cursor/mcp.json): ${env:VAR} and ${userHome}.",
     ["mcp.json", ".devcontainer/devcontainer.json", ".devcontainer.json",
      ".devcontainer/*/devcontainer.json"],
     [CONTINUE_JSON, ".roo/mcp.json", ".kiro/settings/mcp.json"]),
    ("json-cline", "cline", "Cline, Windsurf / Devin Desktop and Roo Code: ${env:VAR} only.",
     ["cline_mcp_settings.json", "mcp_config.json", ".roo/mcp.json"], [CONTINUE_JSON]),
    ("json-gemini", "gemini", "Gemini CLI settings and extension manifests: $VAR, ${VAR},\n"
     "${VAR:-default}.",
     [".gemini/settings.json", "gemini-extension.json"], [CONTINUE_JSON]),
    ("json-literal", "none", "Clients that pass args as written: Claude Desktop, Zed, Continue's\n"
     ".continue/mcpServers/ JSON files, and Kiro.",
     ["claude_desktop_config.json", ".zed/settings.json", ".config/zed/settings.json",
      ".continue/mcpServers/**/*.json", ".kiro/settings/mcp.json"],
     [".continue/mcpServers/**/config.json", ".continue/mcpServers/**/settings.json"]),
]


def _check_json_groups():
    """The groups must cover exactly the files the other MCP JSON families scan."""
    import yaml
    shared = yaml.safe_load("x:\n" + JSON_PATHS)["x"]["paths"]
    ours = {p for g in JSON_GROUPS for p in g[3]} | {".roo/mcp.json", ".kiro/settings/mcp.json"}
    missing = set(shared["include"]) - ours
    if missing:
        raise SystemExit(f"JSON_GROUPS misses {sorted(missing)} from gen_mcp_unpinned.JSON_PATHS")


_check_json_groups()


def json_paths(group):
    _, _, note, inc, exc = group
    s = "    paths:\n"
    s += "".join(f"      # {line}\n" for line in note.split("\n"))
    s += "      include:\n" + "".join(f'        - "{p}"\n' for p in inc)
    s += "      exclude:\n" + "".join(f'        - "{p}"\n' for p in exc)
    return s


def json_rule(k, group):
    fmt, v = group[0], group[1]
    s = header(fmt, "json", k) + json_paths(group) + "    patterns:\n" + JSON_SCOPE
    s += "      - pattern-either:\n" + k["families"]("json", 10, v)
    s += "      - focus-metavariable: $ROOT\n" + k["metadata"](fmt)
    return s


def yaml_rule(k):
    s = header("yaml", "yaml", k) + YAML_PATHS
    s += "    patterns:\n      - pattern-inside: 'mcpServers: [...]'\n      - pattern-either:\n"
    s += k["families"]("yaml", 10)
    s += "      - focus-metavariable: $ROOT\n" + k["metadata"]("yaml")
    return s


def toml_rule(k):
    s = header("toml", "regex", k) + TOML_PATHS + "    patterns:\n" + TOML_SERVERS
    s += """      # Drops candidate matches that bound no server; without it the metavariable-pattern
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
""".replace("{TOML_ENABLED}", TOML_ENABLED)
    s += k["families"]("toml", 16)
    s += "      - focus-metavariable: $ROOT\n" + k["metadata"]("toml")
    return s


def workspace_rule(k):
    s = header("workspace", "regex", k) + WORKSPACE_PATHS + "    patterns:\n" + pregex(JSONC_MCP, 6)
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
"""
    s += k["families"]("jsonc", 22)
    s += "      - focus-metavariable: $ROOT\n" + k["metadata"]("workspace")
    return s


def subagent_rule(k):
    s = header("subagent", "generic", k) + SUBAGENT_PATHS + subagent_patterns(k["families"]("yaml", 16))
    s += "      - focus-metavariable: $ROOT\n" + k["metadata"]("subagent")
    return s


# ---- mcp-container-host-root-mount ---------------------------------------------------------
#
# Any MCP server container, not only the filesystem server, with the host's root, a drive,
# every user's home, or one user's home bind-mounted into it. The mount shapes and the root
# regexes are the ones above, so both rules read a mount the same way. A filesystem server
# image is left to mcp-filesystem-root-too-broad, which reports the same mounts with a message
# about its file tools: this rule requires that no later element is that image, the exact
# complement of the filesystem rule's docker branch, so one mount gives one finding.
#
# Docker (docs.docker.com, bind mounts and docker container run reference, read 2026-10-25):
# -v <host>:<container>[:opts] with ro / readonly / z / Z / propagation options, and --mount
# type=bind,source|src=<host>,target|dst|destination=<container>[,readonly|ro]. A read-only
# mount is still reported: the container (root by default) reads every secret on the host,
# and most public MCP configs that mount / use :ro. Compose (compose-go v2.16.2,
# paths/unix.go) expands a leading ~ in a volume's host path, and interpolates ${HOME}.

HOST_ID = "mcp-container-host-root-mount"

# docker run (or docker container run) and its options, then a host folder mounted among the
# options before the image. A -v after the image is the container command's own argument.
def host_docker_re(v):
    return rf"""(?sx)
(?(DEFINE)
{G}
{fs_define(False, v)}
{DOCKER_OPTS}
)
{START}
(?: (?=(?&o)container(?&c)) (?&el) (?&nx) )?
(?=(?&o)run(?&c)) (?&el) (?&nx)
(?: (?&opt) (?&nx) )*?
{DOCKER_MOUNT}
# A filesystem server image: mcp-filesystem-root-too-broad reports it.
(?! {FS_IMAGE_LATER} )"""


def host_shell_re(v):
    return shell_define(v) + r"""(?| """ + SHELL_MOUNT_V + r""" (?!(?&imagelater))
  | """ + SHELL_MOUNT_M + r""" (?!(?&imagelater)) )"""


def host_families(fmt, n, v=None):
    pad = " " * n
    v = v or FORMAT_VARS[fmt]
    out = family(fmt, [
        "docker run (or podman) with a host folder bind-mounted among the options before the",
        "image: -v <host>:<path>, --volume, or --mount type=bind,src=<host>,dst=<path>.",
    ], [(DOCKER_CMD, None)], host_docker_re(v), n)
    out += f"{pad}# A shell given the whole command line: \"bash\", [\"-c\", \"docker run -v $HOME:/h ...\"].\n"
    out += f"{pad}# The shell expands $HOME itself.\n"
    out += string_branch(fmt, host_shell_re(v), n)
    return out


HOST_MESSAGE = """    message: >-
      This MCP server runs in a container with the host's whole disk or a whole home directory
      bind-mounted into it (/, a drive such as C:\\, /Users or /home, or one user's home: the
      HOME or USERPROFILE variable, /Users/<name>, /home/<name>). Every tool the server has
      that reads files, follows a path, or runs a command then reaches the host's SSH keys,
      cloud and registry credentials, shell profiles and other projects, and, since a
      container runs as root unless told otherwise, files only root can read. A prompt
      injection in anything the agent reads can steer those tools there. Read-only still
      exposes every secret; a writable mount also lets the container plant a command in a
      shell profile or cron file and so escape to the host. Mount only the folders the server
      needs (the project folder, a data folder), read-only where it only reads.
"""

HOST_SYNC_NOTE = """# Generated by scripts/gen_mcp_filesystem_root.py, which holds the root and docker mount
# regexes shared by the mcp-filesystem-root-too-broad and mcp-container-host-root-mount rules,
# and takes the file paths from scripts/gen_mcp_unpinned.py. Edit the script and run
# scripts/build.py; build.py --check fails if this file drifts.
"""

HOST_COMMON_REFS = """        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP02-2025%E2%80%93Privilege-Escalation-via-Scope-Creep.md
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md
        - https://docs.docker.com/engine/storage/bind-mounts/
        - https://docs.docker.com/reference/cli/docker/container/run/
"""

HOST_TECHNOLOGY = {k: v.replace("[mcp,", "[mcp, docker,") for k, v in TECHNOLOGY.items()}


def host_metadata(fmt, pack="agent-config"):
    refs = HOST_COMMON_REFS + (FORMAT_REFS[fmt] if fmt in FORMAT_REFS else COMPOSE_REFS)
    tech = HOST_TECHNOLOGY.get(fmt, "[mcp, docker-compose]")
    return f"""    metadata:
      category: security
      subcategory: [audit]
      pack-category: {pack}
      owasp-llm:
        - "LLM03:2026 - Excessive Agency"
        - "LLM06:2025 - Excessive Agency"
      owasp-agentic:
        - "ASI02 - Tool Misuse and Exploitation"
      owasp-mcp:
        - "MCP02:2025 - Privilege Escalation via Scope Creep"
      owasp-aisvs:
        - "v1.01-C9.3.1 - Component Isolation and Tool Authorization"
      mitre-atlas:
        - "AML.T0053 - AI Agent Tool Invocation"
        - "AML.T0037 - Data from Local System"
      cwe:
        - "CWE-250: Execution with Unnecessary Privileges"
      # A match always gives the container the whole disk or a whole home; whether the agent
      # can reach it depends on the server's tools, which config doesn't show.
      confidence: MEDIUM
      likelihood: MEDIUM
      impact: HIGH
      technology: {tech}
      references:
""" + refs


KINDS = {
    "fs": {"id": RULE_ID, "message": MESSAGE, "sync": SYNC_NOTE, "families": families,
           "metadata": metadata},
    "host": {"id": HOST_ID, "message": HOST_MESSAGE, "sync": HOST_SYNC_NOTE,
             "families": host_families, "metadata": host_metadata},
}


# ---- the compose twin ----------------------------------------------------------------------

# The files mcp-server-bind-all-interfaces-config-compose and vector-db-published-without-auth-
# compose scan (SHARED_PATHS "docker compose files" in build.py keeps them equal).
COMPOSE_PATHS = """    paths:
      include:
        - "docker-compose.yml"
        - "docker-compose.yaml"
        - "docker-compose.*.yml"
        - "docker-compose.*.yaml"
        - "docker-compose-*.yml"
        - "docker-compose-*.yaml"
        - "compose.yml"
        - "compose.yaml"
        - "compose.*.yml"
        - "compose.*.yaml"
"""

COMPOSE_REFS = """        - https://docs.docker.com/reference/compose-file/services/
        - https://docs.docker.com/reference/compose-file/interpolation/
        - https://github.com/compose-spec/compose-go/blob/v2.16.2/paths/unix.go
        - https://github.com/compose-spec/compose-go/blob/v2.16.2/paths/home.go
"""

# "mcp" at the start or end of a name part (devops-mcp, mcp-clipboard, mcp/filesystem,
# mcpjungle, fastmcp), not inside one; mcpe (Minecraft Pocket Edition servers) is left out.
MCP_NAME = r"""(?i)^.*?(?:(?<![a-z0-9])mcp(?!e(?![a-z0-9]))|mcp(?![a-z0-9]))"""
# A command that starts an MCP server: an mcp name, an MCP SDK package, or a stdio bridge.
MCP_COMMAND = r"""(?is)^.*?(?:(?<![a-z0-9])mcp(?!e(?![a-z0-9]))|mcp(?![a-z0-9])|modelcontextprotocol|supergateway)"""
# Host agents that mount / to read disk or process stats, often named after the MCP project
# they sit next to (container_name: mcp-standards-node-exporter).
MONITOR_IMAGE = (r"""(?i)^["']?+(?:[^\s"'/]*+/)*?(?:node-exporter|node_exporter|cadvisor|netdata"""
                 r"""|promtail|alloy|telegraf|fluent-bit|fluentbit|vector|otelcol(?:-contrib)?"""
                 r"""|opentelemetry-collector(?:-contrib|-k8s)?|metricbeat|filebeat|auditbeat"""
                 r"""|falco|beszel-agent|scrutiny|smartctl-exporter|(?<=datadoghq/|datadog/)agent)"""
                 r"""(?:[:@]|["']?+$)""")

# One volumes entry: short syntax <host>:<container>[:mode], or long syntax with type: bind.
def compose_volume_re():
    return r"""(?xs)
(?(DEFINE)
""" + fs_define(False, "compose") + r"""
)
\A (?: ["']?+ (?&root) :
  | (?= .*? (?:\A|\n) [ \t]*+ (?: - [ \t]++ )?+ type [ \t]*+ : [ \t]*+ ["']?+ bind ["']?+ [ \t]*+ (?: \#[^\n]*+ )? (?:\n|\z) )
    .*? (?:\A|\n) [ \t]*+ (?: - [ \t]++ )?+ source [ \t]*+ : [ \t]*+
    # A plain ~ is YAML null, not a home.
    (?: ["'] (?&root) ["'] | (?! ~ [ \t]*+ (?: \#|\n|\z ) ) (?&root) ) [ \t]*+ (?: \#[^\n]*+ )? (?:\n|\z) )"""


def compose_rule():
    s = f"rules:\n  - id: {HOST_ID}-compose\n"
    s += ind(HOST_SYNC_NOTE, 4)
    s += """    # A compose service counts as an MCP server when its key, container_name or image has
    # "mcp" as a name part, it publishes a port named for MCP (${MCP_PORT:-8081}), or its
    # command or entrypoint starts one. Host monitoring agents
    # (node-exporter, cAdvisor, ...) that sit next to an MCP project and mount / for disk
    # stats are left alone. mcp-filesystem-root-too-broad has no compose twin, so this rule
    # also reports the filesystem server's image here.
    languages: [yaml]
    severity: WARNING
""" + HOST_MESSAGE.replace("This MCP server runs in a container", "This compose service runs an MCP server in a container") + COMPOSE_PATHS
    s += "    patterns:\n      - pattern-either:\n"
    for key, var, regex in (("volumes", "$SVC", MCP_NAME), ("image", "$IMG", MCP_NAME),
                            ("container_name", "$CN", MCP_NAME), ("ports", "$P", MCP_NAME),
                            ("command", "$CMD", MCP_COMMAND),
                            ("entrypoint", "$CMD", MCP_COMMAND)):
        s += "          - patterns:\n"
        s += f"              - pattern-inside: |\n                  $SVC:\n                    ...\n"
        value = {"volumes": "$VOLS", "ports": "[..., $P, ...]"}.get(key, var)
        s += f"                    {key}: {value}\n                    ...\n"
        s += mvr(var, regex, 14, literal=True)
    s += """      - pattern-not-inside:
          patterns:
            - pattern: |
                $SVC2:
                  ...
                  image: $MIMG
                  ...
"""
    s += mvr("$MIMG", MONITOR_IMAGE, 12, literal=True)
    s += "      - pattern: 'volumes: [..., $VOL, ...]'\n"
    s += mvr("$VOL", compose_volume_re(), 6, literal=True)
    s += "      - focus-metavariable: $VOL\n" + host_metadata("compose", "mcp-server")
    return s


def render() -> dict[Path, str]:
    """The rule files and the content this script generates for each."""
    out = {}
    for k in KINDS.values():
        out.update({
            **{RULE_DIR / f"{k['id']}{SUFFIX[g[0]]}.yaml": json_rule(k, g) for g in JSON_GROUPS},
            RULE_DIR / f"{k['id']}-yaml.yaml": yaml_rule(k),
            RULE_DIR / f"{k['id']}-toml.yaml": toml_rule(k),
            RULE_DIR / f"{k['id']}-workspace.yaml": workspace_rule(k),
            RULE_DIR / f"{k['id']}-subagent.yaml": subagent_rule(k),
        })
    out[RULE_DIR / f"{HOST_ID}-compose.yaml"] = compose_rule()
    return out


def main() -> int:
    for path, content in render().items():
        if not path.exists() or path.read_text() != content:
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
