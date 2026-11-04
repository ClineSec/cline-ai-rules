#!/usr/bin/env python3
"""Generate the tool-returns-environment rules (MCP and agent tools, Python and TypeScript).

The four rules flag a tool handler that returns the process environment to the model: the whole
environment (os.environ / process.env, a parsed .env file, the output of `env` or `printenv`,
/proc/<pid>/environ) or one variable named like a secret. What differs between them is only where
a tool handler is, and the sibling tool-argument rules already know that, so this script copies
the handler shapes instead of keeping hand-synced copies:

- mcp-tool-returns-environment: the registration shapes of mcp-tool-arg-to-shell's first source
  (MCPServer / FastMCP / fastmcp @tool, @server.call_tool(), add_tool, Claude Agent SDK @tool),
  its pydantic-ai exclusions, and its second source's v2 low-level on_call_tool handler, copied
  verbatim (build.py SHARED_BLOCKS also checks them);
- agent-tool-returns-environment: the registration shapes of agent-tool-arg-to-shell's source
  (LangChain, CrewAI, OpenAI Agents, pydantic-ai), copied verbatim (also in SHARED_BLOCKS);
- the -ts twins: the registration shapes of mcp-tool-arg-to-shell-ts and
  agent-tool-arg-to-shell-ts. Those bind the handler's first parameter (`($ARGS, ...) =>`),
  which a tool with no input doesn't have (`async () => ...`), so this script rewrites each
  `$ARGS, ...)` to `...)` and lets the v1 `server.tool(name, cb)` overloads in. render() fails
  when a rewrite no longer applies, so a change to a sibling's shapes reaches these rules or
  stops the build.

What this script adds is the environment as a taint source and the handler's return value as
the sink. The rules use taint_assume_safe_functions, so only the calls listed as propagators
(copies, serializers, string building, MCP content types) carry the environment; anything else
that takes it (subprocess.run(env=...), a client constructor) returns a clean value. Secret
names come from gen_secret_in_system_prompt.py (ENV, ENV_ATTR).

A filter clears the environment only when it can't keep a secret: it keeps entries by exact name
(k in SHOWN, k == "TZ") or drops or masks the ones named like secrets ("TOKEN" not in k,
"***" if SECRET_RE.search(k) else v). A prefix filter (k.startswith("GITHUB_")) or any other
condition still keeps GITHUB_TOKEN, so the result carries the environment; so do encodings
(base64, hex, URL-quoting, case changes) and, in TypeScript, a slice longer than a short preview.

Edit this script (or the sibling rules), not the generated rule files. scripts/build.py
regenerates them, and scripts/build.py --check fails when a rule file differs from what this
script produces.

Usage:
    python3 scripts/gen_tool_returns_environment.py    # rewrite the rule files
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

import yaml

from gen_mcp_unpinned import NOT_PAREN_RECEIVER, mvr, paren_guard
from gen_secret_in_system_prompt import ENV, ENV_ATTR

ROOT = Path(__file__).resolve().parent.parent
PY_MCP_SIBLING = ROOT / "rules" / "python" / "injection" / "mcp-tool-arg-to-shell.yaml"
PY_AGENT_SIBLING = ROOT / "rules" / "python" / "injection" / "agent-tool-arg-to-shell.yaml"
TS_MCP_SIBLING = ROOT / "rules" / "typescript" / "injection" / "mcp-tool-arg-to-shell-ts.yaml"
TS_AGENT_SIBLING = ROOT / "rules" / "typescript" / "injection" / "agent-tool-arg-to-shell-ts.yaml"
PY_MCP_RULE = ROOT / "rules" / "python" / "data-exposure" / "mcp-tool-returns-environment.yaml"
PY_AGENT_RULE = ROOT / "rules" / "python" / "data-exposure" / "agent-tool-returns-environment.yaml"
TS_MCP_RULE = ROOT / "rules" / "typescript" / "data-exposure" / "mcp-tool-returns-environment-ts.yaml"
TS_AGENT_RULE = ROOT / "rules" / "typescript" / "data-exposure" / "agent-tool-returns-environment-ts.yaml"


# ---- copying the handler shapes from the siblings -------------------------------------------

def list_items(lines: list[str], start: int, indent: int) -> list[str]:
    """The items of the YAML block list whose `- ` sits at column `indent`, starting at line
    `start`, as text. Comment lines before an item belong to it."""
    items: list[str] = []
    pending: list[str] = []
    i = start
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip(" ")
        col = len(line) - len(stripped)
        if not stripped.strip():
            pending.append(line)
        elif stripped.startswith("#") and col >= indent:
            pending.append(line)
        elif col == indent and stripped.startswith("- "):
            items.append("".join(pending) + line)
            pending = []
        elif col > indent and items:
            items[-1] += "".join(pending) + line
            pending = []
        else:
            break
        i += 1
    return items


def sibling_patterns(path: Path, source: int) -> tuple[list[str], list]:
    """The `patterns` items of pattern-sources[source] in a sibling rule, as text and as data."""
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    i = lines.index("    pattern-sources:\n") + 1
    seen = -1
    while True:
        if lines[i] == "      - patterns:\n":
            seen += 1
            if seen == source:
                break
        i += 1
    items = list_items(lines, i + 1, 10)
    data = yaml.safe_load(text)["rules"][0]["pattern-sources"][source]["patterns"]
    parsed = yaml.safe_load(textwrap.dedent("".join(items)))
    if parsed != data:
        raise SystemExit(f"gen_tool_returns_environment.py: misread the patterns of {path.relative_to(ROOT)}")
    return items, data


def reindent(text: str, n: int) -> str:
    return textwrap.indent(textwrap.dedent(text), " " * n)


def rewrite(text: str, rewrites: list[tuple[str, str]]) -> str:
    """Apply exact-text rewrites; each must apply at least once."""
    for old, new in rewrites:
        if old not in text:
            raise SystemExit(f"gen_tool_returns_environment.py: a sibling's handler shapes changed; "
                             f"no longer found:\n{old}")
        text = text.replace(old, new)
    return text


def py_mcp_shapes() -> tuple[str, str]:
    """The decorator and add_tool shapes plus the pydantic-ai exclusions (source 0, items 0-2),
    and the v2 low-level handler shapes (source 1, item 0), at the sink's indent."""
    first, _ = sibling_patterns(PY_MCP_SIBLING, 0)
    second, _ = sibling_patterns(PY_MCP_SIBLING, 1)
    return reindent("".join(first[:3]), 10), reindent(second[0], 10)


def py_agent_shapes() -> str:
    items, _ = sibling_patterns(PY_AGENT_SIBLING, 0)
    return reindent(items[0], 10)


