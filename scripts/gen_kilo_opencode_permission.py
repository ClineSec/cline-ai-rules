#!/usr/bin/env python3
"""Generate the opencode / Kilo Code permission rules from one set of key and pattern tests.

opencode and Kilo Code (v7, built on opencode) decide whether a tool call runs, asks, or is
blocked from "permission" rules (verified 2026-10-23 against opencode v1.19.4, commit
148842ef7cb1, and Kilo Code v7.8.17, commit eb11204e8f14):

- A rule is "allow", "ask" or "deny", for every tool ("permission": "allow", or a "*" key) or
  per permission key: bash, edit (all file writes), external_directory, webfetch, task, ...,
  and an MCP tool's <server>_<tool> name, where a glob ("github_*") covers a whole server.
- A key can hold a pattern map instead ("bash": {"*": "ask", "git status *": "allow"}), matched
  against the command, path, or URL. The last matching rule wins, in file order, for keys and
  for patterns: {"bash": "allow", "*": "ask"} asks before every command.
- The same rules sit at the top level, per agent ("agent": {"<name>": {"permission": ...}}, and
  the older "mode" key), and in agent Markdown front matter (agent/, agents/, mode/ and modes/
  folders of a config directory). The deprecated "tools" map is converted to rules: true is
  "allow" (write and patch become edit), false is "deny", and an explicit permission wins.
- Defaults: opencode starts every agent from "*": "allow" (doom_loop and external_directory
  ask, .env reads ask). Kilo starts from the same "*": "allow" but sets bash to "*": "ask" with
  a list of read-only commands allowed (and edit to ask in its JetBrains plugin). In both, a
  project's opencode.json(c), kilo.json(c) (Kilo), and .opencode/ or .kilo/.kilocode/ folders
  are loaded without a prompt and override the user's global config.

The rules flag allows that cover a whole surface: every tool, every shell command (a wildcard,
or a shell or command runner followed by one: "bash *", "sudo *"), every file edit, every path
outside the project (or all of home), and all of an MCP server's tools. Specific allows
("git status *", "npm test", "docs/**", a named tool) are left alone, and so is a glob after a
read verb ("github_get_*"), using the tool-name test from gen_mcp_auto_approve.py.

Four rules share these tests: the JSON config files, agent and mode Markdown front matter,
environment variables that carry the same settings (OPENCODE_PERMISSION, KILO_PERMISSION, and
the *_CONFIG_CONTENT variables), and Kilo's custom modes files, whose groups become permission
rules.

The JSON files are scanned as text: OpenGrep's JSON parser skips .jsonc files even when
paths.include names them, and Kilo's documented file is kilo.jsonc. Each rule walks the members
of a permission (or tools) object with \\G, so every flagged member is its own finding and a
member nested in another key's pattern map never counts as a top-level one.

Edit this script, not the rule files. scripts/build.py regenerates them, and
scripts/build.py --check fails when a rule file differs from what this script produces.

Usage:
    python3 scripts/gen_kilo_opencode_permission.py    # rewrite the rule files
"""

from __future__ import annotations

import sys
from pathlib import Path

from gen_mcp_auto_approve import TOOL_DEFINE
from gen_mcp_unpinned import ind, pregex

# Only the read-verb test of the shared tool-name groups is used here.
READ_DEFINE = "\n".join(line for line in TOOL_DEFINE.splitlines() if "(?<act>" not in line)

ROOT = Path(__file__).resolve().parent.parent
RULE_DIR = ROOT / "rules" / "agent-config" / "permissions"

# ---- key and pattern tests (the text inside the quotes) ------------------------------------

# A key or pattern that is only wildcards: "*", "**", "* *", "**/*".
ANY = r"[*/\x20]*\*[*/\x20]*"
# An MCP tool glob (or any other non-built-in glob key): a "*" or "?" with no read verb before
# it, so "github_*" counts and "github_get_*" doesn't. Built-in keys never hold a glob.
MCP = r"(?! " + ANY + r" (?:[\"':\s\\]|$) ) (?: (?! (?&read) ) [^*?\"'\s:{},\\] )*? [*?] [^\"'\s:{},\\]*+"
# Keys whose plain "allow" approves a whole surface.
SCALAR_KEY = r"(?: " + ANY + r" | bash | edit | external_directory | " + MCP + r" )"
# A shell or command runner followed only by a wildcard runs anything: "bash *", "sh -c *",
# "sudo *", "env *". Command prefixes ("git *", "npm test *") are left to the narrower rules.
RUNNER = r"(?: bash | sh | zsh | dash | ksh | mksh | fish | pwsh | powershell | cmd | eval | exec | sudo | doas | env | xargs | nohup | command )"
# So does an interpreter or package runner followed only by a wildcard, or by code flags and
# one: "python *", "node -e *", "npx *", "npm exec *", "uv run *". A module, script, or package
# named before the wildcard is narrow and stays quiet: "python -m pytest *", "npx eslint *".
INTERP = (r"(?: (?: python | py | pypy ) [\d.]* | node | nodejs | bun | bunx | deno | ruby | perl | php | lua | luajit"
          r" | Rscript | tsx | ts-node | npx | pnpx | uvx"
          r" | (?: npm | pnpm | yarn ) \x20+ (?: exec | dlx ) | bun \x20+ x | uv \x20+ (?: tool \x20+ )? run"
          r" | pipx \x20+ run | poetry \x20+ run | bundle \x20+ exec )")
