#!/usr/bin/env python3
"""Generate the mcp-config-unpinned-package rule files from one set of regexes.

The JSON (most MCP clients), YAML (Continue), TOML (Codex), VS Code workspace-file and Claude
Code subagent front matter rules judge pins with the same runner and spec regexes. Those regexes are written once here, in a format-agnostic form:
elements may be "double", 'single' or plain (YAML) scalars, separated by "," or a YAML "- "
bullet, with //, /* */ or # comments between them. Only the scaffolding that finds a server's
command and args differs per format.

The path, scope, TOML, JSONC and subagent front matter scaffolding constants below also feed
gen_mcp_plaintext_secret.py, gen_mcp_remote_host.py and gen_mcp_hidden_path.py, so every MCP
config family scans the same files and servers.

Edit this script, not the rule files. scripts/build.py regenerates them, and
scripts/build.py --check fails when a rule file differs from what this script produces.

Usage:
    python3 scripts/gen_mcp_unpinned.py    # rewrite the rule files
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULE_DIR = ROOT / "rules" / "agent-config" / "supply-chain"

G = r'''
  # Shared tokens. An element is a "double", 'single' or plain (YAML) scalar; elements are
  # separated by , or a YAML "- " bullet, with //, /* */ or # comments in between.
  (?<sep> (?: \s | //[^\n]* | /\*(?:(?!\*/).)*\*/ | \#[^\n]* )*+ )
  (?<nx> (?&sep) (?: , | -(?=\s) ) (?&sep) )
  (?<o> ["']?+ )
  (?<c> ["'] | (?= [ \t]*+ (?:[,\]\r\n]|\z) | [ \t]+\# ) )
  (?<el> "(?:[^"\\]|\\.)*+" | '(?:[^']|'')*+'
    | (?!["'\[\]{},\#\s]) [^\r\n,\]]*? (?= [ \t]*+ (?:[,\]\r\n]|\z) | [ \t]+\# ) )'''.strip("\n")

START = r'''^ (?: \[ (?&sep) | -(?=\s) (?&sep) )'''

PY_UNPINNED = r'''
  # A requirement with no version, @latest, a range, or a wildcard; a git source not at a
  # commit SHA. Local paths and archive URLs are left alone.
  (?<unpinned> (?! [./~$%\\] | [A-Za-z]: | file: | https?: | - )
    (?: git\+[a-z]+:// (?:[^"'\s,\]@/]*@)?+ [^"'\s,\]@]*+
          (?: @(?![0-9a-fA-F]{7,40}(?:\#[^"'\s,\]]*)?(?&c)) [^"'\s,\]]* )?
      | [A-Za-z0-9][\w.-]* (?:\[[^\]"'\s]*\])? [ \t]*
          (?: @latest | (?:>=|<=|~=|!=|>|<)[^"'\r\n\]]* | ==[^"'\r\n\]=]*\*[^"'\r\n\]]* )? ) )'''.strip("\n")

NPM = rf'''(?sx)
(?(DEFINE)
{G}
  (?<exact> =?v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.+-]*)? )
  # Options that take the next element as their value (npm 11).
  (?<valopt> (?: -w|--workspace|--registry|--cache|--userconfig|--prefix|--loglevel
    |--node-options|--script-shell ) (?![\w-]) )
  # -p/--package name the package; -c/--call make the positionals a command.
  (?<srcopt> (?=(?&o)(?:-p|--package|-c|--call)(?&c)) (?&el) (?&nx) (?&el)
    | (?=(?&o)--(?:package|call)=) (?&el) )
  # Any other option, with its value. --before (resolve as of a date) is never consumed, so
  # the scans below stop at it.
  (?<opt> (?=(?&o)(?&valopt)(?&c)) (?&el) (?&nx) (?&el)
    | (?!(?&o)(?:(?:-p|--package|-c|--call|--before)(?:(?&c)|=)|(?&valopt)(?&c))) (?=(?&o)-) (?&el) )
  # A spec that can change under the same config: a registry name with no version, a range,
  # or a tag (latest, next); a git source not at a commit SHA. Local paths, file: and tarball
  # URLs are left alone.
  (?<unpinned> (?! [./~$%\\] | [A-Za-z]: | file: | https?: | - )
    (?: (?:git(?:\+[a-z]+)?://|git@|github:|gitlab:|bitbucket:|gist:) [^"'\s,\]\#]*
          (?: \#(?![0-9a-fA-F]{{7,40}}(?&c)) [^"'\s,\]]* )?
      | [\w.-]+/[\w.-]+ (?: \#(?![0-9a-fA-F]{{7,40}}(?&c)) [^"'\s,\]]* )?
      | (?:@[\w.-]+/)?[\w.-]+
          (?: @(?!(?&exact)(?&c)|npm:(?:@[\w.-]+/)?[\w.-]+@(?&exact)(?&c)) [^"'\s,\]/\#]* )? ) )
)
{START}
# cmd /c <runner>, and npm exec / pnpm dlx / yarn dlx / bun x. The command checks above tie
# each prefix to its command; once matched, a prefix is never re-read as the package.
(?> (?: (?=(?&o)/[cC](?&c)) (?&el) (?&nx) (?&el) (?&nx) )? )
(?> (?: (?: (?=(?&o)-) (?&el) (?&nx) )*+ (?=(?&o)(?:exec|x|dlx)(?&c)) (?&el) (?&nx) )? )
(?! (?: (?:(?&opt)|(?&srcopt)) (?&nx) )*+ (?&o)--before(?:(?&c)|=) )
(?: (?: (?:(?&opt)|(?&srcopt)) (?&nx) )*?
      (?: (?=(?&o)(?:-p|--package)(?&c)) (?&el) (?&nx) (?&o) | (?&o)--package= )
  | (?: (?&opt) (?&nx) )*+ (?&o) )
(?=(?&unpinned)(?&c))
(?<PKG>(?:[^"'\s,\[\]]|\[[^\]"'\s]*\])+)'''

NPM = NPM.replace("{{", "{").replace("}}", "}")

PY = rf'''(?sx)
(?(DEFINE)
{G}
  # Options of uv tool run and pipx run that take the next element as their value (uv 0.10.9,
  # pipx 1.8.0).
  (?<valopt> (?: --from|--spec|-w|--with|--with-editable|--with-requirements|-b
    |--build-constraints|--env-file|--python-platform|--torch-backend|--index|--default-index
    |-i|--index-url|--extra-index-url|-f|--find-links|--index-strategy|--keyring-provider|-P
    |--upgrade-package|--resolution|--prerelease|--fork-strategy|--exclude-newer-package
    |--no-sources-package|--reinstall-package|--link-mode|-C|--config-setting
    |--config-settings-package|--no-build-isolation-package|--no-build-package
    |--no-binary-package|--cache-dir|--refresh-package|-p|--python|--color
    |--allow-insecure-host|--directory|--project|--config-file|--pip-args ) (?![\w-]) )
  # Options that hold the resolution still: a cutoff date, or a constraints or overrides
  # file. Never consumed, so the scans below stop at them.
  (?<pinopt> (?: --exclude-newer|-c|--constraints|--overrides ) (?![\w-]) )
  (?<opt> (?=(?&o)(?&valopt)(?&c)) (?&el) (?&nx) (?&el)
    | (?!(?&o)(?:(?&valopt)(?&c)|(?&pinopt)(?:(?&c)|=))) (?=(?&o)-) (?&el) )
  (?<plainopt> (?!(?&o)(?:--from|--spec)(?:(?&c)|=)) (?&opt) )
{PY_UNPINNED}
)
{START}
# cmd /c uvx, uv tool run, pipx run; once matched, a prefix is never re-read as the package.
(?> (?: (?=(?&o)/[cC](?&c)) (?&el) (?&nx) (?&el) (?&nx)
      | (?=(?&o)tool(?&c)) (?&el) (?&nx) (?=(?&o)run(?&c)) (?&el) (?&nx)
      | (?=(?&o)run(?&c)) (?&el) (?&nx) )? )
(?! (?: (?&opt) (?&nx) )*+ (?&o)(?&pinopt)(?:(?&c)|=) )
# --from / --spec name the package (the positional is then a command); --with adds more.
(?: (?: (?&opt) (?&nx) )*?
      (?: (?=(?&o)(?:--from|--spec|--with|-w)(?&c)) (?&el) (?&nx) (?&o)
        | (?&o)(?:--from|--spec|--with)= )
  | (?: (?&plainopt) (?&nx) )*+ (?&o) )
(?=(?&unpinned)(?&c))
(?<PKG>(?:[^"'\s,\[\]]|\[[^\]"'\s]*\])+)'''

UVRUN = rf'''(?sx)
(?(DEFINE)
{G}
  # Options of uv run that take the next element as their value (uv 0.10.9).
  (?<valopt> (?: --extra|--no-extra|--group|--no-group|--only-group|--env-file|-w|--with
    |--with-editable|--with-requirements|--package|--python-platform|--index|--default-index
    |-i|--index-url|--extra-index-url|-f|--find-links|--index-strategy|--keyring-provider|-P
    |--upgrade-package|--resolution|--prerelease|--fork-strategy|--exclude-newer-package
    |--no-sources-package|--reinstall-package|--link-mode|-C|--config-setting
    |--config-settings-package|--no-build-isolation-package|--no-build-package
    |--no-binary-package|--cache-dir|--refresh-package|-p|--python|--color
    |--allow-insecure-host|--directory|--project|--config-file ) (?![\w-]) )
  (?<pinopt> --exclude-newer (?![\w-]) )
  (?<opt> (?=(?&o)(?&valopt)(?&c)) (?&el) (?&nx) (?&el)
    | (?!(?&o)(?:(?&valopt)(?&c)|(?&pinopt)(?:(?&c)|=))) (?=(?&o)-) (?&el) )
{PY_UNPINNED}
)
{START}
(?=(?&o)run(?&c)) (?&el) (?&nx)
(?! (?: (?&opt) (?&nx) )*+ (?&o)(?&pinopt)(?:(?&c)|=) )
# Only --with names packages; the first positional is the script or command.
(?: (?&opt) (?&nx) )*?
(?: (?=(?&o)(?:--with|-w)(?&c)) (?&el) (?&nx) (?&o) | (?&o)--with= )
(?=(?&unpinned)(?&c))
(?<PKG>(?:[^"'\s,\[\]]|\[[^\]"'\s]*\])+)'''

# One docker run option and its value, as elements (uses G's tokens). gen_mcp_filesystem_root.py
# imports it to find a bind mount among the options before the image.
DOCKER_OPTS = r'''
  # docker run's boolean long options (Docker 28.3); every other long option takes a value,
  # and so do the short options -a -c -e -h -l -m -p -u -v -w.
  (?<boolopt> (?: --rm|--init|--interactive|--tty|--privileged|--read-only|--detach
    |--publish-all|--no-healthcheck|--oom-kill-disable|--disable-content-trust|--quiet
    |--sig-proxy|--help|--use-api-socket ) (?![\w-]) )
  (?<opt> (?=(?&o)(?&boolopt)(?&c)) (?&el)
    | (?=(?&o)--[\w-]+=) (?&el)
    | (?!(?&o)(?&boolopt)(?&c)) (?=(?&o)--[\w-]+(?&c)) (?&el) (?&nx) (?&el)
    | (?=(?&o)-[dPiqt]*[acehlmpuvw](?&c)) (?&el) (?&nx) (?&el)
    | (?!(?&o)-[dPiqt]*[acehlmpuvw](?&c)) (?=(?&o)-[^-"'\s]) (?&el) )'''.strip("\n")

DOCKER = rf'''(?sx)
(?(DEFINE)
{G}
{DOCKER_OPTS}
)
{START}
(?: (?=(?&o)container(?&c)) (?&el) (?&nx) )?
(?=(?&o)run(?&c)) (?&el) (?&nx)
(?: (?&opt) (?&nx) )*+
(?&o) (?=(?!-)(?:[\w.-]+(?::\d+)?/)*[\w.-]+(?::latest)?(?&c))
(?<PKG>(?:[^"'\s,\[\]]|\[[^\]"'\s]*\])+)'''

SHELL = r'''(?x)
(?(DEFINE)
  (?<exact> =?v?\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.+-]*)? )
  (?<end> (?=\s|$|[;&|)`]|\\?["']) )
)
# A command position: the start, or after ; & | ( or exec.
.*? (?: ^ | [;&|(]\s* | \bexec\s+ )
(?: (?:npx|bunx|pnpx|pnpm\s+dlx|yarn\s+dlx|npm\s+exec)
      (?:\s+(?:-y|--yes|-q|--quiet|--silent))* \s+ (?:--\s+)?
      (?= (?!-) (?:@[\w.-]+/)?[\w.-]+ (?:@(?!(?&exact)(?&end))[^\s"'\\;&|)/\#]*)? (?&end) )
  | (?:uvx|uv\s+tool\s+run|pipx\s+run)
      (?:\s+(?:-q|--quiet|--refresh|--isolated|--offline|--no-cache))* \s+
      (?:--(?:from|spec)[\s=]\\?["']?)?
      (?= [A-Za-z0-9][\w.-]*(?:\[[^\]"'\s]*\])?(?:@latest)? (?&end) ) )
(?<PKG>[^\s"'\\;&|)`]+)'''

# Codex: one server's command and args, from $SRV. $SRV holds a [mcp_servers.<name>] table's
# keys, one inline table, or (dotted keys) the rest of a table starting at the server's command
# or args line; <P> is that line's "mcp_servers.<name>." / "<name>." prefix, empty otherwise,
# and both keys must carry it.
TOML_PREFIX = r"""(?<P>(?:(?:mcp_servers[ \t]*\.[ \t]*)?(?:"[^"\n]*"|'[^'\n]*'|[\w-]+)[ \t]*\.[ \t]*(?=(?:command|args)[ \t]*=))?)"""
TOML_EXTRACT = (r"""(?ms)\A(?=[ \t]*""" + TOML_PREFIX + r""")"""
    r"""(?=.*?(?:^|[{,])[ \t]*\k<P>command[ \t]*=[ \t]*["'](?<CMD>[^"'\n]*)["'])"""
    r""".*?(?:^|[{,])[ \t]*\k<P>args[ \t]*=[ \t]*(?<ARGS>\[(?:"(?:[^"\\\n]|\\.)*"|'[^'\n]*'|\#[^\n]*|[^\]"'\#])*\])""")
TOML_ENABLED = (r"""(?s)\A(?=[ \t]*""" + TOML_PREFIX.replace("<P>", "<p>") + r""")"""
    r"""(?!.*?(?:\A|[\n{,])[ \t]*\k<p>enabled[ \t]*=[ \t]*false\b)""")

# Command checks: the value may arrive quoted (YAML keeps quotes on the bound scalar).
def cmd(names, ext=r"(?:\.cmd|\.exe)?"):
    return rf"""(?i)^["']?(?:[^"']*[/\\])?(?:{names}){ext}["']?$"""

SEPX = r"""\s*(?:,|-(?=\s))\s*"""
def pre(body):
    return rf"""^(?:\[|-(?=\s))\s*{body}(?=[\s,\]]|$)"""

# (command regex, optional args prefix regex) per runner.
NPM_BRANCHES = [
    (cmd("npx|bunx|pnpx"), None),
    (cmd("npm"), pre(r"""["']?(?:exec|x)["']?""")),
    (cmd("pnpm|yarn"), pre(rf"""(?:["']?-[^"'\s,\]]*["']?{SEPX})*["']?dlx["']?""")),
    (cmd("bun", r"(?:\.exe)?"), pre(r"""["']?x["']?""")),
    (cmd("cmd", r"(?:\.exe)?"), "(?i)" + pre(rf"""["']?/c["']?{SEPX}["']?(?:[^"'\s,\]]*[/\\])?(?:npx|bunx|pnpx)(?:\.cmd|\.exe)?["']?""")),
]
PY_BRANCHES = [
    (cmd("uvx", r"(?:\.exe)?"), None),
    (cmd("uv", r"(?:\.exe)?"), pre(rf"""["']?tool["']?{SEPX}["']?run["']?""")),
    (cmd("pipx", r"(?:\.exe)?"), pre(r"""["']?run["']?""")),
    (cmd("cmd", r"(?:\.exe)?"), "(?i)" + pre(rf"""["']?/c["']?{SEPX}["']?(?:[^"'\s,\]]*[/\\])?uvx(?:\.exe)?["']?""")),
]
UVRUN_CMD = cmd("uv", r"(?:\.exe)?")
DOCKER_CMD = cmd("docker", r"(?:\.exe)?")
SHELL_CMD = cmd(r"(?:ba|z|da|k)?sh|cmd|pwsh|powershell", r"(?:\.exe)?")


def ind(text, n):
    return textwrap.indent(text, " " * n)


def block(key, text, n):
    """A YAML key with a literal block scalar."""
    return " " * n + f"{key}: |-\n" + ind(text, n + 2) + "\n"


def mvr(var, regex, n, literal=False):
    pad = " " * n
    out = f"{pad}- metavariable-regex:\n{pad}    metavariable: {var}\n"
    if literal or "\n" in regex or regex.strip() != regex or regex.startswith(("'", '"')):
        out += block("regex", regex, n + 4)
    else:
        out += f"{pad}    regex: {regex}\n"
    return out


# OpenGrep 1.30.2 aborts the whole file ("Other syntax error ... Invalid_argument: String.sub /
# Bytes.sub", every rule's findings in it lost) when a metavariable-pattern runs on a value that
# starts with a parenthesized expression followed by more of the expression: a member access or
# index, such as (a or b).strip(), (await r.get(u)).json(), or (xs as string[]).includes(k), or an
# operator, such as (m.get(k) ?? 0) === 0 or (k as string) === "HOME"; a pattern inside matches
# from that first parenthesis, and a condition inside reads a metavariable bound there
# (metavariable-regex, -comparison, -pattern). Put this regex on the same metavariable just
# before such a metavariable-pattern: it skips a value whose leading paren group (string
# literals inside it skipped), after any extra opening parentheses, is followed by anything but
# `=>`, a `:` return type, a closing parenthesis, or the end, so ((m.get(k) ?? 0) === 0) is
# skipped and an arrow function's `(k) => ...` and a value parenthesized as a whole are kept.
# A parenthesis later in the value, as in f((a ?? b) === c) or 0 === (a ?? b), is safe.
NOT_PAREN_RECEIVER = (r"""^(?!(?:\(\s*)*(?<p>\((?:[^()"'`]++|"(?:[^"\\]|\\.)*+"|'(?:[^'\\]|\\.)*+'|`(?:[^`\\]|\\.)*+`"""
                      r"""|(?&p))*+\))\s*+(?!=>|:|$|\)))""")


def paren_guard(var, n):
    """The NOT_PAREN_RECEIVER condition on `var`, to go before a metavariable-pattern on it."""
    return mvr(var, NOT_PAREN_RECEIVER, n, literal=True)


# ---- format scaffolding -------------------------------------------------------------------

def runner(fmt, cmd_re, prefix_re, n):
    """One runner branch: binds $ARGS for a server whose command matches."""
    pad = " " * n
    out = f"{pad}- patterns:\n"
    if fmt == "json":
        out += f"{pad}    - pattern-inside: '{{..., \"command\": \"$CMD\", ...}}'\n"
        out += mvr("$CMD", cmd_re, n + 4, literal=True)
        out += f"{pad}    - pattern: '\"args\": $ARGS'\n"
    elif fmt == "yaml":
        out += f"{pad}    - pattern-inside: |\n{pad}        command: $CMD\n{pad}        ...\n"
        out += mvr("$CMD", cmd_re, n + 4, literal=True)
        out += f"{pad}    - pattern: 'args: $ARGS'\n"
    elif fmt == "jsonc":  # $SRV is one server object; capture its command and args array.
        out += pregex(JSONC_EXTRACT, n + 4)
        out += mvr("$CMD", cmd_re, n + 4, literal=True)
    else:  # toml: $SRV is one server's keys; capture its command and args array.
        out += f"{pad}    - pattern-regex: " + TOML_EXTRACT + "\n"
        out += mvr("$CMD", cmd_re, n + 4, literal=True)
    if prefix_re:
        out += mvr("$ARGS", prefix_re, n + 4, literal=True)
    return out


def family(fmt, comment, branches, big, n):
    pad = " " * n
    out = ""
    for line in comment:
        out += f"{pad}# {line}\n"
    out += f"{pad}- patterns:\n"
    if len(branches) == 1:
        # Inline the single branch's terms.
        inner = runner(fmt, *branches[0], n + 4)
        inner = inner.split("\n", 1)[1]  # drop "- patterns:"
        inner = textwrap.dedent(inner)
        out += ind(inner, n + 4)
    else:
        out += f"{pad}    - pattern-either:\n"
        for b in branches:
            out += runner(fmt, *b, n + 8)
    out += mvr("$ARGS", big, n + 4, literal=True)
    return out


def shell(fmt, n):
    pad = " " * n
    out = f"{pad}# A shell given the whole command line: \"bash\", [\"-c\", \"... && npx -y pkg\"].\n"
    out += f"{pad}- patterns:\n"
    if fmt == "json":
        out += f"{pad}    - pattern-inside: '{{..., \"command\": \"$CMD\", ...}}'\n"
        out += mvr("$CMD", SHELL_CMD, n + 4, literal=True)
        out += f"{pad}    - pattern-inside: '\"args\": [...]'\n"
        out += f"{pad}    - pattern: '\"$S\"'\n"
    elif fmt == "yaml":
        out += f"{pad}    - pattern-inside: |\n{pad}        command: $CMD\n{pad}        ...\n"
        out += mvr("$CMD", SHELL_CMD, n + 4, literal=True)
        out += f"{pad}    - pattern-inside: 'args: [...]'\n"
        out += f"{pad}    - pattern: '\"$S\"'\n"
    else:
        inner = runner(fmt, SHELL_CMD, None, n).split("\n", 1)[1]
        out += inner
        if fmt == "toml":
            out += f"{pad}    # Each string in the array: \"basic\" (with escapes) or 'literal'.\n"
        out += f"{pad}    - metavariable-pattern:\n"
        out += f"{pad}        metavariable: $ARGS\n"
        out += f"{pad}        language: regex\n"
        out += f"{pad}        patterns:\n"
        if fmt == "jsonc":
            out += pregex(JSONC_STRING.replace("<V>", "<S>"), n + 10)
            out += mvr("$S", SHELL, n + 10, literal=True)
            return out
        out += f"{pad}          - pattern-either:\n"
        out += f"{pad}              - pattern-regex: '\"(?<S>(?:[^\"\\\\\\n]|\\\\.)*)\"'\n"
        out += f"{pad}              - pattern-regex: '\'\'(?<S>[^\'\'\\n]*)\'\''\n"
        # $S is only visible to conditions inside the metavariable-pattern that binds it.
        out += mvr("$S", SHELL, n + 10, literal=True)
        return out
    out += mvr("$S", SHELL, n + 4, literal=True)
    return out


def families(fmt, n):
    out = ""
    out += family(fmt, [
        "npm registry runners: npx, bunx, pnpx; npm exec, pnpm dlx, yarn dlx, bun x; and the",
        "Windows wrapper cmd /c npx. The runner's own options come before the package.",
    ], NPM_BRANCHES, NPM, n)
    out += family(fmt, [
        "PyPI runners: uvx, uv tool run, pipx run, and cmd /c uvx. --from / --spec name the",
        "package and make the first positional a command; --with adds more packages.",
    ], PY_BRANCHES, PY, n)
    out += family(fmt, [
        "uv run --with: extra packages installed next to a script, outside the project lock",
        "(the shape fastmcp install writes). The positional is the script, not a package.",
    ], [(UVRUN_CMD, None)], UVRUN, n)
    out += family(fmt, [
        "docker run with an image that has no tag or the \"latest\" tag. Version tags are left",
        "alone; a digest pin is stricter but not something this rule demands.",
    ], [(DOCKER_CMD, None)], DOCKER, n)
    out += shell(fmt, n)
    return out


SYNC_NOTE = """# Generated by scripts/gen_mcp_unpinned.py, which holds the runner and spec regexes shared by
# the mcp-config-unpinned-package rules for JSON, Continue YAML, Codex TOML, VS Code
# workspace files and Claude Code subagent front matter. Edit the script and run
# scripts/build.py; build.py --check fails if this file drifts.
"""

MESSAGE = """    message: >-
      This MCP server is started through a package runner with no fixed version, so the client
      installs whatever the registry serves at that moment, on every machine that loads this
      config, and runs it with the developer's credentials and the agent's tool access. One
      hijacked maintainer account is enough: the next client start runs the new release. In 2026
      the Mini Shai-Hulud and Hades campaigns published malicious releases of real MCP server
      packages (@antv/mcp-server-antv on npm, ray-mcp-server on PyPI). Pin an exact version
      (npx "pkg@1.2.3", uvx "pkg==1.2.3" or "pkg@1.2.3", "--from pkg==1.2.3"), a git source to a
      commit SHA, or a container image to a digest (image@sha256:...), and upgrade it on purpose.
      An npx package that is already a dependency in this project's lockfile runs the locked
      version, so that case can be ignored.
"""

METADATA = """    metadata:
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
      owasp-aisvs:
        - "v1.01-C10.1.1 - Component Integrity"
      mitre-atlas:
        - "AML.T0010.005 - AI Supply Chain Compromise: AI Agent Tool"
      cwe:
        - "CWE-494: Download of Code Without Integrity Check"
        - "CWE-829: Inclusion of Functionality from Untrusted Control Sphere"
      # Every match floats; an npx package that the project's lockfile already pins is the
      # common exception, and the rule can't see the lockfile.
      confidence: MEDIUM
      likelihood: LOW
      impact: HIGH
"""

COMMON_REFS = """        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP04-2025%E2%80%93Software-Supply-Chain-Attacks%26Dependency-Tampering.md
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM04_SupplyChain.md
"""
TAIL_REFS = """        - https://docs.npmjs.com/cli/v11/commands/npm-exec
        - https://docs.astral.sh/uv/guides/tools/
        - https://osv.dev/vulnerability/MAL-2026-4068
        - https://osv.dev/vulnerability/PYSEC-2026-1074
"""


# ---- file paths shared with gen_mcp_plaintext_secret.py ---------------------------------

# The MCP config files each format's rule scans. mcp-config-plaintext-secret* imports these,
# so both rule families always scan the same files.
JSON_PATHS = """    paths:
      include:
        # Claude Code project scope and plugins; also VS Code's portable workspace-root file.
        - ".mcp.json"
        # Cursor (.cursor/mcp.json, ~/.cursor/mcp.json), VS Code (.vscode/mcp.json and the user
        # profile's mcp.json), and other clients that use the same file name.
        - "mcp.json"
        # Claude Code user and local scope, and the administrator-managed file.
        - ".claude.json"
        - "managed-mcp.json"
        # Claude Code plugins can declare servers inline in the manifest or a marketplace entry.
        - ".claude-plugin/plugin.json"
        - ".claude-plugin/marketplace.json"
        - "claude_desktop_config.json"
        # Cline (VS Code extension global storage and ~/.cline/data/settings/).
        - "cline_mcp_settings.json"
        # Windsurf / Devin Desktop (~/.codeium/windsurf/, ~/.config/devin/).
        - "mcp_config.json"
        # GitHub Copilot CLI (~/.copilot/mcp-config.json), which VS Code also writes.
        - "mcp-config.json"
        # Gemini CLI settings and extension manifests.
        - ".gemini/settings.json"
        - "gemini-extension.json"
        # Zed: context_servers in project settings and the user's ~/.config/zed/settings.json
        # (Zed v1.25.2).
        - ".zed/settings.json"
        - ".config/zed/settings.json"
        # VS Code dev containers: customizations.vscode.mcp.servers.
        - ".devcontainer/devcontainer.json"
        - ".devcontainer.json"
        - ".devcontainer/*/devcontainer.json"
        # Continue reads any JSON file in .continue/mcpServers/ (Claude, Cursor or one-server
        # format), workspace or home, at any depth.
        - ".continue/mcpServers/**/*.json"
      exclude:
        # Continue skips these two names in .continue/mcpServers/.
        - ".continue/mcpServers/**/config.json"
        - ".continue/mcpServers/**/settings.json"
"""

# Where a server entry sits in those JSON files.
JSON_SCOPE = """      # "mcpServers" in most clients, "servers" in VS Code, "context_servers" in Zed. Continue
      # also accepts a file holding one server at its root.
      - pattern-either:
          - pattern-inside: '"mcpServers": {...}'
          - pattern-inside: '"servers": {...}'
          - pattern-inside: '"context_servers": {...}'
          - patterns:
              - pattern-inside: '{..., "command": $X, ...}'
              - pattern-not-inside: '"$K": {..., "command": $Y, ...}'
              - pattern-not-inside: '[..., {..., "command": $Y, ...}, ...]'
"""

YAML_PATHS = """    paths:
      include:
        # Continue (continue 5522c6f): ~/.continue/config.yaml, and block and agent files under
        # a workspace or home .continue/ folder (mcpServers/, agents/, assistants/, configs/).
        - ".continue/**/*.yaml"
        - ".continue/**/*.yml"
"""

TOML_PATHS = r"""    paths:
      include:
        # Codex: ~/.codex/config.toml, and .codex/config.toml in a trusted project.
        - ".codex/config.toml"
"""


# The servers in a Codex config.toml: binds $SRV to one server's keys (see TOML_EXTRACT).
# gen_mcp_remote_host.py and gen_mcp_hidden_path.py import it, so every family finds the same
# servers.
TOML_SERVERS = r"""      # $SRV is one server's keys.
      - pattern-either:
          # [mcp_servers.<name>]: its keys up to the next table header. Sub-tables such as
          # [mcp_servers.<name>.env] start their own header and are not matched.
          - pattern-regex: (?m)^[ \t]*\[[ \t]*mcp_servers[ \t]*\.[ \t]*(?:"[^"\n]*"|'[^'\n]*'|[\w-]+)[ \t]*\][ \t]*(?:\#[^\n]*)?\n(?<SRV>(?:(?![ \t]*\[)[^\n]*(?:\n|\z))*)
          # Servers inside the [mcp_servers] table ...
          - patterns:
              - pattern-regex: (?m)^[ \t]*\[[ \t]*mcp_servers[ \t]*\][ \t]*(?:\#[^\n]*)?\n(?<TABLE>(?:(?![ \t]*\[)[^\n]*(?:\n|\z))*)
              - metavariable-pattern:
                  metavariable: $TABLE
                  language: regex
                  pattern-either:
                    # Inline tables: <name> = { ... }.
                    - pattern-regex: (?m)^[ \t]*(?:"[^"\n]*"|'[^'\n]*'|[\w-]+)[ \t]*=[ \t]*(?<SRV>\{[^\n]*\})
                    # Dotted keys: <name>.command = ... $SRV starts at each command or args
                    # line and runs to the next header; the server match ties both keys to
                    # the same name.
                    - pattern-regex: (?m)^[ \t]*(?=(?<SRV>(?:"[^"\n]*"|'[^'\n]*'|[\w-]+)[ \t]*\.[ \t]*(?:command|args)[ \t]*=(?s:.*)))[^\n]*
          # ... and before the first table header: mcp_servers.<name> = { ... } or
          # mcp_servers.<name>.command = ...
          - patterns:
              - pattern-regex: \A(?<TABLE>(?:(?![ \t]*\[)[^\n]*(?:\n|\z))*)
              - metavariable-pattern:
                  metavariable: $TABLE
                  language: regex
                  pattern-either:
                    - pattern-regex: (?m)^[ \t]*mcp_servers[ \t]*\.[ \t]*(?:"[^"\n]*"|'[^'\n]*'|[\w-]+)[ \t]*=[ \t]*(?<SRV>\{[^\n]*\})
                    - pattern-regex: (?m)^[ \t]*(?=(?<SRV>mcp_servers[ \t]*\.[ \t]*(?:"[^"\n]*"|'[^'\n]*'|[\w-]+)[ \t]*\.[ \t]*(?:command|args)[ \t]*=(?s:.*)))[^\n]*
"""


# ---- VS Code workspace files, shared with the other MCP config generators -----------------

# VS Code reads MCP servers from a *.code-workspace file's settings.mcp (VS Code 1.143.1,
# mcpResourceScannerService.ts). The file is JSONC, which OpenGrep's JSON parser skips, so the
# -workspace rules are regex rules built from these scanners.
WORKSPACE_PATHS = """    paths:
      include:
        # VS Code multi-root workspace files: settings.mcp.servers.
        - "*.code-workspace"
"""

# Walks a line over plain text, whole strings and /* */ comments and stops at a // comment, so
# a match never starts inside a string or a comment.
JSONC_WALK = r"""(?m)(?:^|\G)(?:[^"/\n]|/(?![/*])|/\*(?:(?!\*/)[^\n])*+\*/|"(?:[^"\\\n]|\\.)*+")*?"""
JSONC_STRING = JSONC_WALK + r'''"(?<V>(?:[^"\\\n]|\\.)*+)"'''
JSONC_PAIR = JSONC_WALK + r'''"(?<K>[^"\\\n]*+)"[ \t]*+:[ \t]*+"(?<V>(?:[^"\\\n]|\\.)*+)"'''
# The inside of one balanced {...} (PLAIN is [^{}"/]) or [...] (PLAIN is [^\[\]"/]), skipping
# strings and comments.
_BAL = r'''(?:PLAIN++|"(?:[^"\\]|\\.)*+"|//[^\n]*+|/\*(?s:.*?)\*/|/|(?&GROUP))*+'''
_OBJ = r'''[^{}"/]'''
_ARR = r'''[^\[\]"/]'''
# Skips whole lines (each may end in a // comment) and then plain tokens on the target line, so
# whatever follows starts outside any string or comment. Use it inside a multi-line value such
# as $SRV, where JSONC_WALK's \G continuation doesn't apply. The _NB variant stays inside one
# brace level (for flat objects such as VS Code inputs).
_TOK = r'''(?:[^"/\nBRACES]|/(?![/*])|/\*(?:(?!\*/)[^\n])*+\*/|"(?:[^"\\\n]|\\.)*+")'''
JSONC_LINES = (r'''(?:TOK*+(?://[^\n]*+)?\n)*?TOK*?''').replace("TOK", _TOK.replace("BRACES", ""))
JSONC_LINES_NB = (r'''(?:TOK*+(?://[^\n]*+)?\n)*?TOK*?''').replace("TOK", _TOK.replace("BRACES", "{}"))
# VS Code reads servers from the workspace file's settings.mcp (VS Code 1.143.1,
# mcpResourceScannerService.ts).
JSONC_MCP = (JSONC_WALK + r'''"mcp"\s*+:\s*+(?<MCP>\{''' + _BAL.replace("PLAIN", _OBJ).replace("GROUP", "MCP") + r'''\})''')
# One server object inside it: "name": { ... }, not the "servers" wrapper itself.
JSONC_SERVER = (JSONC_WALK + r'''"(?!servers")[^"\\\n]*+"\s*+:\s*+(?<SRV>\{''' + _BAL.replace("PLAIN", _OBJ).replace("GROUP", "SRV") + r'''\})''')
JSONC_ARGS = (JSONC_WALK + r'''"args"\s*+:\s*+(?<ARGS>\[''' + _BAL.replace("PLAIN", _ARR).replace("GROUP", "ARGS") + r'''\])''')

# One server's command and args, from $SRV (the JSONC twin of TOML_EXTRACT). Both keys are
# found through JSONC_LINES, so a commented-out "command" line inside a live server is skipped.
JSONC_EXTRACT = (r'''\A(?=''' + JSONC_LINES + r'''"command"\s*+:\s*+"(?<CMD>[^"\\\n]*+)")'''
                 + JSONC_LINES + r'''"args"\s*+:\s*+(?<ARGS>\['''
                 + _BAL.replace("PLAIN", _ARR).replace("GROUP", "ARGS") + r'''\])''')


def pregex(regex, n):
    """A pattern-regex item as a literal block scalar (regexes may start with a quote)."""
    return " " * n + "- pattern-regex: |-\n" + ind(regex, n + 4) + "\n"


# ---- Claude Code subagent front matter, shared with the other MCP config generators -------

# A subagent file (.claude/agents/*.md) can declare MCP servers inline in its front matter's
# mcpServers list, each keyed by the server name, with the same schema as a .mcp.json entry
# (Claude Code docs, sub-agents, v2.1.310). Claude Code starts them without the per-server
# prompt a project .mcp.json server gets: after folder trust for a project's .claude/agents/,
# and with no trust check from ~/.claude/agents/. Plugin subagents ignore mcpServers, so a
# plugin's agents/ folder is left out. project-mcp-server-no-prompt-subagent scans the same
# files.
SUBAGENT_PATHS = """    paths:
      include:
        # Project (.claude/agents/) and user (~/.claude/agents/) subagents.
        - ".claude/agents/**"
"""

SUBAGENT_NOTE = """    # Generic, not YAML: OpenGrep can't parse a Markdown file's front matter, so a regex finds
    # the front matter's top-level mcpServers: block and the YAML checks run on that block.
"""

# The front matter, from a leading --- line to the next --- line, and its top-level
# mcpServers: block: the key line, then indented, list-item, comment and blank lines. Only the
# block is parsed as YAML, so another key that a YAML parser rejects (a description with
# ": " in it, as Claude Code's own examples have) doesn't hide the servers.
SUBAGENT_FRONT = r"""\A(?:\x{FEFF})?---[ \t]*\r?\n(?s:.*?)\r?\n---[ \t]*(?:\r?\n|\z)"""
SUBAGENT_BLOCK = (r"""(?m)^(?<MS>mcpServers[ \t]*:[^\r\n]*\r?\n"""
                  r"""(?:(?:[ \t]+[^\r\n]*|-[ \t][^\r\n]*|\#[^\r\n]*|[ \t]*)\r?\n)*)""")


def subagent_patterns(branches):
    """The patterns of a -subagent rule: the front matter's mcpServers block, parsed as YAML,
    then the family's YAML checks. branches are the -yaml rule's pattern-either branches,
    written at indent 16. An entry that is a bare name (- github) references a server
    configured elsewhere and holds nothing to check."""
    return ("    patterns:\n"
            "      # The front matter: from a leading --- line to the next --- line.\n"
            "      - pattern-regex: " + SUBAGENT_FRONT + "\n"
            "      # Its top-level mcpServers: block, parsed alone so that another key a YAML\n"
            "      # parser rejects (a description with \": \" in it) doesn't hide the servers.\n"
            "      - pattern-regex: " + SUBAGENT_BLOCK + "\n"
            "      - metavariable-pattern:\n"
            "          metavariable: $MS\n"
            "          language: yaml\n"
            "          patterns:\n"
            "            - pattern-inside: 'mcpServers: [...]'\n"
            "            - pattern-either:\n" + branches)


SUBAGENT_TRUST = """      Claude Code starts a subagent's inline MCP servers without the per-server prompt that a
      project .mcp.json server gets: once the folder is trusted for a project's
      .claude/agents/ file, and with no check at all for one in ~/.claude/agents/, whenever
      the subagent runs, including when Claude delegates to it on its own.
"""

SUBAGENT_REFS = """        - https://code.claude.com/docs/en/sub-agents#scope-mcp-servers-to-a-subagent
        - https://code.claude.com/docs/en/sub-agents#inline-server-trust
        - https://code.claude.com/docs/en/mcp
"""


def json_rule():
    s = "rules:\n  - id: mcp-config-unpinned-package\n"
    s += ind(SYNC_NOTE.format(a="-toml", b="-yaml"), 4)
    s += "    languages: [json]\n    severity: WARNING\n" + MESSAGE
    s += JSON_PATHS + "    patterns:\n" + JSON_SCOPE + "      - pattern-either:\n"
    s += families("json", 10)
    s += "      - focus-metavariable: $PKG\n"
    s += METADATA
    s += "      technology: [mcp, claude-code, claude-desktop, cursor, vscode, cline, windsurf, gemini-cli, continue]\n"
    s += "      references:\n" + COMMON_REFS + """        - https://code.claude.com/docs/en/mcp
        - https://code.claude.com/docs/en/plugins-reference
        - https://cursor.com/docs/context/mcp
        - https://code.visualstudio.com/docs/copilot/reference/mcp-configuration
        - https://modelcontextprotocol.io/docs/develop/connect-local-servers
        - https://docs.cline.bot/mcp/configuring-mcp-servers
        - https://docs.devin.ai/desktop/cascade/mcp
        - https://geminicli.com/docs/tools/mcp-server/
        - https://docs.continue.dev/customize/deep-dives/mcp
""" + TAIL_REFS
    return s


def yaml_rule():
    s = "rules:\n  - id: mcp-config-unpinned-package-yaml\n"
    s += ind(SYNC_NOTE.format(a="", b="-toml"), 4)
    s += "    languages: [yaml]\n    severity: WARNING\n" + MESSAGE
    s += YAML_PATHS + """    patterns:
      - pattern-inside: 'mcpServers: [...]'
      - pattern-either:
"""
    s += families("yaml", 10)
    s += "      - focus-metavariable: $PKG\n"
    s += METADATA
    s += "      technology: [mcp, continue]\n"
    s += "      references:\n" + COMMON_REFS + """        - https://docs.continue.dev/customize/deep-dives/mcp
        - https://docs.continue.dev/reference
        - https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/core/config/loadLocalAssistants.ts
""" + TAIL_REFS
    return s


def toml_rule():
    s = "rules:\n  - id: mcp-config-unpinned-package-toml\n"
    s += "    # Regex, not a parser: OpenGrep has no TOML support.\n"
    s += ind(SYNC_NOTE.format(a="", b="-yaml"), 4)
    s += "    languages: [regex]\n    severity: WARNING\n" + MESSAGE
    s += TOML_PATHS + r"""    patterns:
"""
    s += TOML_SERVERS + r"""      # enabled = false: Codex skips the server (for dotted keys, only that server's key counts).
      - metavariable-regex:
          metavariable: $SRV
          regex: {TOML_ENABLED}
      - metavariable-pattern:
          metavariable: $SRV
          language: regex
          patterns:
            - pattern-either:
"""
    s = s.replace("{TOML_ENABLED}", TOML_ENABLED)
    s += families("toml", 16)
    s += "      - focus-metavariable: $PKG\n"
    s += METADATA
    s += "      technology: [mcp, codex]\n"
    s += "      references:\n" + COMMON_REFS + """        - https://learn.chatgpt.com/docs/extend/mcp?surface=cli
        - https://github.com/openai/codex/blob/342ed69a174c206c1de52a59491b131e0753cfa5/codex-rs/config/src/mcp_types.rs
""" + TAIL_REFS
    return s


WORKSPACE_REGEX_NOTE = """    # Regex, not JSON: OpenGrep's JSON parser skips *.code-workspace files (unknown
    # extension), even when paths.include names them.
"""


def workspace_rule():
    s = "rules:\n  - id: mcp-config-unpinned-package-workspace\n" + WORKSPACE_REGEX_NOTE
    s += ind(SYNC_NOTE, 4)
    s += "    languages: [regex]\n    severity: WARNING\n" + MESSAGE
    s += WORKSPACE_PATHS + "    patterns:\n" + pregex(JSONC_MCP, 6)
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
    s += families("jsonc", 22)
    s += "      - focus-metavariable: $PKG\n"
    s += METADATA
    s += "      technology: [mcp, vscode]\n"
    s += "      references:\n" + COMMON_REFS + """        - https://code.visualstudio.com/docs/copilot/reference/mcp-configuration
        - https://github.com/microsoft/vscode/blob/1.143.1/src/vs/platform/mcp/common/mcpResourceScannerService.ts
""" + TAIL_REFS
    return s


SUBAGENT_MESSAGE = """    message: >-
      This subagent's inline MCP server is started through a package runner with no fixed
      version, so Claude Code installs whatever the registry serves at that moment and runs it
      with the developer's credentials and the agent's tool access.
""" + SUBAGENT_TRUST + """      One hijacked maintainer account is enough: the next run of the subagent runs the new
      release. In 2026 the Mini Shai-Hulud and Hades campaigns published malicious releases of
      real MCP server packages (@antv/mcp-server-antv on npm, ray-mcp-server on PyPI). Pin an
      exact version (npx "pkg@1.2.3", uvx "pkg==1.2.3" or "pkg@1.2.3", "--from pkg==1.2.3"), a
      git source to a commit SHA, or a container image to a digest (image@sha256:...), and
      upgrade it on purpose.
"""


def subagent_rule():
    s = "rules:\n  - id: mcp-config-unpinned-package-subagent\n" + SUBAGENT_NOTE
    s += ind(SYNC_NOTE, 4)
    s += "    languages: [generic]\n    severity: WARNING\n" + SUBAGENT_MESSAGE
    s += SUBAGENT_PATHS + subagent_patterns(families("yaml", 16))
    s += "      - focus-metavariable: $PKG\n"
    s += METADATA
    s += "      technology: [mcp, claude-code]\n"
    s += "      references:\n" + COMMON_REFS + SUBAGENT_REFS + TAIL_REFS
    return s


def render() -> dict[Path, str]:
    """The rule files and the content this script generates for each."""
    return {
        RULE_DIR / "mcp-config-unpinned-package.yaml": json_rule(),
        RULE_DIR / "mcp-config-unpinned-package-yaml.yaml": yaml_rule(),
        RULE_DIR / "mcp-config-unpinned-package-toml.yaml": toml_rule(),
        RULE_DIR / "mcp-config-unpinned-package-workspace.yaml": workspace_rule(),
        RULE_DIR / "mcp-config-unpinned-package-subagent.yaml": subagent_rule(),
    }


def main() -> int:
    for path, content in render().items():
        if not path.exists() or path.read_text() != content:
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