# `($ARGS, ...)` binds the first parameter; a handler of a tool without input takes none.
TS_ARGS = [("$ARGS, ...)", "...)")]
TS_MCP_REWRITES = TS_ARGS + [(
    """              # Deprecated v1 overloads: the handler is the last argument. tool(name, cb) and
              # tool(name, description, cb) register zero-argument tools whose handler only
              # gets the request context.
              - patterns:
                  - pattern: $SERVER.tool($NAME, $X, ..., (...) => {...})
                  - pattern-not: $SERVER.tool($NAME, "$DESC", (...) => {...})
""",
    """              # Deprecated v1 overloads: the handler is the last argument, including
              # tool(name, cb) and tool(name, description, cb) for a tool without input.
              - pattern: $SERVER.tool($NAME, ..., (...) => {...})
"""), (
    # Every prompt and resource handler returns what the client reads, with or without
    # arguments and at a fixed URI too.
    """              # Prompts: registerPrompt(name, { argsSchema }, (args, ctx) => ...). Without
              # argsSchema the handler gets only the context. The v1 prompt(name,
              # [description,] argsSchema, cb) overloads are like tool()'s.
              - pattern: '$SERVER.registerPrompt($NAME, {..., argsSchema: $SCHEMA, ...}, (...) => {...})'
              - patterns:
                  - pattern: $SERVER.registerPrompt($NAME, $CONFIG, (...) => {...})
                  - pattern-not: '$SERVER.registerPrompt($NAME, {...}, (...) => {...})'
              - patterns:
                  - pattern: $SERVER.prompt($NAME, $X, ..., (...) => {...})
                  - pattern-not: $SERVER.prompt($NAME, "$DESC", (...) => {...})
""",
    """              # Prompts (registerPrompt, v1 prompt), with or without arguments.
              - pattern: $SERVER.registerPrompt($NAME, $CONFIG, (...) => {...})
              - pattern: $SERVER.prompt($NAME, ..., (...) => {...})
"""), (
    """                  - pattern-not: $SERVER.registerResource($NAME, "$FIXED", ...)
                  - pattern-not: $SERVER.resource($NAME, "$FIXED", ...)
""",
    "")]


def ts_shapes(path: Path, rewrites: list[tuple[str, str]]) -> str:
    items, _ = sibling_patterns(path, 0)
    text = items[0]
    for old, new in rewrites[:1]:
        text = rewrite(text, [(old, new)])
    text = rewrite(text, rewrites[1:])
    if "$ARGS" in text:
        raise SystemExit("gen_tool_returns_environment.py: $ARGS left in the TypeScript handler shapes")
    return reindent(text, 10)


def field_items(path: Path, field: str) -> list[str]:
    """The items of a sibling rule's top-level list `field` (pattern-sources,
    pattern-sanitizers), as text, checked against the parsed rule."""
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    items = list_items(lines, lines.index(f"    {field}:\n") + 1, 6)
    data = yaml.safe_load(text)["rules"][0][field]
    if yaml.safe_load(textwrap.dedent("".join(items))) != data:
        raise SystemExit(f"gen_tool_returns_environment.py: misread the {field} of {path.relative_to(ROOT)}")
    return items


def labeled(text: str, label: str = "ENV") -> str:
    """Give every top-level source item in `text` a label."""
    out = re.sub(r"(?m)^      - (patterns|pattern|pattern-either):", rf"      - label: {label}\n        \1:", text)
    if out.count(f"label: {label}") != len(re.findall(r"(?m)^      - ", text)):
        raise SystemExit("gen_tool_returns_environment.py: a source item has an unexpected first key")
    return out


ARG_INTRO = """\
      # The tool's arguments, unlabeled (__SOURCE__): only an environment lookup they name
      # (below) is reported, not an argument the tool echoes back. Copied from {sibling}, with
      # its allowlist sanitizers.
"""


def sources(sibling: Path, env_sources: str, dynamic: str) -> str:
    return ("    pattern-sources:\n" + ARG_INTRO.format(sibling=sibling.stem)
            + "".join(field_items(sibling, "pattern-sources"))
            + labeled(env_sources) + dynamic)


def sanitizers(sibling: Path, count: int, own: str) -> str:
    return ("    pattern-sanitizers:\n" + "".join(field_items(sibling, "pattern-sanitizers")[:count]) + own)


def sinks(text: str) -> str:
    """Every sink requires the ENV label."""
    out = text.replace("      - exact: true\n        patterns:\n",
                       "      - requires: ENV\n        exact: true\n        patterns:\n")
    if "requires: ENV" not in out:
        raise SystemExit("gen_tool_returns_environment.py: sink scaffolding changed")
    return out


# ---- regexes ---------------------------------------------------------------------------------

def not_secret(regex: str, shape: str) -> str:
    """A regex for a name of `shape` that `regex` (an ENV / ENV_ATTR name regex from
    gen_secret_in_system_prompt.py) doesn't count as a secret's."""
    head, _, rest = regex.split("\n", 2)
    if head != "(?x)" or not rest.startswith("(?!"):
        raise SystemExit("gen_tool_returns_environment.py: unexpected secret-name regex layout")
    return f"{head}\n{shape}\n(?!\n{rest}\n)"


# Upper-case names only, the way environment variables are written: a lower-case key
# (args["name"], input.name) is a tool argument or a field, not one variable of the environment.
ENV_KEY_OK = not_secret(ENV, "^ [\"'`] (?=[A-Z][A-Z0-9_]* [\"'`] $)")
ENV_ATTR_OK = not_secret(ENV_ATTR, "^ (?=[A-Z][A-Z0-9_]* $)")
ENV_ATTR_ANY_OK = not_secret(ENV_ATTR, "^ (?=[A-Za-z_$][\\w$]* $)")
# The command that prints the whole environment: env or printenv with no operands (a NUL
# separator or a pipe into sort still prints all of it; `printenv HOME` prints one).
PY_PRINTENV = r"""^["'](?:/usr)?(?:/bin/)?(?:env|printenv)(?:\s+(?:-0|--null))?(?:\s*\|\s*sort)?["']$"""
TS_PRINTENV = r"""^["'`](?:/usr)?(?:/bin/)?(?:env|printenv)(?:\s+(?:-0|--null))?(?:\s*\|\s*sort)?["'`]$"""
PROC_ENVIRON = r"""^[fF]?["'`]/proc/(?:self|\d+|[$]?\{[^}"'`]+\})/environ["'`]$"""
PY_RUN = (r"^(?:subprocess\.(?:run|check_output|getoutput|getstatusoutput|Popen|call)|os\.popen"
          r"|(?:asyncio\.)?create_subprocess_(?:exec|shell)|anyio\.(?:run_process|open_process))$")
TS_EXEC = r"^(?:[\w$]+\.)?(?:execSync|execFileSync|spawnSync|execa|execaSync|execAsync|execFileAsync)$"


# ---- Python ----------------------------------------------------------------------------------

OPTIONS = """    mode: taint
    options:
      # Only the propagators below carry the environment through a call: subprocess.run(env=env),
      # a client built from it, len(env), and bool(token) return clean values.
      taint_assume_safe_functions: true
      taint_assume_safe_booleans: true
      taint_assume_safe_numbers: true
"""