# The program may have a path (".venv/bin/python *", "/usr/bin/env *"). Flags are allowed
# between the runner and the wildcard, except a shell's -n (--noexec), which only checks
# syntax ("bash -n *"). After an interpreter only short flags and the eval and print flags
# count, so "node --test *" stays quiet.
BASH_PATTERN = (r"(?: " + ANY + r" | (?: " + RUNNER + r" \x20+ (?: -[\w-]+ \x20+ )*? )*?"
                r" (?: [\w.~$:-]*+ [/\\]{1,2} )*+"
                r" (?: " + RUNNER + r" (?: \.exe )? (?: \x20+ (?! -n \x20 | --noexec \x20 ) (?: --?[\w-]+ | /[cCkK] ) )*"
                r" | " + INTERP + r" (?: \.exe )? (?: \x20+ (?: -[A-Za-z]{1,3} | --eval | --print | --yes ) )* )"
                r" \x20* \* )")
EDIT_PATTERN = r"(?: (?: \./ )? " + ANY + r" )"
# external_directory patterns are absolute: everything, the filesystem root, or all of home.
EXT_PATTERN = r"(?: (?: ~ | \$HOME | [A-Za-z]: )? [*/\\\x20]* \* [*/\\\x20]* )"
# The deprecated tools map, by kind of key: (name, the tools key whose true becomes a broad
# allow, the permission key that overrides it). A permission member for the same key, or a "*"
# one, wins over the converted entry (opencode config/config.ts and agent.ts normalize); for
# MCP globs any glob key in the permission object counts, since the two globs can't be compared.
GLOB = r"[^\"'\s:{},]*[*?][^\"'\s:{},]*"
TOOLS_CLASSES = [
    ("bash", r"bash", r"(?: " + ANY + r" | bash )"),
    ("edit", r"(?: edit | write | patch )", r"(?: " + ANY + r" | edit )"),
    ("all", ANY, ANY),
    ("mcp", MCP, GLOB),
]


def qk_json(k):
    return rf'"{k}"'


def qk_esc(k):
    """A key inside a JSON string that is itself in double quotes: \\"bash\\"."""
    return rf'\\"{k}\\"'


QK = {"json": qk_json, "esc": qk_esc}


def qk_yaml(k):
    """A YAML key or flow scalar: double-quoted, single-quoted, or plain (then a colon)."""
    return rf"""(?: "{k}" | '{k}' | {k} (?=[ \t]*:) )"""


# ---- the flow walker (JSON and YAML flow mappings) -----------------------------------------

FLOW_DEFINE = {
    "json": r"""(?(DEFINE)
  (?<c> (?: \s++ | //[^\n]*+ | /\*(?s:.*?)\*/ )*+ )
  (?<s> "(?:[^"\\\n]|\\.)*+" )
  (?<o> \{ (?: [^{}\[\]"/]++ | (?&s) | //[^\n]*+ | /\*(?s:.*?)\*/ | / | (?&o) | (?&a) )*+ \} )
  (?<a> \[ (?: [^{}\[\]"/]++ | (?&s) | //[^\n]*+ | /\*(?s:.*?)\*/ | / | (?&o) | (?&a) )*+ \] )
  (?<k> (?&s) )
  (?<m> (?&k) (?&c) : (?&c) (?: (?&s) | (?&o) | (?&a) | [\w.+-]++ ) )
)""",
    # JSON inside a double-quoted string ("{\"bash\": \"allow\"}"): every quote is \", and a
    # backslash before a newline continues a shell string.
    "esc": r"""(?(DEFINE)
  (?<c> (?: \s++ | \\\r?\n )*+ )
  (?<s> \\" (?: [^"\\\n] | \\[^"\n] )*+ \\" )
  (?<o> \{ (?: [^{}\[\]"\\]++ | (?&s) | \\(?!") | (?&o) | (?&a) )*+ \} )
  (?<a> \[ (?: [^{}\[\]"\\]++ | (?&s) | \\(?!") | (?&o) | (?&a) )*+ \] )
  (?<k> (?&s) )
  (?<m> (?&k) (?&c) : (?&c) (?: (?&s) | (?&o) | (?&a) | [\w.+-]++ ) )
)""",
    "yaml": r"""(?(DEFINE)
  (?<c> (?: \s++ | \#[^\n]*+ )*+ )
  (?<s> "(?:[^"\\\n]|\\.)*+" | '(?:[^'\n]|'')*+' )
  (?<b> [^\s"'{}\[\],:\#] (?: [^\n{}\[\],:\#] | :(?!\s) )*+ )
  (?<o> \{ (?: [^{}\[\]"'\#]++ | (?&s) | \#[^\n]*+ | (?&o) | (?&a) )*+ \} )
  (?<a> \[ (?: [^{}\[\]"'\#]++ | (?&s) | \#[^\n]*+ | (?&o) | (?&a) )*+ \] )
  (?<k> (?&s) | (?&b) )
  (?<m> (?&k) (?&c) : (?&c) (?: (?&s) | (?&o) | (?&a) | (?&b) ) )
)""",
}

FLOW_VALUE = {
    "allow": r"""(?: "allow" | 'allow' | allow (?![^\s,}\]\#/]) )""",
    "true": r"""(?: true | True | TRUE ) (?![^\s,}\]\#/])""",
    "esc-allow": r'\\"allow\\"',
}