PY_ENV_SOURCES = """\
      # The whole environment as a value: os.environ returned, copied (dict(os.environ),
      # {**os.environ}, os.environ.copy()), serialized, or iterated for its items. A lookup, a
      # membership test, its length, and its keys alone are not its values.
      - patterns:
          - pattern-either:
              - pattern: os.environ
              - pattern: os.environb
          - pattern-not-inside: os.$ENV.$ATTR
          - pattern-not-inside: os.$ENV[$KEY]
          - pattern-not-inside: $KEY in os.$ENV
          - pattern-not-inside: $KEY not in os.$ENV
          - pattern-not-inside: len(os.$ENV)
          - pattern-not-inside: sorted(os.$ENV, ...)
          - pattern-not-inside: list(os.$ENV)
          - pattern-not-inside: set(os.$ENV)
          - pattern-not-inside: tuple(os.$ENV)
          - pattern-not-inside: |
              for $KEY in os.$ENV:
                ...
          - pattern-not-inside: '[$X for $KEY in os.$ENV]'
          - pattern-not-inside: '($X for $KEY in os.$ENV)'
      - patterns:
          - pattern: os.$ENV.$METHOD()
""" + mvr("$ENV", "^environb?$", 10) + mvr("$METHOD", "^(?:copy|items|values)$", 10) + """\
      # Every variable read back by name while iterating the names: {k: os.environ[k] for k in
      # sorted(os.environ)}, [f"{k}={os.getenv(k)}" for k in os.environ.keys()], filtered or not
      # (the filter sanitizers below decide whether a filter is enough).
      - patterns:
          - pattern-either:
              - pattern: '{$K: $V for $K in $XS}'
              - pattern: '[$V for $K in $XS]'
              - pattern: '($V for $K in $XS)'
              - pattern: '{$K: $V for $K in $XS if $C}'
              - pattern: '[$V for $K in $XS if $C]'
              - pattern: '($V for $K in $XS if $C)'
""" + paren_guard("$XS", 10) + """\
          - metavariable-pattern:
              metavariable: $XS
              patterns:
                - pattern-either:
                    - pattern: os.$ENV
                    - pattern: $FN(os.$ENV, ...)
                    - pattern: os.$ENV.keys()
                    - pattern: $FN(os.$ENV.keys(), ...)
""" + mvr("$ENV", "^environb?$", 16) + """\
          - metavariable-pattern:
              metavariable: $V
              pattern-either:
                - pattern: os.environ[$K]
                - pattern: os.environ.get($K, ...)
                - pattern: os.getenv($K, ...)
      # A parsed .env file (python-dotenv), or another process's environment (psutil).
      - pattern: dotenv.dotenv_values(...)
      - pattern: dotenv.main.dotenv_values(...)
      - pattern: psutil.Process(...).environ()
      - patterns:
          - pattern-inside: |
              $PROC = psutil.Process(...)
              ...
          - pattern: $PROC.environ()
      # A command that prints the whole environment: subprocess.run(["env"]),
      # check_output("printenv"), os.popen("env"), create_subprocess_exec("printenv", ...).
      - patterns:
          - pattern-either:
              - pattern: $RUN([$CMD], ...)
              - pattern: $RUN($CMD, ...)
          - pattern-not: $RUN($CMD, $OPERAND, ...)
""" + mvr("$RUN", PY_RUN, 10) + mvr("$CMD", PY_PRINTENV, 10, literal=True) + """\
      # The environment file of a process: open("/proc/self/environ"), Path(f"/proc/{pid}/environ").
      - patterns:
          - pattern-either:
              - pattern: open($PATH, ...)
              - pattern: pathlib.Path($PATH)
""" + mvr("$PATH", PROC_ENVIRON, 10, literal=True) + """\
      # One variable named like a secret: os.environ["GITHUB_TOKEN"], os.getenv("DB_PASSWORD").
      # The names are the ones secret-in-system-prompt treats as secrets.
      - patterns:
          - pattern-either:
              - pattern: os.environ[$NAME]
              - pattern: os.environ.get($NAME, ...)
              - pattern: os.getenv($NAME, ...)
              - pattern: decouple.config($NAME, ...)
""" + mvr("$NAME", ENV, 10, literal=True)

PY_DYNAMIC = """\
      # A variable the model names: os.environ.get(name), os.environ[name], os.getenv(name) with
      # a tool argument as the name, so a prompt injection can ask for AWS_SECRET_ACCESS_KEY.
      - label: ENV
        requires: __SOURCE__
        pattern-either:
          - pattern: os.environ.get($KEY, ...)
          - pattern: os.environ[$KEY]
          - pattern: os.getenv($KEY, ...)
          - pattern: decouple.config($KEY, ...)
      # A module-level snapshot (STARTUP_ENV = dict(os.environ)) used in a function or class
      # defined after it. With --taint-intrafile, OpenGrep drops module-level taint inside a
      # function the file never calls, so the name's later uses are sources too. The region
      # starts at the snapshot itself and runs to the end of its block: a region from any
      # assignment to each later def took 25 s on a module of 4,000 constants (OpenGrep 1.30.2).
      - label: ENV
        patterns:
          - pattern-either:
              - pattern-inside: |
                  $G = dict(os.environ, ...)
                  ...
              - pattern-inside: |
                  $G = dict(os.environb, ...)
                  ...
              - pattern-inside: |
                  $G = os.environ
                  ...
              - pattern-inside: |
                  $G = os.environb
                  ...
              - pattern-inside: |
                  $G = os.environ.copy()
                  ...
              - pattern-inside: |
                  $G = os.environb.copy()
                  ...
              - pattern-inside: |
                  $G = {**os.environ, ...}
                  ...
              - pattern-inside: |
                  $G = {**os.environb, ...}
                  ...
              - pattern-inside: |
                  $G = dotenv_values(...)
                  ...
              - pattern-inside: |
                  $G = dotenv.dotenv_values(...)
                  ...
          - pattern-either:
              - pattern-inside: |
                  def $FN(...):
                    ...
              - pattern-inside: |
                  async def $FN(...):
                    ...
              - pattern-inside: |
                  class $CLS:
                    ...
""" + mvr("$G", r"^[A-Z][A-Z0-9_]*$", 10) + """          - pattern: $G
          - pattern-not-inside: $G[$KEY]
          - pattern-not-inside: $G.get(...)
          - pattern-not-inside: $G.keys()
          - pattern-not-inside: $KEY in $G
          - pattern-not-inside: $KEY not in $G
          - pattern-not-inside: len($G)
          - pattern-not-inside: sorted($G, ...)
          - pattern-not-inside: list($G)
          - pattern-not-inside: $G = $VALUE
"""

# The constructors that build a tool result or a model: TextContent(text=...),
# CallToolResult(content=[...]), fastmcp's ToolResult, a pydantic model of the report. The
# environment handed to a process, client, or container (env=, api_key=, headers=) isn't
# returned.
PY_CTOR = r"^(?:[\w.]*\.)?[A-Z]\w*$"
PY_CTOR_KW = r"^(?!(?i:env|environ|environment|extra_env|.*(?:api_?key|token|secret|password|credentials?|headers|auth)\w*)$)"

# Encoding a value doesn't hide it: base64, hex, URL-quoting, or a case change is reversible.
PY_FN_NAMES = (r"dict|list|tuple|sorted|reversed|filter|str|repr|ascii|bytes|json\.dumps|pprint\.pformat"
               r"|yaml\.(?:safe_)?dump|toml\.dumps|tomli_w\.dumps|orjson\.dumps|ujson\.dumps|dataclasses\.asdict"
               r"|shlex\.join|shlex\.quote|base64\.(?:b64encode|urlsafe_b64encode|standard_b64encode|b32encode"
               r"|b16encode|b85encode|encodebytes)|binascii\.(?:hexlify|b2a_hex|b2a_base64)|codecs\.encode"
               r"|urllib\.parse\.(?:quote|quote_plus|urlencode)|html\.escape|zlib\.compress|gzip\.compress")
PY_METHOD_NAMES = (r"copy|items|values|decode|encode|strip|rstrip|lstrip|read|read_text|read_bytes|readlines"
                   r"|splitlines|split|replace|communicate|getvalue|model_dump|model_dump_json|to_dict|upper"
                   r"|lower|casefold|title|swapcase|removeprefix|removesuffix|hex|ljust|rjust|zfill")
PY_FN_PROP = rf"^(?:{PY_FN_NAMES})$"
PY_METHOD_PROP = rf"^(?:{PY_METHOD_NAMES})$"
# A comprehension whose element is some other call (redact(v), mask(k, v)): the comprehension
# takes its iterable's taint, so it needs clearing when the element doesn't carry it.
PY_OTHER_CALL = (rf"^(?!(?:{PY_FN_NAMES})$)(?![\w.]*\.(?:{PY_METHOD_NAMES}|join|format|format_map)$)"
                 r"(?![\w.]*\.?[A-Z]\w*$)")

PY_PROPAGATORS = """    pattern-propagators:
      # Copies, serializations, and text built from a value carry it: dict(env),
      # json.dumps(env), sorted(env.items()), "\\n".join(lines), out.decode(), pformat(env).
      - patterns:
          - pattern-either:
              - patterns:
                  - pattern: $FN($X, ...)
""" + mvr("$FN", PY_FN_PROP, 18) + """\
              - patterns:
                  - pattern: $X.$METHOD(...)
""" + mvr("$METHOD", PY_METHOD_PROP, 18) + """\
              - pattern: filter($F, $X)
              - pattern: $SEP.join($X)
              - pattern: $FMT.format(..., $X, ...)
              - pattern: $FMT.format(..., $KW=$X, ...)
              - pattern: $FMT.format_map($X)
              - patterns:
                  - pattern-either:
                      - pattern: $CTOR(..., $X, ...)
                      - patterns:
                          - pattern: $CTOR(..., $KW=$X, ...)
""" + mvr("$KW", PY_CTOR_KW, 26) + mvr("$CTOR", PY_CTOR, 18) + """\
                  - metavariable-comparison:
                      comparison: not re.match("^(?:[a-zA-Z0-9_.]*[.])?(?:Popen|Process|Thread|Timer|[A-Z][a-zA-Z0-9_]*(?:Client|Session|Connection|Engine|Pool|Executor|Runner))$", str($CTOR))
          - pattern: $CALL
""" + mvr("$CALL", r"(?s)^.+\)$", 10) + """\
        from: $X
        to: $CALL
      # A lookup keyed by a tool argument carries the argument to the lookup's value, where the
      # labeled source above turns it into the environment.
      - patterns:
          - pattern-either:
              - pattern: os.environ.get($X, ...)
              - pattern: os.getenv($X, ...)
              - pattern: decouple.config($X, ...)
          - pattern: $CALL
""" + mvr("$CALL", r"(?s)^.+\)$", 10) + """\
        from: $X
        to: $CALL
      # A mapping filled from it: report.update(os.environ), and env.get("GITHUB_TOKEN").
      - pattern: $DICT.update($X)
        from: $X
        to: $DICT
      - patterns:
          - pattern: $X.get($NAME, ...)
          - pattern: $CALL
""" + mvr("$NAME", ENV, 10, literal=True) + mvr("$CALL", r"(?s)^.+\)$", 10) + """\
        from: $X
        to: $CALL
"""

# ---- filters --------------------------------------------------------------------------------
# The condition's metavariables ($KEYNAME, $ALLOWED, ...) are named apart from the enclosing
# pattern's ($X, $K): a shared name inside metavariable-pattern must bind the same text.
# A filter or a masking conditional clears the environment only when it can't let a secret
# through: it keeps entries by exact name (k in SHOWN, k == "TZ"), or it drops or masks the
# entries named like secrets ("TOKEN" not in k, not SECRET_RE.search(k)). A prefix or any other
# filter (k.startswith("GITHUB_")) still keeps GITHUB_TOKEN, so it carries the environment.

def rx(var: str, regex: str) -> dict:
    return {"metavariable-regex": {"metavariable": var, "regex": regex}}


def mvp(var: str, body: dict) -> list:
    """A metavariable-pattern, after the guard against OpenGrep's crash on a parenthesized
    receiver (NOT_PAREN_RECEIVER in gen_mcp_unpinned.py); splice it into a patterns list."""
    return [rx(var, NOT_PAREN_RECEIVER), {"metavariable-pattern": {"metavariable": var, **body}}]


class NoAliases(yaml.SafeDumper):
    def ignore_aliases(self, data):  # OpenGrep's YAML reader rejects anchors and aliases
        return True


def ydump(items: list, n: int) -> str:
    return textwrap.indent(yaml.dump(items, Dumper=NoAliases, sort_keys=False, width=1000), " " * n)


# Text that names a secret: a literal ("TOKEN", ("_KEY", "_SECRET")), a regex, or a variable.
SECRET_TEXT = (r"(?is)^.*(?:key|token|secret|passw|pwd|auth|cred|private|session|cookie|signature|cert"
               r"|bearer|dsn|sensitive)")
# A predicate or a list that names secrets: is_secret(k), SENSITIVE_NAMES, REDACTED.
SECRET_FN = r"(?i)^(?:[\w$.]*\.)?[\w$]*(?:secret|sensitive|private|credential|redact|mask)[\w$]*$"
DENY_NAME = (r"(?i)^(?:[\w$.]*\.)?[\w$]*(?:secret|sensitive|deny|denied|block|redact|hidden|private|mask|exclu"
             r"|credential)[\w$]*$")
ALLOW_NAME = (r"(?i)^(?!(?:os\.environ|process\.env)\b)(?!(?:[\w$.]*\.)?[\w$]*(?:secret|sensitive|deny|denied"
              r"|block|redact|hidden|private|mask|exclu|credential))")
QUOTED = r"""^[rbuRBU]?["'`]"""
NOT_QUOTED = r"""^(?![rbuRBUfF]{0,2}["'`])"""
PY_MASK = r"""(?s)^(?:None|[rbuRBU]?(?:"[^"]*"|'[^']*')|(?:[\w.]*\.)?\w*(?:mask|redact|hide|obfuscate|censor)\w*\(.*\))$"""
TS_MASK = r"""(?s)^(?:null|undefined|"[^"]*"|'[^']*'|`[^`$]*`|(?:[\w$.]*\.)?[\w$]*(?:mask|redact|hide|obfuscate|censor)[\w$]*\(.*\))$"""

PY_SECRET_TEST = [
    {"patterns": [{"pattern-either": [{"pattern": "$LIT in $KEYNAME"}, {"pattern": "$LIT in $KEYNAME.$M()"}]},
                  rx("$LIT", QUOTED), rx("$LIT", SECRET_TEXT)]},
    {"patterns": [{"pattern-either": [{"pattern": "$KEYNAME.$TEST($ARG)"}, {"pattern": "$KEYNAME.$M().$TEST($ARG)"}]},
                  rx("$TEST", "^(?:startswith|endswith)$"), rx("$ARG", SECRET_TEXT)]},
    {"patterns": [{"pattern-either": [{"pattern": "re.$TEST($ARG, $KEYNAME, ...)"}, {"pattern": "$ARG.$TEST($KEYNAME, ...)"}]},
                  rx("$TEST", "^(?:search|match|fullmatch)$"), rx("$ARG", SECRET_TEXT)]},
    {"patterns": [{"pattern": "$F($KEYNAME, ...)"}, rx("$F", SECRET_FN)]},
    {"patterns": [{"pattern": "$KEYNAME in $DENY"}, rx("$DENY", DENY_NAME)]},
    {"patterns": [{"pattern-either": [{"pattern": "any($W in $KEYNAME for $W in $WORDS)"},
                                      {"pattern": "any($W in $KEYNAME.$M() for $W in $WORDS)"}]},
                  rx("$WORDS", SECRET_TEXT)]},
]
PY_KEEP = [
    {"patterns": [{"pattern": "$KEYNAME in $ALLOWED"}, rx("$KEYNAME", NOT_QUOTED), rx("$ALLOWED", ALLOW_NAME)]},
    {"patterns": [{"pattern-either": [{"pattern": "$KEYNAME == $LIT"}, {"pattern": "$LIT == $KEYNAME"}]}, rx("$LIT", QUOTED)]},
]
PY_DROP = [
    {"patterns": [{"pattern": "not $Q"}, *mvp("$Q", {"pattern-either": PY_SECRET_TEST})]},
    {"patterns": [{"pattern-either": [{"pattern": "$LIT not in $KEYNAME"}, {"pattern": "$LIT not in $KEYNAME.$M()"}]},
                  rx("$LIT", QUOTED), rx("$LIT", SECRET_TEXT)]},
    {"patterns": [{"pattern": "$KEYNAME not in $DENY"}, rx("$DENY", DENY_NAME)]},
]
TS_SECRET_TEST = [
    {"patterns": [{"pattern-either": [{"pattern": "$KEYNAME.$TEST($ARG)"}, {"pattern": "$KEYNAME.$M().$TEST($ARG)"}]},
                  rx("$TEST", "^(?:includes|startsWith|endsWith|match|search)$"), rx("$ARG", SECRET_TEXT)]},
    {"patterns": [{"pattern": "$RE.test($KEYNAME)"}, rx("$RE", SECRET_TEXT)]},
    {"patterns": [{"pattern": "$F($KEYNAME, ...)"}, rx("$F", SECRET_FN)]},
    {"patterns": [{"pattern-either": [{"pattern": "$DENY.has($KEYNAME)"}, {"pattern": "$DENY.includes($KEYNAME)"}]},
                  rx("$DENY", DENY_NAME)]},
    {"patterns": [{"pattern": "$WORDS.some(...)"}, rx("$WORDS", SECRET_TEXT)]},
]
TS_KEEP = [
    {"patterns": [{"pattern-either": [{"pattern": "$ALLOWED.has($KEYNAME)"}, {"pattern": "$ALLOWED.includes($KEYNAME)"}]},
                  rx("$KEYNAME", NOT_QUOTED), rx("$ALLOWED", ALLOW_NAME)]},
    {"patterns": [{"pattern-either": [{"pattern": "$KEYNAME === $LIT"}, {"pattern": "$LIT === $KEYNAME"},
                                      {"pattern": "$KEYNAME == $LIT"}, {"pattern": "$LIT == $KEYNAME"}]}, rx("$LIT", QUOTED)]},
]
TS_DROP = [{"patterns": [{"pattern": "!$Q"}, *mvp("$Q", {"pattern-either": TS_SECRET_TEST})]}]