def flow_rest(qk, value):
    """The rest of an object after a member, through its closing brace, with no later "*"
    member whose value isn't the flagged one (a later "*" rule overrides every earlier one)."""
    star = qk(ANY)
    return (rf"""(?: (?&c) , (?&c) (?: (?! {star} (?&c) : ) (?&m) | {star} (?&c) : (?&c) {value} ) )*+"""
            r""" (?&c) ,? (?&c) \}""")


def flow_walker(fmt, start, keys, value, maps):
    """A regex that reports each flagged member of the flow object opened by `start`.

    `keys` is the test for a flagged key with a scalar value; `maps` (or None) lists
    (key test, pattern test) pairs for keys whose pattern map is searched for a flagged
    pattern. The finding is the named group HIT. \\G resumes after the previous finding, so
    each flagged member of the same object is its own match."""
    qk = QK.get(fmt, qk_yaml)
    val = FLOW_VALUE["esc-" + value if fmt == "esc" else value]
    rest = flow_rest(qk, val)
    s = "(?x)(?m)\n" + READ_DEFINE + "\n" + FLOW_DEFINE[fmt] + "\n"
    s += f"(?: {start} (?&c) | \\G (?&c) , (?&c) )\n"
    s += "(?: (?&m) (?&c) , (?&c) )*?\n"
    s += f"(?: (?= {qk(keys)} (?&c) : (?&c) {val} )\n"
    if maps:
        names = [f"p{i}" for i in range(len(maps))]
        alts = " | ".join(f"{qk(k)} (?<{n}>)" for (k, _), n in zip(maps, names))
        cond = qk(maps[-1][1])
        for (_, p), n in reversed(list(zip(maps[:-1], names[:-1]))):
            cond = f"(?(<{n}>) {qk(p)} | {cond} )"
        s += f"  | (?<inmap>) (?: {alts} ) (?&c) : (?&c) \\{{ (?&c)\n"
        s += "    (?: (?&m) (?&c) , (?&c) )*?\n"
        s += f"    (?= {cond} (?&c) : (?&c) {val} )\n"
    s += ")\n"
    s += f"(?<HIT> (?&k) (?&c) : (?&c) {val} )\n"
    if maps:
        s += f"(?(<inmap>) {rest} )\n"
    s += f"(?= {rest} )"
    return s


PERMISSION_MAPS = [
    ("bash", BASH_PATTERN),
    ("edit", EDIT_PATTERN),
    ("external_directory", EXT_PATTERN),
    (r"(?: " + ANY + r" | " + MCP + r" )", ANY),
]

# ---- the block walker (YAML front matter) --------------------------------------------------

BLOCK_DEFINE = r"""(?(DEFINE)
  (?<nl> \r?\n | \z )
  (?<bl> [ \t]*+ (?: \#[^\n]*+ )? \r?\n )
  (?<ky> "(?:[^"\\\n]|\\.)*+" | '(?:[^'\n]|'')*+' | [^\s"'\#:] (?: [^\n:] | :(?![\s]) )*? (?=[ \t]*:) )
  (?<mem> \k<I> (?![ \t]) [^\n]*+ (?&nl) (?: \k<I> [ \t]++ [^\s\#] [^\n]*+ (?&nl) | (?&bl) )*+ )
)"""

BLOCK_VALUE = {
    "allow": r"""(?: "allow" | 'allow' | allow )""",
    "true": r"""(?: true | True | TRUE )""",
}

EOL = r"[ \t]*+ (?: \#[^\n]*+ )? (?&nl)"


def block_walker(start, keys, value, maps):
    """The block-mapping twin of flow_walker, for YAML front matter: members are lines at the
    first child's indent (I), their pattern maps at a deeper indent; a member can also hold a
    flow map ("bash": {"*": allow}) on its line. `start` matches up to the parent key's line."""
    qk = qk_yaml
    val = BLOCK_VALUE[value]
    fval = FLOW_VALUE[value]
    star = qk(ANY)
    later_star = rf"(?! \k<I> {star} [ \t]*: (?! [ \t]* {val} {EOL} ) )"
    outer_rest = rf"(?= (?: {later_star} (?&mem) | (?&bl) )*+ (?! \k<I> [^\s] ) )"
    s = "(?x)(?m)\n" + READ_DEFINE + "\n" + BLOCK_DEFINE + "\n" + FLOW_DEFINE["yaml"] + "\n"
    s += rf"(?: {start} [ \t]*: {EOL} | \G )" + "\n"
    s += r"(?&bl)*+ (?= (?<I>[ \t]++) [^\s\#] )" + "\n"
    s += "(?&mem)*?\n"
    s += r"\k<I>" + "\n"
    s += f"(?: (?= {qk(keys)} [ \\t]*: [ \\t]* {val} {EOL} )\n"
    if maps:
        names = [f"p{i}" for i in range(len(maps))]
        fnames = [f"f{i}" for i in range(len(maps))]

        def cond(ns):
            c = qk(maps[-1][1])
            for (_, p), n in reversed(list(zip(maps[:-1], ns[:-1]))):
                c = f"(?(<{n}>) {qk(p)} | {c} )"
            return c

        alts = " | ".join(f"{qk(k)} (?<{n}>)" for (k, _), n in zip(maps, names))
        falts = " | ".join(f"{qk(k)} (?<{n}>)" for (k, _), n in zip(maps, fnames))
        # A pattern map in block style, one pattern per deeper line.
        s += f"  | (?<inb>) (?: {alts} ) [ \\t]*: {EOL}\n"
        s += r"    (?&bl)*+ (?= (?<J> \k<I> [ \t]++ ) [^\s\#] )" + "\n"
        s += r"    (?: \k<J> (?![ \t]) [^\n]*+ (?&nl) (?&bl)*+ )*?" + "\n"
        s += rf"    \k<J> (?= {cond(names)} [ \t]*: [ \t]* {val} {EOL} )" + "\n"
        # A pattern map in flow style on the member's line.
        s += f"  | (?<inf>) (?: {falts} ) [ \\t]*: [ \\t]* \\{{ (?&c)\n"
        s += "    (?: (?&m) (?&c) , (?&c) )*?\n"
        s += f"    (?= {cond(fnames)} (?&c) : (?&c) {fval} )\n"
    s += ")\n"
    if maps:
        s += f"(?<HIT> (?: (?(<inf>) (?&k) (?&c) : (?&c) {fval} | (?&ky) [ \\t]*: [ \\t]* {val} ) ) )\n"
        inner_star = rf"(?! \k<I> [ \t]++ {star} [ \t]*: (?! [ \t]* {val} {EOL} ) )"
        s += (rf"(?(<inf>) {flow_rest(qk_yaml, fval)} {EOL} | {EOL}"
              rf" (?(<inb>) (?: {inner_star} (?: \k<I> [ \t]++ [^\s\#] [^\n]*+ (?&nl) | (?&bl) ) )*+"
              rf" (?! \k<I> [ \t]++ [^\s\#] ) ) )") + "\n"
    else:
        s += f"(?<HIT> (?&ky) [ \\t]*: [ \\t]* {val} ) {EOL}\n"
    s += outer_rest
    return s