def safe_condition(keep: list, drop: list, negate: str, either: str) -> dict:
    """A condition true only for entries that are safe to keep (not under an `or`)."""
    return {"pattern-either": [
        {"patterns": [{"pattern-either": keep}, {"pattern-not-inside": either}, {"pattern-not-inside": negate}]},
        {"patterns": [{"pattern-either": drop}, {"pattern-not-inside": either}]},
    ]}


def secret_condition(tests: list, negate: str, both: str) -> dict:
    """A condition true for every entry named like a secret (an `or` of tests is fine)."""
    return {"patterns": [{"pattern-either": tests}, {"pattern-not-inside": negate}, {"pattern-not-inside": both}]}


PY_SAFE = safe_condition(PY_KEEP, PY_DROP, "not $Z", "$Y or $Z")
PY_SECRET = secret_condition(PY_SECRET_TEST, "not $Z", "$Y and $Z")
TS_SAFE = safe_condition(TS_KEEP, TS_DROP, "!$Z", "$Y || $Z")
TS_SECRET = secret_condition(TS_SECRET_TEST, "!$Z", "$Y && $Z")


def masked(positive: dict, cond: str, keep: str, mask: str, mask_re: str, safe: dict, secret: dict) -> list:
    """`<mask> if <secret test> else v`, or `v if <safe test> else <mask>`, as two pattern
    lists after `positive` (cond, keep, and mask name the conditional's test, its first
    branch, and its second branch)."""
    return [[positive, rx(keep, mask_re), *mvp(cond, secret)],
            [positive, rx(mask, mask_re), *mvp(cond, safe)]]


PY_FILTERS = """\
      # A comprehension or filter() that keeps entries only by exact name or drops the ones named
      # like secrets: {k: v for k, v in os.environ.items() if k in SHOWN}, if "TOKEN" not in k.
      # A prefix filter (k.startswith("GITHUB_")) or any other condition still keeps
      # GITHUB_TOKEN, so the comprehension keeps the environment's taint. Not exact: a propagator's
      # $CALL can be any call around os.environ.items(), so the environment inside is cleared too.
""" + ydump([{"patterns": [
    {"pattern-either": [{"pattern": "{$K: $V for $T in $XS if $C}"}, {"pattern": "[$V for $T in $XS if $C]"},
                        {"pattern": "($V for $T in $XS if $C)"}, {"pattern": "filter(lambda $T: $C, $XS)"}]},
    *mvp("$C", PY_SAFE)]}], 6) + """\
      # A comprehension that masks the values named like secrets ("***" if "TOKEN" in k else v)
      # or keeps only the exact names (v if k in SHOWN else None).
""" + ydump([{"patterns": branch} for branch in masked(
    {"pattern-either": [{"pattern": "{$K: $A if $C else $B for $T in $XS}"},
                        {"pattern": "[$A if $C else $B for $T in $XS]"},
                        {"pattern": "($A if $C else $B for $T in $XS)"}]},
    "$C", "$A", "$B", PY_MASK, PY_SAFE, PY_SECRET)], 6)

TS_FILTERS = """\
      # filter, find, or findLast with a callback that keeps entries only by exact name or drops
      # the ones named like secrets: .filter(([k]) => SHOWN.has(k)), (([k]) => !/token/i.test(k)).
      # A prefix filter (k.startsWith("GITHUB_")) or any other callback still keeps
      # GITHUB_TOKEN, so its result keeps the environment's taint. Not exact: the propagator
      # above carries process.env straight to the outermost call, so the environment inside
      # the filtered call is cleared too.
""" + ydump([{"patterns": [
    {"pattern-either": [{"pattern": "$X.$METHOD((...) => $C)"},
                        {"pattern": "$X.$METHOD((...) => {\n  ...\n  return $C;\n})"},
                        {"pattern": "$X.$METHOD(function (...) {\n  ...\n  return $C;\n})"}]},
    rx("$METHOD", "^(?:filter|find|findLast)$"),
    *mvp("$C", TS_SAFE)]}], 6) + """\
      # The same allowlist through a type assertion, .filter(([k]) => (SHOWN as readonly
      # string[]).includes(k)), matched here because the guard above skips a callback that
      # starts with a parenthesized expression.
""" + ydump([{"patterns": [
    {"pattern-either": [{"pattern": f"$X.$METHOD((...) => ($ALLOWED as $T).{m}($KEYNAME))"} for m in ("includes", "has")]},
    rx("$METHOD", "^(?:filter|find|findLast)$"),
    rx("$KEYNAME", NOT_QUOTED), rx("$ALLOWED", ALLOW_NAME)]}], 6) + """\
      # map or flatMap with a callback that masks the values named like secrets:
      # .map(([k, v]) => [k, /token|secret/i.test(k) ? "***" : v]).
""" + ydump([{"patterns": [
    {"pattern": "$X.$METHOD((...) => $BODY)"},
    rx("$METHOD", "^(?:map|flatMap)$"),
    *mvp("$BODY", {"pattern-either": [{"patterns": branch} for branch in masked(
        {"pattern": "$C ? $A : $B"}, "$C", "$A", "$B", TS_MASK, TS_SAFE, TS_SECRET)]})]}], 6)

PY_SANITIZERS = """\
      # One variable read by a literal name that isn't a secret's: env["TZ"]. A name the caller
      # chooses (env[name]) or a secret's name (env["GITHUB_TOKEN"]) stays tainted.
      - exact: true
        patterns:
          - pattern: $MAP[$KEY]
""" + mvr("$KEY", ENV_KEY_OK, 10, literal=True) + """\
      # Facts about the environment rather than its values.
      - exact: true
        pattern-either:
          - pattern: $A == $B
          - pattern: $A != $B
          - pattern: $A is $B
          - pattern: $A is not $B
          # Only a literal name: `name in ALLOWED` is the allowlist sanitizer above, and an
          # exact sanitizer on the same test would hide it.
          - pattern: '"$NAME" in $B'
          - pattern: '"$NAME" not in $B'
          # OpenGrep carries taint through len() even with taint_assume_safe_functions.
          - pattern: len($X)
          - pattern: bool($X)
"""  + PY_FILTERS + """\
      - exact: true
        patterns:
          - pattern-either:
              - pattern: '[$F(...) for $T in $XS]'
              - pattern: '($F(...) for $T in $XS)'
              - pattern: '{$K: $F(...) for $T in $XS}'
""" + mvr("$F", PY_OTHER_CALL, 10) + """\
      # len() and bool() are operators to OpenGrep, so $F(...) doesn't match them.
      - exact: true
        pattern-either:
          - pattern: '[len($X) for $T in $XS]'
          - pattern: '(len($X) for $T in $XS)'
          - pattern: '{$K: len($X) for $T in $XS}'
          - pattern: '[bool($X) for $T in $XS]'
          - pattern: '(bool($X) for $T in $XS)'
          - pattern: '{$K: bool($X) for $T in $XS}'
"""

PY_MCP_SINKS_HEAD = """    pattern-sinks:
      # What an MCP tool, resource, or prompt function returns: the SDKs serialize it into the
      # tool result, resource contents, or prompt messages the client hands the model (MCPServer
      # and FastMCP convert any value with pydantic_core.to_json, falling back to str(), so a bare
      # os.environ goes out whole). The registration shapes are mcp-tool-arg-to-shell's sources.
      - exact: true
        patterns:
"""
# The value a handler returns. A Python slice in it (json.dumps(env)[:4000]) is invisible to
# OpenGrep 1.30.2's taint engine: no taint flows into or out of out[:4000], even into a sink
# around it, so a truncated dump is a miss and a preview (token[:4]) needs no sanitizer.
PY_RETURN_VALUE = """          - pattern: return $E
          - focus-metavariable: $E
"""
RETURN = """          - pattern-inside: |
              def $F(...): ...
""" + PY_RETURN_VALUE
PY_MCP_SINKS_LOWLEVEL = """      # v2 low-level Server: the CallToolResult of the on_call_tool handler.
      - exact: true
        patterns:
"""
PLAIN_RETURN = PY_RETURN_VALUE
# An arrow function's expression body is a return too, so a callback inside the handler
# (entries.map(([k, v]) => `${k}=${v}`)) would be one; only the handler's own return counts.
# The callback methods are named: an imported function resolves to a dotted name, so a bare
# $X.$METHOD(...) also matches LangChain.js tool(async () => ...), the handler itself.
TS_RETURN = """          - pattern: return $E
          - pattern-not-inside:
              patterns:
                - pattern: $X.$METHOD((...) => {...}, ...)
""" + mvr("$METHOD", r"^(?:map|flatMap|filter|forEach|reduce|reduceRight|some|every|find|findIndex|findLast|findLastIndex|sort|toSorted|then|catch|finally|replace|replaceAll)$", 16) + """\
          - focus-metavariable: $E
"""

PY_AGENT_SINKS_HEAD = """    pattern-sinks:
      # What an agent tool function returns: the framework turns it into the tool message the
      # model reads next (LangChain ToolMessage content, the OpenAI Agents SDK's str() of the
      # result, pydantic-ai and CrewAI tool returns). The registration shapes are
      # agent-tool-arg-to-shell's sources.
      - exact: true
        patterns:
"""

MESSAGE = """    message: >-
      {who} returns the process environment to the model: the whole environment ({whole}) or
      a variable named like a secret. What it returns goes into the model's context and the
      {where}, so every API key, token, and connection string the {proc} was started with can be
      repeated in a reply, written into another tool call, or sent somewhere by a prompt
      injection in anything the model reads, and it stays in provider and tracing logs. Return
      only the non-secret settings the tool needs, read by name ({fix}), or say whether a
      secret is set rather than what it is.
"""

PY_WHOLE = "os.environ, a dotenv file, `env` or `printenv` output"
PY_FIX = '`{"tz": os.environ.get("TZ")}`'
TS_WHOLE = "process.env, a parsed .env file, `env` or `printenv` output"
TS_FIX = "`{ tz: process.env.TZ }`"


def metadata(mcp: bool, technology: str, refs: str) -> str:
    owasp = """      owasp-llm:
        - "LLM02:2026 - Sensitive Information Disclosure"
        - "LLM02:2025 - Sensitive Information Disclosure"
"""
    if mcp:
        owasp += """      owasp-mcp:
        - "MCP10:2025 - Context Injection & Over-Sharing"
        - "MCP01:2025 - Token Mismanagement & Secret Exposure"
"""
    return f"""    metadata:
      category: security
      subcategory: [vuln]
      pack-category: {"mcp-server" if mcp else "ai-code"}
{owasp}      owasp-aisvs:
        - "v1.01-C9.5.4 - Agent Authorization, Delegation, and Continuous Enforcement"
      mitre-atlas:
        - "AML.T0055 - Unsecured Credentials"
        - "AML.T0057 - LLM Data Leakage"
      cwe:
        - "CWE-526: Cleartext Storage of Sensitive Information in an Environment Variable"
        - "CWE-200: Exposure of Sensitive Information to an Unauthorized Actor"
      confidence: HIGH
      likelihood: MEDIUM
      impact: HIGH
      technology: [{technology}]
      references:
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/7e144e05142b2105faa1603178a1163a2a34df24/2026/final/LLM02_SensitiveInformationDisclosure.md
{refs}        - https://cwe.mitre.org/data/definitions/526.html
"""


MCP_OWASP_REFS = """        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP10-2025%E2%80%93ContextInjection%26OverSharing.md
        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP01-2025-Token-Mismanagement-and-Secret-Exposure.md
"""

HEADER = """# Generated by scripts/gen_tool_returns_environment.py from {sibling} (the tool handler
# shapes) and gen_secret_in_system_prompt.py (secret names). Edit those, or the script, not this file.
rules:
  - id: {id}
"""


def header(rule_id: str, sibling: Path, comment: str, language: str) -> str:
    return (HEADER.format(sibling=sibling.stem, id=rule_id)
            + textwrap.indent(comment.strip("\n"), "    # ") + "\n"
            + f"    languages: {language}\n    severity: ERROR\n")


def py_mcp_rule() -> str:
    shapes, lowlevel = py_mcp_shapes()
    return (header("mcp-tool-returns-environment", PY_MCP_SIBLING, PY_MCP_COMMENT, "[python]")
            + MESSAGE.format(who="An MCP tool, resource, or prompt handler", whole=PY_WHOLE, where="client's transcript",
                             proc="server", fix=PY_FIX)
            + OPTIONS + sources(PY_MCP_SIBLING, PY_ENV_SOURCES, PY_DYNAMIC) + PY_PROPAGATORS
            + sanitizers(PY_MCP_SIBLING, 2, PY_SANITIZERS)
            + sinks(PY_MCP_SINKS_HEAD + shapes + RETURN + PY_MCP_SINKS_LOWLEVEL + lowlevel + PLAIN_RETURN)
            + metadata(True, "mcp, fastmcp, claude-agent-sdk", MCP_OWASP_REFS
                       + "        - https://github.com/modelcontextprotocol/python-sdk/blob/v2.3.0/src/mcp/server/mcpserver/utilities/func_metadata.py\n"
                       "        - https://github.com/modelcontextprotocol/python-sdk/blob/v1.30.0/src/mcp/server/fastmcp/utilities/func_metadata.py\n"
                       "        - https://github.com/modelcontextprotocol/python-sdk/blob/v2.3.0/src/mcp/server/lowlevel/server.py\n"
                       "        - https://github.com/PrefectHQ/fastmcp/blob/v4.1.3/fastmcp_slim/fastmcp/server/server.py\n"))