# ---- shared rule text ----------------------------------------------------------------------

SYNC_NOTE = """# Generated by scripts/gen_kilo_opencode_permission.py, which holds the key and pattern tests
# both rules share (and the MCP tool-name test from gen_mcp_auto_approve.py). Edit the script
# and run scripts/build.py; build.py --check fails if this file drifts.
"""

WHAT = """      "permission": "allow" or a "*" key set to "allow" approves every tool (shell
      commands, file edits, web fetches, MCP tools), "bash" set to "allow" or given a "*"
      pattern (or a shell or runner followed by one, such as "bash *" or "sudo *") approves
      every shell command, "edit" approves every file write, "external_directory" set to
      "allow" (or "~/**") lets every tool read and write anywhere on the machine, and a glob
      key such as "github_*" approves all of an MCP server's tools. The deprecated "tools"
      map turns true into the same allow rules. A project's config is loaded without a
      prompt and overrides the developer's own global settings, and Kilo Code otherwise asks
      before shell commands (Kilo Code 7.8, opencode 1.19).
      A prompt injection in a file, issue, web page, or tool result the agent reads can then
      run arbitrary commands, rewrite files, or use the MCP servers with the developer's
      credentials. Keep "*" (or bash) at "ask" and allow only specific command prefixes
      ("git status *", "npm test"), paths, and named read-only MCP tools."""

METADATA = """    metadata:
      category: security
      subcategory: [audit]
      pack-category: agent-config
      owasp-llm:
        - "LLM03:2026 - Excessive Agency"
        - "LLM06:2025 - Excessive Agency"
      owasp-agentic:
        - "ASI02 - Tool Misuse and Exploitation"
        - "ASI05 - Unexpected Code Execution (RCE)"
      owasp-mcp:
        - "MCP02:2025 - Privilege Escalation via Scope Creep"
      owasp-aisvs:
        - "v1.01-C9.5.1 - Agent Authorization, Delegation, and Continuous Enforcement"
        - "v1.01-C9.2.1 - High-Impact Action Approval and Irreversibility Controls"
      mitre-atlas:
        - "AML.T0053 - AI Agent Tool Invocation"
        - "AML.T0112.000 - Machine Compromise: Local AI Agent"
      cwe:
        - "CWE-250: Execution with Unnecessary Privileges"
      confidence: HIGH
      likelihood: MEDIUM
      impact: HIGH
      technology: [opencode, kilo-code]
      references:
        - https://github.com/anomalyco/opencode/blob/v1.19.4/packages/web/src/content/docs/permissions.mdx
        - https://github.com/anomalyco/opencode/blob/v1.19.4/packages/opencode/src/agent/agent.ts
        - https://github.com/anomalyco/opencode/blob/v1.19.4/packages/opencode/src/config/config.ts
        - https://github.com/Kilo-Org/kilocode/blob/v7.8.17/packages/kilo-docs/pages/getting-started/settings/auto-approving-actions.md
        - https://github.com/Kilo-Org/kilocode/blob/v7.8.17/packages/opencode/src/kilocode/agent/index.ts
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md
"""


def header(rule_id, comment, severity="ERROR"):
    return (f"rules:\n  - id: {rule_id}\n" + ind(comment, 4) + ind(SYNC_NOTE, 4)
            + f"    languages: [regex]\n    severity: {severity}\n")


# ---- kilo-opencode-permission-allow (JSON and JSONC config files) --------------------------