def py_agent_rule() -> str:
    return (header("agent-tool-returns-environment", PY_AGENT_SIBLING, PY_AGENT_COMMENT, "[python]")
            + MESSAGE.format(who="An agent tool", whole=PY_WHOLE, where="run's transcript",
                             proc="agent", fix=PY_FIX)
            + OPTIONS + sources(PY_AGENT_SIBLING, PY_ENV_SOURCES, PY_DYNAMIC) + PY_PROPAGATORS
            + sanitizers(PY_AGENT_SIBLING, 2, PY_SANITIZERS)
            + sinks(PY_AGENT_SINKS_HEAD + py_agent_shapes() + RETURN)
            + metadata(False, "langchain, crewai, openai-agents, pydantic-ai",
                       "        - https://github.com/langchain-ai/langchain/blob/langchain-core%3D%3D1.6.13/libs/core/langchain_core/tools/base.py\n"
                       "        - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/tool.py\n"
                       "        - https://github.com/pydantic/pydantic-ai/blob/v2.59.0/pydantic_ai_slim/pydantic_ai/toolsets/function.py\n"
                       "        - https://github.com/crewAIInc/crewAI/blob/1.15.28/lib/crewai/src/crewai/tools/base_tool.py\n"))


PY_MCP_COMMENT = """MCP tool, resource, and prompt handlers that return the environment. Handler shapes:
mcp-tool-arg-to-shell (MCP Python SDK v2.3.0 MCPServer and low-level Server(on_call_tool=...,
on_read_resource=..., on_get_prompt=...), v1.30.0 FastMCP and @server.call_tool() /
read_resource() / get_prompt(), fastmcp 4.1.3 @mcp.tool / resource / prompt, the standalone
decorators, add_tool / add_prompt / add_template, Claude Agent SDK @tool); the SDKs pass a
handler's return value to the client as the tool result, resource contents, or prompt
messages. Agent-framework tools are agent-tool-returns-environment."""

PY_AGENT_COMMENT = """Agent-framework sibling of mcp-tool-returns-environment: the same sources, propagators, and
sanitizers, with agent-tool-arg-to-shell's tool shapes (langchain-core 1.6.13 @tool and
BaseTool._run, openai-agents 0.24.0 @function_tool, pydantic-ai 2.59.0 @agent.tool /
tool_plain, crewai 1.15.28 @tool), whose return value becomes the tool message the model reads."""


# ---- TypeScript ------------------------------------------------------------------------------

TS_ENV_SOURCES = """\
      # The whole environment as a value: process.env returned, spread ({...process.env}),
      # serialized, or listed with Object.entries. A lookup (process.env.HOME), a membership
      # test, and Object.keys alone are not its values.
      - patterns:
          - pattern-either:
              - pattern: process.env
              - pattern: Bun.env
          - pattern-not-inside: $RT.env.$KEY
          - pattern-not-inside: $RT.env[$KEY]
          - pattern-not-inside: $KEY in $RT.env
      - pattern: Deno.env.toObject()
      # A parsed .env file: dotenv.config() (its .parsed), dotenv.parse(text).
      - patterns:
          - pattern-either:
              - pattern: dotenv.config(...)
              - pattern: dotenv.parse(...)
              - patterns:
                  - pattern-inside: |
                      import { $FN } from "dotenv";
                      ...
                  - pattern: $FN(...)
""" + mvr("$FN", "^(?:config|parse)$", 18) + """\
      # A command that prints the whole environment: execSync("env"), execFileSync("printenv"),
      # spawnSync("env"), execa("printenv").
      - patterns:
          - pattern-either:
              - pattern: $EXEC($CMD)
              - pattern: '$EXEC($CMD, {...})'
              - pattern: $EXEC($CMD, [], ...)
""" + mvr("$EXEC", TS_EXEC, 10) + mvr("$CMD", TS_PRINTENV, 10, literal=True) + """\
      # The environment file of a process: readFileSync("/proc/self/environ").
      - patterns:
          - pattern: $READ($PATH, ...)
""" + mvr("$PATH", PROC_ENVIRON, 10, literal=True) + """\
      # One variable named like a secret: process.env.GITHUB_TOKEN, process.env["DB_PASSWORD"].
      # The names are the ones secret-in-system-prompt-ts treats as secrets.
      - patterns:
          - pattern: $RT.env.$NAME
""" + mvr("$RT", "^(?:process|Bun)$", 10) + mvr("$NAME", ENV_ATTR, 10, literal=True) + """\
      - patterns:
          - pattern: $RT.env[$NAME]
""" + mvr("$RT", "^(?:process|Bun)$", 10) + mvr("$NAME", ENV, 10, literal=True)

TS_DYNAMIC = """\
      # A variable the model names: process.env[name] with a tool argument as the name, so a
      # prompt injection can ask for AWS_SECRET_ACCESS_KEY.
      - label: ENV
        requires: __SOURCE__
        patterns:
          - pattern: $RT.env[$KEY]
""" + mvr("$RT", "^(?:process|Bun)$", 10)

# In TypeScript a propagator's `to: $CALL` can be any call around the matched one: OpenGrep
# taints redact(Object.entries(process.env)) and Object.fromEntries(entries.filter(...)) through
# the inner match, and that is also how nested propagators compose
# (JSON.stringify(Object.assign({}, process.env))). So one propagator holds every shape, and the
# regex requires $CALL to be built only from these calls and methods around a parenthesis-free
# value: anything else in between (a redact() call, a .filter()) leaves the result clean.
TS_FUNCTIONS = ["JSON.stringify($X, ...)", "Object.entries($X)", "Object.values($X)",
                "Object.fromEntries($X)", "Object.assign($T, ..., $X, ...)", "structuredClone($X, ...)",
                "String($X)", "util.inspect($X, ...)", "util.format(..., $X, ...)", "$DEC.decode($X, ...)",
                "Buffer.from($X, ...)", "btoa($X)", "encodeURIComponent($X)", "encodeURI($X)",
                "querystring.stringify($X, ...)"]
TS_CALLEES = (r"JSON\.stringify|Object\.(?:entries|values|fromEntries|assign)|structuredClone|String"
              r"|util\.(?:inspect|format)|[\w$.]+\.decode|Buffer\.from|btoa|encodeURIComponent|encodeURI"
              r"|querystring\.stringify")
# filter, find, and findLast carry the entries they keep; the filter sanitizers below clear the
# whole call, the environment inside it included, when the callback can't keep a secret.
TS_METHODS = (r"map|flatMap|filter|find|findLast|join|sort|toSorted|reverse|flat|concat|toString|trim|trimEnd"
              r"|trimStart|split|replace|replaceAll|toUpperCase|toLowerCase|padStart|padEnd|normalize|at"
              r"|slice|substring|substr")
TS_BUILT = (r"""(?sx)
^ (?(DEFINE)
    (?<bal> (?: [^()] | \( (?&bal) \) )* )
    (?<built>
      (?: (?:CALLEES) \( (?: [^()]*? , \s* )? (?&built) (?: \s* , (?&bal) )? \)
        | [^()]* )
      (?: \. (?! (?:slice|substring|substr) \( \s* (?: 0 \s* , \s* )? -? [0-9] \s* \) )
          (?:METHODS) \( (?&bal) \) )* ) )
# A short preview (token.slice(0, 4), key.slice(-4)) ends the chain.
# A call, not a bare name inside one: binding $CALL to `JSON` or `process` taints the global.
(?= .* \) $ ) (?&built) $""").replace("CALLEES", TS_CALLEES).replace("METHODS", TS_METHODS)


def ts_propagators() -> str:
    shapes = "".join(f"              - pattern: {p}\n" for p in TS_FUNCTIONS)
    return """    pattern-propagators:
      # Copies, serializations, and text built from a value carry it: JSON.stringify(env),
      # Object.entries(env).map(...).join("\\n"), structuredClone(env), out.toString().
      - patterns:
          - pattern-either:
""" + shapes + """              - patterns:
                  - pattern: $X.$METHOD(...)
""" + mvr("$METHOD", rf"^(?:{TS_METHODS})$", 18) + """\
          - pattern: $CALL
""" + mvr("$CALL", TS_BUILT, 10, literal=True) + """        from: $X
        to: $CALL
"""  + """\
      - pattern: Object.assign($T, ..., $X, ...)
        from: $X
        to: $T
"""


TS_HOLDERS = r"^(?!(?:env|parsed|stdout|output|environment|variables|vars)$)"

TS_SANITIZERS = """\
      # One variable read by a name that isn't a secret's: env.HOME, env["TZ"]. A name the
      # caller chooses (env[name]) or a secret's name (env.GITHUB_TOKEN) stays tainted, and so
      # do the members that hold the environment itself (dotenv's .parsed, a command's .stdout).
      - exact: true
        patterns:
          - pattern: $MAP.$KEY
""" + mvr("$KEY", TS_HOLDERS, 10) + mvr("$KEY", ENV_ATTR_OK, 10, literal=True) + """\
      # Any non-secret name read straight from process.env (a lower-case npm_config_* or
      # http_proxy too): once process.env is a source anywhere in a file, OpenGrep treats every
      # later process.env.<name> read, in any function, as part of it.
      - exact: true
        patterns:
          - pattern: $RT.env.$KEY
""" + mvr("$RT", "^(?:process|Bun)$", 10) + mvr("$KEY", ENV_ATTR_ANY_OK, 10, literal=True) + """\
      - exact: true
        patterns:
          - pattern: $MAP[$KEY]
""" + mvr("$KEY", ENV_KEY_OK, 10, literal=True) + """\
      # A method that answers a question about the entries: some, every, findIndex. (OpenGrep
      # carries a receiver's taint into any method's result.) filter, find, and findLast are
      # below: their result is entries.
      - exact: true
        patterns:
          - pattern: $X.$METHOD(...)
""" + mvr("$METHOD", r"^(?:some|every|indexOf|lastIndexOf|findIndex|findLastIndex|hasOwnProperty|startsWith|endsWith|localeCompare)$", 10) + """\
      # Facts about the environment rather than its values.
      - exact: true
        pattern-either:
          - pattern: $A === $B
          - pattern: $A !== $B
          - pattern: $A == $B
          - pattern: $A != $B
          - pattern: $A in $B
""" + TS_FILTERS

TS_MCP_SINKS_HEAD = """    pattern-sinks:
      # What an MCP tool, resource, or prompt handler returns (an expression body counts as a
      # return): the tool result, resource contents, or prompt messages the client hands the
      # model. The registration shapes are mcp-tool-arg-to-shell-ts's sources, for handlers with
      # or without parameters.
      - exact: true
        patterns:
"""
TS_AGENT_SINKS_HEAD = """    pattern-sinks:
      # What an agent tool's execute function returns (an expression body counts as a return):
      # the tool result the model reads next. The registration shapes are
      # agent-tool-arg-to-shell-ts's sources, for functions with or without parameters.
      - exact: true
        patterns:
"""

TS_MCP_COMMENT = """JavaScript/TypeScript twin of mcp-tool-returns-environment. Handler shapes:
mcp-tool-arg-to-shell-ts (MCP TypeScript SDK v2.3.1 @modelcontextprotocol/server registerTool,
registerResource, registerPrompt, and setRequestHandler("tools/call" | "resources/read" |
"prompts/get"), 1.32.1 the same plus the tool() / resource() / prompt() overloads and the
request schemas, punkpeye fastmcp addTool / addResourceTemplate / addPrompt, Claude Agent SDK
tool()), with every prompt and resource handler (fixed URIs and argument-less prompts too); a v2
handler for a tool without inputSchema takes only the context (checked in v2.4.0 too). A named
handler for a resource at a fixed URI string isn't a sink."""

TS_AGENT_COMMENT = """JavaScript/TypeScript twin of agent-tool-returns-environment, with agent-tool-arg-to-shell-ts's
tool shapes (Vercel AI SDK ai 7.0.150 tool({ execute }) and dynamicTool, OpenAI Agents JS 0.21.0
tool({ execute }), LangChain.js @langchain/core 1.3.0 tool(fn), DynamicStructuredTool and
StructuredTool._call)."""


def ts_mcp_rule() -> str:
    return (header("mcp-tool-returns-environment-ts", TS_MCP_SIBLING, TS_MCP_COMMENT, "[typescript, javascript]")
            + MESSAGE.format(who="An MCP tool, resource, or prompt handler", whole=TS_WHOLE, where="client's transcript",
                             proc="server", fix=TS_FIX)
            + OPTIONS + sources(TS_MCP_SIBLING, TS_ENV_SOURCES, TS_DYNAMIC) + ts_propagators()
            + sanitizers(TS_MCP_SIBLING, 3, TS_SANITIZERS)
            + sinks(TS_MCP_SINKS_HEAD + ts_shapes(TS_MCP_SIBLING, TS_MCP_REWRITES) + TS_RETURN)
            + metadata(True, "mcp, fastmcp, claude-agent-sdk", MCP_OWASP_REFS
                       + "        - https://github.com/modelcontextprotocol/typescript-sdk/blob/v2.3.1/packages/server/src/server/mcp.ts\n"
                       "        - https://github.com/modelcontextprotocol/typescript-sdk/blob/v2.4.0/packages/server/src/server/mcp.ts\n"
                       "        - https://github.com/modelcontextprotocol/typescript-sdk/blob/1.32.1/src/server/mcp.ts\n"
                       "        - https://github.com/punkpeye/fastmcp/blob/v4.23.5/src/FastMCP.ts\n"))


def ts_agent_rule() -> str:
    return (header("agent-tool-returns-environment-ts", TS_AGENT_SIBLING, TS_AGENT_COMMENT, "[typescript, javascript]")
            + MESSAGE.format(who="An agent tool", whole=TS_WHOLE, where="run's transcript",
                             proc="agent", fix=TS_FIX)
            + OPTIONS + sources(TS_AGENT_SIBLING, TS_ENV_SOURCES, TS_DYNAMIC) + ts_propagators()
            + sanitizers(TS_AGENT_SIBLING, 3, TS_SANITIZERS)
            + sinks(TS_AGENT_SINKS_HEAD + ts_shapes(TS_AGENT_SIBLING, TS_ARGS) + TS_RETURN)
            + metadata(False, "vercel-ai-sdk, openai-agents, langchain",
                       "        - https://github.com/vercel/ai/blob/ai%407.0.150/packages/provider-utils/src/types/tool.ts\n"
                       "        - https://github.com/openai/openai-agents-js/blob/v0.21.0/packages/agents-core/src/tool.ts\n"
                       "        - https://github.com/langchain-ai/langchainjs/blob/%40langchain/core%401.3.0/libs/langchain-core/src/tools/index.ts\n"))


def render() -> dict[Path, str]:
    """The rule files and the content this script generates for each."""
    out = {PY_MCP_RULE: py_mcp_rule(), PY_AGENT_RULE: py_agent_rule(),
           TS_MCP_RULE: ts_mcp_rule(), TS_AGENT_RULE: ts_agent_rule()}
    for path, text in out.items():
        yaml.safe_load(text)  # fail here, not in OpenGrep, on a scaffolding mistake
    return out


def main() -> int:
    for path, content in render().items():
        if not path.exists() or path.read_text() != content:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