JSON_PERMISSION_START = r"""(?m) (?: ^[ \t]*+ | [{,] [ \t]*+ ) "permission" (?&c) : (?&c) \{"""
JSON_SCALAR = r"""(?x)(?m)
(?(DEFINE) (?<c> (?: \s++ | //[^\n]*+ | /\*(?s:.*?)\*/ )*+ ) )
(?: ^[ \t]*+ | [{,] [ \t]*+ ) (?<HIT> "permission" (?&c) : (?&c) "allow" )"""


def json_tools_start(block):
    """An object's tools map, when no permission member of the same object overrides the
    flagged kind of key: a scalar permission, or a permission object with a `block` key."""
    return (r"""\{ (?= (?&c) (?: (?! "permission" (?&c) : (?&c) (?: "[a-z]*" | null"""
            rf""" | \{{ (?&c) (?: (?&m) (?&c) , (?&c) )*? "{block}" (?&c) : ) ) (?&m) (?&c) ,? (?&c) )*+ \}} )"""
            "\n  (?&c) (?: (?&m) (?&c) , (?&c) )*? \"tools\" (?&c) : (?&c) \\{")

JSON_MESSAGE = """    message: >-
      This opencode / Kilo Code permission setting lets the agent act without asking.
""" + WHAT + "\n"

JSON_COMMENT = """# Text rule over opencode.json(c) and kilo.json(c): OpenGrep's JSON parser skips .jsonc files.
"""

JSON_PATHS = """    paths:
      include:
        # Project files at any depth (opencode and Kilo read them from the working directory up
        # to the worktree root), the .opencode/, .kilo/ and .kilocode/ folders, and the user's
        # global ~/.config/opencode/ and ~/.config/kilo/ files. Kilo also reads opencode.json(c).
        - "opencode.json"
        - "opencode.jsonc"
        - "kilo.json"
        - "kilo.jsonc"
        # The older global file name, ~/.config/<tool>/config.json.
        - ".config/opencode/config.json"
        - ".config/kilo/config.json"
"""


def json_rule():
    s = header("kilo-opencode-permission-allow", JSON_COMMENT) + JSON_MESSAGE + JSON_PATHS
    s += "    pattern-either:\n"
    s += "      # \"permission\": \"allow\" sets every permission at once.\n"
    s += "      - patterns:\n" + pregex(JSON_SCALAR, 10) + "          - focus-metavariable: $HIT\n"
    s += "      # A member of a permission object (top level, per agent, per mode).\n"
    s += "      - patterns:\n"
    s += pregex(flow_walker("json", JSON_PERMISSION_START, SCALAR_KEY, "allow", PERMISSION_MAPS), 10)
    s += "          - focus-metavariable: $HIT\n"
    for name, key, block in TOOLS_CLASSES:
        s += f"      # The deprecated tools map ({name}): true becomes allow.\n"
        s += "      - patterns:\n"
        s += pregex(flow_walker("json", json_tools_start(block), key, "true", None), 10)
        s += "          - focus-metavariable: $HIT\n"
    s += METADATA
    return s


# ---- kilo-opencode-permission-allow-md (agent and mode Markdown files) ---------------------

# Each Markdown regex starts at the file's front matter and walks to its key line, rather than
# intersecting with a separate front matter range: eleven intersected ranges made OpenGrep spend
# seconds on every agent file.
FM_OPEN = r"\A (?:\x{FEFF})? ---[ \t]*\r?\n"
FM_LINES = r"(?: (?! ---[ \t]*\r?$ ) [^\n]*+ \n )*?"


def fm_key(key, unblocked=None):
    """From the front matter's opening line to the start of `key` at the top level."""
    guard = ""
    if unblocked is not None:
        guard = (rf" (?= (?: (?! ---[ \t]*\r?$ ) (?! {blocking(unblocked)} ) [^\n]*+ \n )*?"
                 r" ---[ \t]*(?:\r?\n|\z) )")
    return f"{FM_OPEN}{guard} {FM_LINES} {qk_yaml(key)}"


def blocking(block):
    """A permission key that overrides the tools entries of one kind: a scalar permission, or
    a `block` key in a flow or block permission mapping."""
    k = qk_yaml(block)
    return (r"(?: permission | \"permission\" | 'permission' ) [ \t]*: (?:"
            r" [ \t]*+ [\"']?[a-z]+[\"']? [ \t]*+ (?:\#[^\n]*+)? \r?$"
            rf" | [ \t]*+ \{{ [^\n]*? [{{,\s] {k} [ \t]*:"
            r" | [ \t]*+ (?:\#[^\n]*+)? \r?\n (?: [ \t]*+ (?:\#[^\n]*+)? \r?\n )*+ (?= (?<P>[ \t]++) [^\s\#] )"
            r" (?: \k<P> (?![ \t]) [^\n]*+ \n (?: \k<P> [ \t]++ [^\n]*+ \n | [ \t]*+ (?:\#[^\n]*+)? \r?\n )*+ )*?"
            rf" \k<P> {k} [ \t]*: )")


MD_SCALAR = (r"(?x)(?m)" + "\n" + FM_OPEN + " " + FM_LINES + "\n"
             r"(?<HIT> (?: permission | \"permission\" | 'permission' ) [ \t]*: [ \t]* (?: \"allow\" | 'allow' | allow ) )"
             r" [ \t]*+ (?: \#[^\n]*+ )? \r?$")

MD_MESSAGE = """    message: >-
      This opencode / Kilo Code agent file's permission front matter lets the agent act
      without asking while it runs.
""" + WHAT + "\n"

MD_COMMENT = """# Text rule: the YAML front matter of agent and mode Markdown files.
"""

MD_PATHS = """    paths:
      include:
        # Agents ({agent,agents}/**/*.md) and modes ({mode,modes}/*.md) in every config folder:
        # project .opencode/ (opencode), .kilo/ and the older .kilocode/ (Kilo), and the user's
        # ~/.config/opencode/ and ~/.config/kilo/ (opencode v1.19.4 config/agent.ts and
        # paths.ts, Kilo v7.8.17).
        - ".opencode/agent/**/*.md"
        - ".opencode/agents/**/*.md"
        - ".opencode/mode/*.md"
        - ".opencode/modes/*.md"
        - ".kilo/agent/**/*.md"
        - ".kilo/agents/**/*.md"
        - ".kilo/mode/*.md"
        - ".kilo/modes/*.md"
        - ".kilocode/agent/**/*.md"
        - ".kilocode/agents/**/*.md"
        - ".kilocode/mode/*.md"
        - ".kilocode/modes/*.md"
        - ".config/opencode/agent/**/*.md"
        - ".config/opencode/agents/**/*.md"
        - ".config/opencode/mode/*.md"
        - ".config/opencode/modes/*.md"
        - ".config/kilo/agent/**/*.md"
        - ".config/kilo/agents/**/*.md"
        - ".config/kilo/mode/*.md"
        - ".config/kilo/modes/*.md"
"""


def md_branch(comment, regex):
    return (f"      # {comment}\n      - patterns:\n" + pregex(regex, 10)
            + "          - focus-metavariable: $HIT\n")


def md_rule():
    s = header("kilo-opencode-permission-allow-md", MD_COMMENT) + MD_MESSAGE + MD_PATHS
    s += "    pattern-either:\n"
    s += md_branch("permission: allow sets every permission at once.", MD_SCALAR)
    s += md_branch("A member of the permission block.",
                   block_walker(fm_key("permission"), SCALAR_KEY, "allow", PERMISSION_MAPS))
    s += md_branch("permission written as a flow mapping.", flow_walker(
        "yaml", fm_key("permission") + r" [ \t]*: [ \t]* \{", SCALAR_KEY, "allow", PERMISSION_MAPS))
    for name, key, block in TOOLS_CLASSES:
        s += md_branch(f"The deprecated tools map ({name}), unless permission overrides it.",
                       block_walker(fm_key("tools", block), key, "true", None))
        s += md_branch(f"The tools map ({name}) as a flow mapping.", flow_walker(
            "yaml", fm_key("tools", block) + r" [ \t]*: [ \t]* \{", key, "true", None))
    s += METADATA
    return s


# ---- kilo-opencode-permission-allow-modes (Kilo's custom modes files) ----------------------

# Kilo Code 7 still loads the custom modes of the older Kilo extension (kilocode/modes-migrator.ts):
# ~/.kilocodemodes, the project's .kilocodemodes, and the global custom_modes.yaml. Each mode
# becomes a primary agent, and its groups become permission rules: "command" and "browser"
# become bash "allow", "edit" becomes edit "allow" (or, with a fileRegex, allow for that
# pattern and deny for the rest), and a missing read, edit, bash, or mcp group becomes "deny".
# Modes named like a built-in agent (code, build, architect, ask, debug, orchestrator) are
# skipped. The file is YAML (gray-matter), so JSON files are read too.
MODE_GROUP = r"""(?: "(?:command|browser|edit)" | '(?:command|browser|edit)' | (?:command|browser|edit) (?![\w-]) )"""
DEFAULT_SLUG = r"""["']? (?: code | build | architect | ask | debug | orchestrator ) ["']?"""
QK_SLUG = qk_yaml("slug")
QK_GROUPS = qk_yaml("groups")
# A group in a flow sequence: the name alone, or [name, {options}] without a fileRegex.
FLOW_GROUP = (rf"""(?: {MODE_GROUP} (?= (?&c) [,\]] )"""
              rf""" | \[ (?&c) {MODE_GROUP} (?&c) (?: , (?&c) (?! \{{ [^{{}}]*? fileRegex ) (?&o) (?&c) )? ,? (?&c) \] )""")
FLOW_GROUPS = r"""\[ (?&c) (?: (?: (?&s) | (?&o) | (?&a) | (?&b) ) (?&c) , (?&c) )*?"""

# A mode written as a flow mapping (a .kilocodemodes JSON file, or {slug: x, groups: [...]}).
MODES_FLOW = ("(?x)\n" + FLOW_DEFINE["yaml"] + "\n"
              + rf"""\{{ (?! (?&c) (?: (?&m) (?&c) , (?&c) )*? {QK_SLUG} (?&c) : (?&c) {DEFAULT_SLUG} (?&c) [,}}] )""" + "\n"
              + rf"""(?&c) (?: (?&m) (?&c) , (?&c) )*? {QK_GROUPS} (?&c) : (?&c) {FLOW_GROUPS} (?<HIT> {FLOW_GROUP} )""")

# A mode written as a block sequence item ("- slug: x" and deeper lines), with its groups as a
# block sequence (one group per "- " line, or "- - edit" with options below it) or a flow one.
ITEM_LINES = r"(?: [^\n]*+ \n (?= \k<D> [ \t]++ [^\s\#] | [ \t]*+ (?:\#[^\n]*+)? \r?\n ) )*?"
BLOCK_GROUP = (rf"""(?: {MODE_GROUP} [ \t]*+ (?:\#[^\n]*+)? \r?$"""
               rf""" | - [ \t]++ {MODE_GROUP} [ \t]*+ (?:\#[^\n]*+)? \r?$"""
               r""" (?! \r?\n (?: \k<G> [ \t]++ [^\n]*+ \n | [ \t]*+ (?:\#[^\n]*+)? \r?\n )*? \k<G> [ \t]++ (?: - [ \t]++ )? ["']?fileRegex )"""
               rf""" | {FLOW_GROUP} [ \t]*+ (?:\#[^\n]*+)? \r?$ )""")
MODES_BLOCK = ("(?x)(?m)\n" + FLOW_DEFINE["yaml"] + "\n"
               + r"^ (?<D>[ \t]*+) - [ \t]++" + "\n"
               + rf"(?! {ITEM_LINES} [ \t]*+ {QK_SLUG} [ \t]*: [ \t]*+ {DEFAULT_SLUG} [ \t]*+ (?:\#[^\n]*+)? \r?$ )" + "\n"
               + rf"{ITEM_LINES} [ \t]*+ {QK_GROUPS} [ \t]*: [ \t]*+" + "\n"
               + r"(?: (?<fl>) " + FLOW_GROUPS + "\n"
               + r"  | (?:\#[^\n]*+)? \r?\n (?: [ \t]*+ (?:\#[^\n]*+)? \r?\n )*+ (?= (?<G> [ \t]*+ ) - \s )" + "\n"
               + r"    (?: \k<G> - [^\n]*+ \n (?: \k<G> [ \t]++ [^\n]*+ \n | [ \t]*+ (?:\#[^\n]*+)? \r?\n )*+ )*?" + "\n"
               + r"    \k<G> - [ \t]++ )" + "\n"
               + rf"(?<HIT> (?(<fl>) {FLOW_GROUP} | {BLOCK_GROUP} ) )")

MODES_MESSAGE = """    message: >-
      In Kilo Code 7 this custom mode becomes an agent whose groups are permission rules:
      "command" (and "browser") becomes bash "allow", so the mode runs every shell command
      without asking, and "edit" without a fileRegex becomes edit "allow", so it writes any
      file without asking. Kilo otherwise asks before shell commands. A project's
      .kilocodemodes is loaded without a prompt (Kilo Code 7.8), so anyone who picks this mode
      in a clone gets those allows. A prompt injection in a file, issue, web page, or tool
      result the agent reads can then run arbitrary commands or rewrite files. Limit edit with a fileRegex, drop command and browser from modes that
      don't need a shell, or define the mode as a Kilo agent with bash rules that ask
      ("*": "ask") and allow only specific commands.
"""

MODES_COMMENT = """# Text rule over Kilo's custom modes files (.kilocodemodes and custom_modes.yaml, YAML or
# JSON). One finding per mode, at its first group that becomes a wholesale allow. INFO: the
# allows apply only once someone picks the mode, and most custom modes in public repositories
# carry "command" or "edit", so this is for review rather than a build gate.
"""

MODES_PATHS = """    paths:
      include:
        # The project's (and the home folder's) .kilocodemodes, and the global custom_modes.yaml
        # of the Kilo CLI and VS Code extension (Kilo v7.8.17 kilocode/modes-migrator.ts).
        - ".kilocodemodes"
        - ".kilocode/cli/global/settings/custom_modes.yaml"
        - "kilocode.kilo-code/settings/custom_modes.yaml"
"""


def modes_rule():
    s = header("kilo-opencode-permission-allow-modes", MODES_COMMENT, "INFO")
    s += MODES_MESSAGE + MODES_PATHS + "    pattern-either:\n"
    s += md_branch("A mode as a flow mapping (JSON files).", MODES_FLOW)
    s += md_branch("A mode as a block sequence item.", MODES_BLOCK)
    s += (METADATA.replace("      confidence: HIGH\n", "      confidence: MEDIUM\n")
          .replace("      likelihood: MEDIUM\n", "      likelihood: LOW\n")
          .replace("      technology: [opencode, kilo-code]\n", "      technology: [kilo-code]\n")
          .replace("        - https://github.com/Kilo-Org/kilocode/blob/v7.8.17/packages/opencode/src/kilocode/agent/index.ts\n",
                   "        - https://github.com/Kilo-Org/kilocode/blob/v7.8.17/packages/opencode/src/kilocode/agent/index.ts\n"
                   "        - https://github.com/Kilo-Org/kilocode/blob/v7.8.17/packages/opencode/src/kilocode/modes-migrator.ts\n"))
    return s


# ---- kilo-opencode-permission-allow-env (the same settings in environment variables) -------

# OPENCODE_PERMISSION / KILO_PERMISSION hold a permission object as JSON, merged over the
# top-level permission of every config file (opencode config/config.ts; Kilo reads only the
# KILO_ names). OPENCODE_CONFIG_CONTENT / KILO_CONFIG_CONTENT hold a whole config, loaded after
# the project's files. The rule reads the JSON where it is written into the variable: a YAML
# env entry (quoted or a | block), a shell or .env assignment, a Dockerfile ENV, a ${VAR:-...}
# default, or a JSON string. A value built at run time ("$PERMS") is not read.
ENV_SEP = r"""["']? (?: [ \t]* (?: :- | := | : | = ) [ \t]* | [ \t]+ (?= ["']? \{ ) ) (?: \$\{ \w+ :?[-=] )?"""
BLOCK_SCALAR = r"""[|>] [-+]? \d? [-+]? [ \t]*+ (?: \#[^\n]*+ )? \r?\n (?: [ \t]*+ \r?\n )*+ [ \t]*+"""


def env_start(names, fmt):
    """From the variable's name to the opening brace of its JSON value."""
    # Not on a comment line: a # at the start of a line or after a space ends the search.
    name = rf"^ (?: [^\#\n] | (?<=\S)\# )*? (?<![\w$-]) (?: {names} )"
    if fmt == "esc":
        return rf"{name} {ENV_SEP} [\"']? (?= \{{ (?&c) \\\" )"
    return rf"{name} {ENV_SEP} (?: ' | {BLOCK_SCALAR} )? (?= \{{ (?&c) \" )"


PERM_VARS = r"(?: OPENCODE | KILO )_PERMISSION"
CONFIG_VARS = r"(?: OPENCODE | KILO )_CONFIG_CONTENT"


def config_object(fmt):
    """In a config held by a variable, the opening brace of the top-level object or of one
    agent's (or mode's) object."""
    qk = QK[fmt]
    walk = "(?&c) (?: (?&m) (?&c) , (?&c) )*?"
    return (env_start(CONFIG_VARS, fmt)
            + rf" (?: \{{ {walk} (?: {qk('agent')} | {qk('mode')} ) (?&c) : (?&c) \{{ {walk} (?&k) (?&c) : (?&c) )?")


def env_scalar(fmt):
    qk = QK[fmt]
    val = FLOW_VALUE["esc-allow" if fmt == "esc" else "allow"]
    return ("(?x)(?m)\n" + FLOW_DEFINE[fmt] + "\n" + config_object(fmt) + "\n"
            + rf"\{{ (?&c) (?: (?&m) (?&c) , (?&c) )*? (?<HIT> {qk('permission')} (?&c) : (?&c) {val} )")


def env_permission(fmt):
    qk = QK[fmt]
    return (config_object(fmt) + "\n"
            + rf"\{{ (?&c) (?: (?&m) (?&c) , (?&c) )*? {qk('permission')} (?&c) : (?&c) \{{")


ENV_MESSAGE = """    message: >-
      This environment variable gives opencode / Kilo Code permission rules that let the
      agent act without asking. OPENCODE_PERMISSION and KILO_PERMISSION are merged over the
      permission settings of every config file, and OPENCODE_CONFIG_CONTENT and
      KILO_CONFIG_CONTENT are loaded after the project's config.
""" + WHAT + "\n"

ENV_COMMENT = """# Text rule over CI files, Dockerfiles, compose files, .env files, and shell scripts that set
# OPENCODE_PERMISSION, KILO_PERMISSION, OPENCODE_CONFIG_CONTENT, or KILO_CONFIG_CONTENT.
"""

ENV_PATHS = """    paths:
      include:
        # CI and other YAML (GitHub Actions and GitLab env:, compose environment:, Kubernetes
        # env), container files, .env files, shell scripts and profiles, and make/just files.
        - "*.yml"
        - "*.yaml"
        - "Jenkinsfile"
        - "Dockerfile"
        - "Dockerfile.*"
        - "*.Dockerfile"
        - "*.dockerfile"
        - "Containerfile"
        - "devcontainer.json"
        - ".env"
        - ".env.*"
        - "*.env"
        - "*.sh"
        - "*.bash"
        - "*.zsh"
        - ".bashrc"
        - ".bash_profile"
        - ".zshrc"
        - ".zshenv"
        - ".profile"
        - ".envrc"
        - "Makefile"
        - "GNUmakefile"
        - "*.mk"
        - "justfile"
        - "Justfile"
"""


def env_rule():
    s = header("kilo-opencode-permission-allow-env", ENV_COMMENT) + ENV_MESSAGE + ENV_PATHS
    s += "    pattern-either:\n"
    for fmt, how in (("json", "JSON"), ("esc", "JSON with escaped quotes")):
        s += md_branch(f"OPENCODE_PERMISSION / KILO_PERMISSION ({how}).", flow_walker(
            fmt, env_start(PERM_VARS, fmt) + r" \{", SCALAR_KEY, "allow", PERMISSION_MAPS))
        s += md_branch(f"\"permission\": \"allow\" in a config variable ({how}).", env_scalar(fmt))
        s += md_branch(f"A permission object in a config variable ({how}).", flow_walker(
            fmt, env_permission(fmt), SCALAR_KEY, "allow", PERMISSION_MAPS))
    for name, key, block in TOOLS_CLASSES:
        s += md_branch(f"The deprecated tools map ({name}) in a config variable.", flow_walker(
            "json", config_object("json") + "\n" + json_tools_start(block), key, "true", None))
    s += METADATA
    return s


def render() -> dict[Path, str]:
    """The rule files and the content this script generates for each."""
    return {
        RULE_DIR / "kilo-opencode-permission-allow.yaml": json_rule(),
        RULE_DIR / "kilo-opencode-permission-allow-md.yaml": md_rule(),
        RULE_DIR / "kilo-opencode-permission-allow-modes.yaml": modes_rule(),
        RULE_DIR / "kilo-opencode-permission-allow-env.yaml": env_rule(),
    }


def main() -> int:
    for path, content in render().items():
        if not path.exists() or path.read_text() != content:
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
