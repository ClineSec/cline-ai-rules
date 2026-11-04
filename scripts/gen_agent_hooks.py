#!/usr/bin/env python3
"""Generate the hook auto-approval rules from one set of shared tests.

A Claude Code or Claude Agent SDK hook can answer the permission check itself: a PreToolUse
hook that returns permissionDecision "allow" (or the deprecated decision "approve"), or a
PermissionRequest hook that returns decision.behavior "allow". When the hook returns that for
every call and its matcher reaches a tool that acts, those tools run as if the session were in
bypassPermissions mode. These rules report it:

- agent-sdk-hook-auto-approves (Python) and agent-sdk-hook-auto-approves-ts (TypeScript and
  JavaScript): SDK hook callbacks registered in HookMatcher(...) / { matcher, hooks }.
- claude-settings-hook-auto-approves: command hooks in settings and plugin hook files that
  only print a fixed allow.
- claude-frontmatter-hook-auto-approves: the same in skill, command, and subagent frontmatter.
- codex-hook-auto-approves (+ -toml), copilot-hook-auto-approves, devin-hook-auto-approves:
  the same in the hook files of other agent clients that copied the format (see "other agent
  clients' hook files" below for what each one does with an allow, and the clients dropped).

Shared here: the read-only tool list (SAFE) behind the matcher test and the tool-name test,
the "prints a fixed allow" command test, and the `if` filter test.

Checked 2026-10-23 against claude-agent-sdk 0.2.173 (types.py: HookEvent, the hook output
TypedDicts, HookMatcher, the can_use_tool docstring), @anthropic-ai/claude-agent-sdk 0.3.310
(sdk.d.ts: HookEvent, HookCallbackMatcher, the hook output types, permissionPrompts), and the
Claude Code hooks reference and Agent SDK hooks and permissions pages:

- A PreToolUse allow skips the prompt, allow rules, and can_use_tool / canUseTool, but not
  deny or ask rules, critical-path removals, or reads from network paths.
- A PermissionRequest allow answers the prompt, and is the only answer a TypeScript session
  with permissionPrompts: 'none' gets.
- A matcher of "*", "" or none matches every tool; one with only letters, digits, _, -,
  spaces, `,` and `|` is a list of exact names; anything else is an unanchored JS regex.
- A handler's `if` filter (settings and frontmatter only) is one permission rule. For Bash it
  is best-effort: a compound command, $(), backticks, or $VAR run the hook when any part
  matches, or when Claude Code can't tell, so an allow there approves the whole command.
  Tested on Claude Code 2.1.310 (2026-10-24, `claude -p` in a throwaway folder): with
  `if: "Bash(echo hello*)"` and a fixed allow, `touch x` alone was denied, but
  `echo hello && touch x`, `echo hello; touch x`, `echo hello $(touch x)`, and
  `touch x && echo hello` all ran. A whole-tool rule (Edit, Edit(*), *) doesn't narrow
  anything.
- PreModelSwitch and Elicitation decisions don't approve tool calls.

Edit this script, not the rule files. scripts/build.py regenerates them, and
scripts/build.py --check fails when a rule file differs from what this script produces.

Usage:
    python3 scripts/gen_agent_hooks.py    # rewrite the rule files
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY_RULE = ROOT / "rules" / "python" / "permissions" / "agent-sdk-hook-auto-approves.yaml"
TS_RULE = ROOT / "rules" / "typescript" / "permissions" / "agent-sdk-hook-auto-approves-ts.yaml"
JSON_RULE = ROOT / "rules" / "agent-config" / "permissions" / "claude-settings-hook-auto-approves.yaml"
FM_RULE = ROOT / "rules" / "agent-config" / "permissions" / "claude-frontmatter-hook-auto-approves.yaml"


def ind(text: str, n: int) -> str:
    return textwrap.indent(text, " " * n)


# ---- shared tests ----------------------------------------------------------------------------

# Tools whose calls only read: the built-in read tools, and MCP tools named for reading
# (mcp__github__get_issue). Everything else (Bash, Write, Edit, WebFetch, Agent, any other MCP
# tool) acts.
SAFE = (r"(?<safe> (?: Read | Glob | Grep | LS | NotebookRead | TodoWrite | TaskList | TaskGet"
        r" | WebSearch | ListMcpResourcesTool | ReadMcpResourceTool"
        r" | mcp__[\w-]+?__(?i:get|list|read|search|find|query|describe|view|show|lookup|count)"
        r"(?:[_-][\w-]*)? ) )")

# A matcher string that reaches a tool outside SAFE: "*", "", Bash, "mcp__.*". Quiet only when
# every alternative is in SAFE, on the exact-name path ("Read|Glob", "Read, Grep") or as an
# anchored regex ("^(Read|Grep)$"). QUOTES allows the quotes a YAML binding keeps.
# The matcher text that names only SAFE tools, on the exact-name path or as an anchored regex.
SAFE_MATCHER = (r"(?: \s*+ (?&safe) (?: \s*+ [|,] \s*+ (?&safe) )*+ \s*+"
                r" | \^ \(? (?: \?: )? (?&safe) (?: \| (?&safe) )*+ \)? \$ )")


def matcher_regex(quotes: bool, safe: str = SAFE) -> str:
    q = "[\"']?" if quotes else ""
    return f"""(?x)
(?(DEFINE)
  {safe}
)
^ (?! {q} {SAFE_MATCHER} {q} $ )"""


# A tool-name literal outside SAFE, for `if tool_name == "Bash":` in a hook body.
TOOL_NAME_REGEX = f"""(?x)
(?(DEFINE)
  {SAFE}
)
^ (?! (?&safe) $ ) [\\w-]+ $"""

# An `if` filter that doesn't narrow the hook: "*", a whole tool outside SAFE (Edit, Edit(*)),
# or any Bash or PowerShell rule, which runs the hook on compound commands, $(), backticks,
# and $VAR. A read-only tool, or another tool with a real specifier (Edit(docs/**),
# WebFetch(domain:example.com)), narrows it.
IF_REGEX = f"""(?x)
(?(DEFINE)
  {SAFE}
)
^ (?! ["']? \\s*+ (?: (?&safe) (?: \\( [^)]*+ \\) )?+ | (?! (?: Bash | PowerShell ) \\( ) [\\w-]++ \\( \\s*+ (?! \\*{{1,2}} \\s*+ \\) ) [^)\\s] [^)]*+ \\) ) \\s*+ ["']? $ )"""

# A command line that only prints a fixed allow (echo, printf, cat, jq -n, a one-line
# interpreter): the key and value may carry JSON escapes (\\") or no quotes at all (jq -n
# '{hookSpecificOutput: {permissionDecision: "allow"}}'), and nothing in it could decide
# otherwise. "|| true" is not a branch.
GRANTS = r"""(?= .*? (?: permissionDecision | behavior ) \\*+ ["']? \s*+ : \s*+ \\*+ ["']? allow \b
      | .*? \b decision \\*+ ["']? \s*+ : \s*+ \\*+ ["']? approve \b )"""
COMMAND_REGEX = r"""(?x)
# Grants permission.
""" + GRANTS + r"""
# ... with nothing that could decide otherwise.
(?! .*? (?: \b (?: if | then | elif | case | while | until | test | grep ) \b
          | && | \|\| (?! \s*+ (?: true | : ) \b ) | \[ \[? \s | \bjq \s++ -\w*e
          | select \( | \$ \( | ` | \b (?: deny | ask | block | defer ) \b
          | \b exit \s++ 2 \b ) )"""
# An exec-form argument that is the allow JSON itself. A YAML binding keeps its quotes.
ARG_REGEX = r"""(?x)
""" + GRANTS + r"""
(?! .*? \b (?: deny | ask | block | defer ) \b )"""
YAML_ARG_REGEX = r"""(?x)
^ ["']
""" + GRANTS + r"""
(?! .*? \b (?: deny | ask | block | defer ) \b )"""


# Call names that read as a check (policy.enforce(...), verify_path(...)).
CHECK_CALL = r"\b\w*(?i:check|verify|validate|enforce|ensure|guard|authori[sz]e|require|policy|reject|forbid|permit)\w*\s*+\("

PY_RELAXED = (r"""(?sm)^(?!.*(?:^[ \t]*+(?:el)?if\b(?![^\n]*hook_event_name)(?![^\n]*tool\w*["']?\]?\)?\s*+(?:==|in)\s*+[\[({"'])"""
              r"""|^[ \t]*+(?:raise|assert|match|case)\b|^[^#\n]*\bif\b[^\n#]*\belse\b|["'](?:deny|ask|block|defer)["']|"""
              + CHECK_CALL + "))")
PY_STRICT = r"(?sm)^(?!.*^[ \t]*+(?:el)?if\b(?![^\n]*hook_event_name))"
TS_RELAXED = (r"""(?sm)^(?!.*(?:\bif\s*+\((?![^\n]*hook_event_name)(?![^\n]*tool\w*\s*+===?\s*+["'`])(?!\s*+\[[^\]\n]*\]\.includes\()"""
              r"""|\b(?:throw|switch|case)\b|\s\?\s|["'`](?:deny|ask|block|defer)["'`]|""" + CHECK_CALL + "))")
TS_STRICT = (r"""(?sm)^(?!.*(?:\bif\s*+\((?![^\n]*hook_event_name)"""
             r"""|\b(?:throw|switch|case)\b|\s\?\s|["'`](?:deny|ask|block|defer)["'`]|""" + CHECK_CALL + "))")


def mvr(mv: str, regex: str) -> str:
    return f"- metavariable-regex:\n    metavariable: {mv}\n    regex: |-\n{ind(regex, 6)}\n"


# ---- shared metadata -------------------------------------------------------------------------

def metadata(pack: str, confidence: str, technology: str, refs: list[str],
             likelihood: str = "MEDIUM") -> str:
    refs_text = "".join(f"        - {r}\n" for r in refs)
    return f"""    metadata:
      category: security
      subcategory: [audit]
      pack-category: {pack}
      owasp-llm:
        - "LLM03:2026 - Excessive Agency"
        - "LLM06:2025 - Excessive Agency"
      owasp-agentic:
        - "ASI02 - Tool Misuse and Exploitation"
        - "ASI05 - Unexpected Code Execution (RCE)"
      owasp-aisvs:
        - "v1.01-C9.5.1 - Agent Authorization, Delegation, and Continuous Enforcement"
        - "v1.01-C9.2.1 - High-Impact Action Approval and Irreversibility Controls"
      mitre-atlas:
        - "AML.T0053 - AI Agent Tool Invocation"
        - "AML.T0112.000 - Machine Compromise: Local AI Agent"
      cwe:
        - "CWE-250: Execution with Unnecessary Privileges"
      confidence: {confidence}
      likelihood: {likelihood}
      impact: HIGH
      technology: {technology}
      references:
{refs_text}"""


GEN_NOTE = """    # Generated by scripts/gen_agent_hooks.py, which holds the read-only tool list, command
    # test, and `if` filter test shared by the hook auto-approval rules, and the SDK, client,
    # and docs versions they were checked against. Edit the script and run scripts/build.py;
    # build.py --check fails if this file drifts.
"""

# Test files register approving hooks on purpose and run them against a mocked or throwaway
# session, so the SDK rules skip them, as the bypass-permissions rules and
# llm-debug-logging-enabled do. OpenGrep's own ignore list skips only test/ and tests/.
SDK_TEST_NOTE = """    # Tests register approving hooks on purpose against a mocked or throwaway session, so
    # test files are skipped, as in agent-sdk-bypass-permissions. OpenGrep's own ignore list
    # skips only test/ and tests/.
"""
PY_TEST_EXCLUDE = ["test_*.py", "*_test.py", "conftest.py", "test/", "tests/", "e2e/", "e2e-tests/"]
TS_TEST_EXCLUDE = ["*.test.ts", "*.test.tsx", "*.test.js", "*.test.mjs", "*.spec.ts", "*.spec.tsx",
                   "*.spec.js", "__tests__/", "test/", "tests/", "e2e/", "e2e-tests/"]


def test_excludes(globs: list[str]) -> str:
    return SDK_TEST_NOTE + "    paths:\n      exclude:\n" + "".join(f'        - "{g}"\n' for g in globs)


SDK_MESSAGE = """    message: >-
      This Claude Agent SDK hook approves every tool call it is registered for: the callback
      returns `permissionDecision: {q}allow{q}` (or a PermissionRequest `behavior: {q}allow{q}`, or the
      legacy `decision: {q}approve{q}`) without checking anything, and its matcher covers every tool
      or a tool that runs commands, writes files, or reaches the network. A hook's allow skips
      the permission prompt, `{allowed}`, and the `{can_use}` callback, so for those tools
      the session acts as if it ran in `bypassPermissions` mode; only deny and ask rules still
      apply. A prompt injection in any file, issue, web page, or tool result the agent reads can
      then run commands or change files with this process's credentials. Approve only calls the
      hook has checked (a read-only tool, an allowlisted command, a path inside the workspace),
      return `{{}}` to leave the rest to the normal permission flow, and deny or ask on anything
      it can't verify.
"""

CONFIG_TAIL = """the permission prompt
      and the allow list, so for those tools the session acts as if it ran in
      `bypassPermissions` mode; only deny and ask rules still apply. An `if` filter on Bash
      doesn't limit it: the hook also runs for compound commands and commands with $(),
      backticks, or variables, and its allow then approves the whole command. A prompt
      injection in any file, issue, web page, or tool result the agent reads can then run
      commands or change files with the developer's credentials. Use `permissions.allow` rules
      for the specific commands you trust (for example `Bash(npm test)`), or a hook script that
      checks the tool input and prints allow only for calls it has verified.
"""

JSON_MESSAGE = """    message: >-
      This Claude Code hook approves every tool call it is registered for: its command only
      prints a fixed `permissionDecision: "allow"` (or a PermissionRequest `behavior: "allow"`,
      or the legacy `decision: "approve"`), and its matcher covers every tool or a tool that
      runs commands, writes files, or reaches the network. A hook's allow skips """ + CONFIG_TAIL

FM_MESSAGE = """    message: >-
      This skill, slash command, or subagent declares a hook in its frontmatter that approves
      every tool call it is registered for: its command only prints a fixed
      `permissionDecision: "allow"` (or a PermissionRequest `behavior: "allow"`, or the legacy
      `decision: "approve"`), and its matcher covers every tool or a tool that runs commands,
      writes files, or reaches the network. Claude Code registers a skill's hooks as soon as
      the skill is invoked, by a person or by Claude itself, and keeps them for the rest of the
      session; a subagent's hooks run while it does. A hook's allow skips """ + CONFIG_TAIL


# ---- Python ----------------------------------------------------------------------------------

PY_ALLOW_SHAPES = [
    "'{..., \"permissionDecision\": \"allow\", ...}'",
    "'{..., \"decision\": {..., \"behavior\": \"allow\", ...}, ...}'",
    "'{..., \"decision\": \"approve\", ...}'",
    "$T(..., permissionDecision=\"allow\", ...)",
    "'$T(..., decision={..., \"behavior\": \"allow\", ...}, ...)'",
    "$T(..., decision=\"approve\", ...)",
    "return $F(..., \"allow\", ...)",
    "return $F(..., $K=\"allow\", ...)",
]
PY_CONST_SHAPES = [
    "<... {..., \"permissionDecision\": \"allow\", ...} ...>",
    "<... {..., \"decision\": {..., \"behavior\": \"allow\", ...}, ...} ...>",
    "<... $T(..., permissionDecision=\"allow\", ...) ...>",
]


def shapes(lines: list[str], n: int) -> str:
    return "".join(" " * n + f"- pattern: {s}\n" for s in lines)


def py_allow_block() -> str:
    """BODY grants permission outside any if, or inside an if on an acting tool's name."""
    tests = "".join(f"""    - pattern-inside: |
        if $TOOL {op}:
            ...
""" for op in ('== "$TN"', 'in [..., "$TN", ...]', 'in (..., "$TN", ...)', 'in {..., "$TN", ...}'))
    return f"""- metavariable-pattern:
    metavariable: $...BODY
    pattern-either:
      - patterns:
          - pattern-either:
{shapes(PY_ALLOW_SHAPES, 14)}          - pattern-not-inside: |
              if $C:
                  ...
      - patterns:
          - pattern-either:
{ind(tests, 10)}          - pattern-either:
{shapes(PY_ALLOW_SHAPES, 14)}          - metavariable-regex:
              metavariable: $TOOL
              regex: (?i).*tool
{ind(mvr("$TN", TOOL_NAME_REGEX), 10)}"""


def py_const_block() -> str:
    """BODY returns a module constant that holds an allow, with no branch."""
    regions = "".join(f"""    - pattern-inside: |
        $C = {s}
        ...
""" for s in PY_CONST_SHAPES)
    return f"- pattern-either:\n{regions}", f"""- metavariable-regex:
    metavariable: $...BODY
    regex: {PY_STRICT}
"""


PY_MATCHERS = ["HookMatcher(..., hooks={L}, ...)", "HookMatcher($POS, {L}, ...)",
               "$SDK.HookMatcher(..., hooks={L}, ...)", "$SDK.HookMatcher($POS, {L}, ...)"]


def py_branch(kind: str, source: str, placement: str) -> str:
    if kind == "def":
        region = """- pattern-inside: |
    async def $CB($...P):
        $...BODY
    ...
"""
        items = ["$CB", "self.$CB", "partial($CB, ...)", "functools.partial($CB, ...)"]
        refs = ["$CB", "self.$CB"]
    else:
        region = """- pattern-inside: |
    def $FACT(...):
        ...
        async def $CB($...P):
            $...BODY
        ...
        return $CB
    ...
"""
        items = ["$FACT(...)", "self.$FACT(...)"]
        refs = ["$FACT(...)", "self.$FACT(...)"]
    pre, body = ("", py_allow_block()) if source == "inline" else py_const_block()
    if source == "const":
        # The callback returns that constant ($C is bound by the region before it).
        if kind == "def":
            region += """- pattern-inside: |
    async def $CB($...P):
        ...
        return $C
    ...
"""
        else:
            region += """- pattern-inside: |
    def $FACT(...):
        ...
        async def $CB($...P):
            ...
            return $C
        ...
        return $CB
    ...
"""
    if placement == "literal":
        regs = "".join(f"    - pattern-inside: {m.format(L='[..., ' + i + ', ...]')}\n"
                       for i in items for m in PY_MATCHERS)
        reg = "- pattern-either:\n" + regs + "- pattern-either:\n" + "".join(
            f"    - pattern: {r}\n" for r in refs)
    else:
        lists = "".join(f"""    - pattern-inside: |
        $L = [..., {i}, ...]
        ...
    - pattern-inside: |
        $L: $LT = [..., {i}, ...]
        ...
""" for i in items)
        regs = "".join(f"    - pattern-inside: {m.format(L='$L')}\n" for m in PY_MATCHERS)
        reg = "- pattern-either:\n" + lists + "- pattern-either:\n" + regs + "- pattern: $L\n"
    # A constant's region comes first, so that $C is bound before the callback.
    return "- patterns:\n" + ind(pre + region + reg + body, 4)


def py_rule() -> str:
    branches = ""
    labels = {
        ("def", "inline", "literal"): "A coroutine defined in this file (a function, or a method registered as\n# self.name; functools.partial too), listed in the HookMatcher's hooks. It grants permission\n# outside any `if` (an early `return {}` for another event or for named tools leaves every\n# other tool approved), or inside `if tool_name == \"Bash\":` and the like, which is the same\n# as a matcher on that tool.",
        ("def", "inline", "listvar"): "The same, in a list kept in a variable and passed as hooks=.",
        ("def", "const", "literal"): "A coroutine that returns an allow dict kept in a module constant, with no `if`\n# other than the hook_event_name guard.",
        ("def", "const", "listvar"): "The same, in a list kept in a variable.",
        ("factory", "inline", "literal"): "A coroutine built by a factory in this file (def make_hook(...): async def hook\n# ...; return hook) and registered as make_hook(...).",
        ("factory", "inline", "listvar"): "The same, in a list kept in a variable.",
        ("factory", "const", "literal"): "A factory-built coroutine that returns an allow constant.",
        ("factory", "const", "listvar"): "The same, in a list kept in a variable.",
    }
    for kind in ("def", "factory"):
        for source in ("inline", "const"):
            for placement in ("literal", "listvar"):
                note = "".join(f"# {line}\n" if line else "#\n"
                               for line in labels[(kind, source, placement)].replace("# ", "").split("\n"))
                branches += ind(note + py_branch(kind, source, placement), 10)
    scope = ["HookMatcher(..., matcher={M}, ...)", "HookMatcher({M}, [...], ...)", "HookMatcher({M}, $HL, ...)",
             "$SDK.HookMatcher(..., matcher={M}, ...)", "$SDK.HookMatcher({M}, [...], ...)",
             "$SDK.HookMatcher({M}, $HL, ...)"]
    scope_lits = "".join(f"              - pattern-not-inside: {m.format(M='$ANY')}\n" for m in scope)
    scope_m = "".join(f"                  - pattern-inside: {m.format(M='$M')}\n" for m in scope)
    return f"""rules:
  - id: agent-sdk-hook-auto-approves
{GEN_NOTE}    languages: [python]
    severity: ERROR
{SDK_MESSAGE.format(q='"', allowed='allowed_tools', can_use='can_use_tool')}{test_excludes(PY_TEST_EXCLUDE)}    patterns:
      - pattern-either:
{branches}      # ... and nothing else in it could decide otherwise: no `if` other than the
      # hook_event_name guard and tool-name tests, no conditional expression, raise, assert,
      # match, other decision, or a call that reads as a check (policy.enforce(...)).
{ind(mvr("$...BODY", PY_RELAXED), 6)}      # The HookMatcher's matcher reaches more than read-only tools.
      - pattern-either:
          # No matcher (or matcher=None): every tool.
          - patterns:
              - pattern-inside: HookMatcher(...)
{scope_lits}          - patterns:
              - pattern-either:
{scope_m}              # None, a literal, or a constant (constant propagation); a matcher read from
              # elsewhere is left alone.
              - metavariable-pattern:
                  metavariable: $M
                  pattern-either:
                    - pattern: None
                    - patterns:
                        - pattern: '"$MS"'
{ind(mvr("$MS", matcher_regex(False)), 24)}      # Bypass mode already approves everything; agent-sdk-bypass-permissions reports it.
      - pattern-not-inside: $FN(..., permission_mode="bypassPermissions", ...)
{metadata("ai-code", "MEDIUM", "[claude-agent-sdk, anthropic]", [
        "https://code.claude.com/docs/en/agent-sdk/hooks",
        "https://code.claude.com/docs/en/agent-sdk/permissions",
        "https://code.claude.com/docs/en/hooks",
        "https://github.com/anthropics/claude-agent-sdk-python/blob/v0.2.173/src/claude_agent_sdk/types.py",
        "https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md"])}"""


# ---- TypeScript / JavaScript -----------------------------------------------------------------

TS_ALLOW_SHAPES = [
    "'{..., permissionDecision: \"allow\", ...}'",
    "'{..., decision: {..., behavior: \"allow\", ...}, ...}'",
    "'{..., decision: \"approve\", ...}'",
]
TS_HELPER_SHAPES = [
    "return $F(..., \"allow\", ...);",
    "'($...P) => $F(..., \"allow\", ...)'",
    "'async ($...P) => $F(..., \"allow\", ...)'",
]
ARROW = ["'($...P) => $BODY'", "'async ($...P) => $BODY'"]


def ts_allow_block(text: str) -> str:
    tests = "".join(f"    - pattern-inside: {t}\n" for t in (
        'if ($TOOL === "$TN") $S', 'if ($TOOL == "$TN") $S', 'if ([..., "$TN", ...].includes($TOOL)) $S'))
    return f"""- metavariable-pattern:
    metavariable: {text}
    pattern-either:
      - patterns:
          - pattern-either:
{shapes(TS_ALLOW_SHAPES + TS_HELPER_SHAPES, 14)}          - pattern-not-inside: if ($C) $S
      - patterns:
          - pattern-either:
{ind(tests, 10)}          - pattern-either:
{shapes(TS_ALLOW_SHAPES + TS_HELPER_SHAPES[:1], 14)}          - metavariable-regex:
              metavariable: $TOOL
              regex: (?i).*tool
{ind(mvr("$TN", TOOL_NAME_REGEX), 10)}{mvr(text, TS_RELAXED)}"""


def ts_const_block(text: str, kind: str) -> str:
    regions = "".join(f"""    - pattern-inside: |
        {decl} = <... {s} ...>;
        ...
""" for s in ("{..., permissionDecision: \"allow\", ...}", "{..., decision: {..., behavior: \"allow\", ...}, ...}")
        for decl in ("const $C", "const $C: $CT"))
    if text != "$FUNC" or kind == "factory":
        # A function body or a factory: ts_branch adds regions that return $C itself.
        return f"- pattern-either:\n{regions}", mvr(text, TS_STRICT)
    rets = ["'($...P) => $RET'", "'async ($...P) => $RET'",
            "'($...P) => { ... return $RET; }'", "'async ($...P) => { ... return $RET; }'"]
    return f"- pattern-either:\n{regions}", f"""- metavariable-pattern:
    metavariable: {text}
    pattern-either:
{shapes(rets, 6)}- metavariable-comparison:
    comparison: str($RET) == str($C)
{mvr(text, TS_STRICT)}"""


def fn_regions(head: str) -> str:
    """Function declarations and const function expressions named $CB, binding $...BODY."""
    decls = [f"{a}function {head}($...P) {{ $...BODY }}" for a in ("async ", "")]
    exprs = [f"const $CB{t} = {a}function{n} ($...P) {{ $...BODY }};"
             for t in ("", ": $T") for a in ("async ", "") for n in ("", " $FN")]
    return decls, exprs


# Factory heads: a function declaration (typed or not) or a const arrow with a block body.
FACT_HEADS = [("function $FACT($...FP) {", "}"), ("function $FACT($...FP): $RT {", "}"),
              ("const $FACT = ($...FP) => {", "};")]


def factory_fn_regions() -> list[str]:
    """Factories that declare a function and return it by name (`async function inner(input)
    {...} return inner;`), binding the callback's $...BODY. A function expression returned
    directly (`return async function allowAll(input) {...}`) already matches the arrow shapes
    of the "factory" kind, and so does a block-bodied arrow factory (the arrow pattern finds
    the returned arrow inside the block)."""
    declared = [f"{a}function $CB($...P) {{ $...BODY }} ... return $CB;" for a in ("async ", "")]
    return [f"{h} ... {r} {t}" for h, t in FACT_HEADS for r in declared]


TS_KINDS = {
    # name: (regions, text metavariable, items in the hooks array, refs)
    "inline": ([], "$FUNC", ["$FUNC"], ["$FUNC"]),
    "arrow": (["const $CB = $FUNC;", "const $CB: $T = $FUNC;"], "$FUNC", ["$CB"], ["$CB"]),
    "function": (fn_regions("$CB")[0] + fn_regions("$CB")[1], "$...BODY", ["$CB"], ["$CB"]),
    "method": (["class $CLS {\n  ...\n  async $CB($...P) { $...BODY }\n  ...\n}",
                "class $CLS {\n  ...\n  $CB($...P) { $...BODY }\n  ...\n}"],
               "$...BODY", ["this.$CB", "this.$CB.bind(this)"], ["this.$CB"]),
    "field": (["class $CLS {\n  ...\n  $CB = $FUNC;\n  ...\n}"],
              "$FUNC", ["this.$CB", "this.$CB.bind(this)"], ["this.$CB"]),
    "factory": (["function $FACT($...FP) { ... return $FUNC; }", "function $FACT($...FP): $RT { ... return $FUNC; }",
                 "const $FACT = ($...FP) => $FUNC;"],
                "$FUNC", ["$FACT(...)"], ["$FACT(...)"]),
    "factory-function": (factory_fn_regions(), "$...BODY", ["$FACT(...)"], ["$FACT(...)"]),
}


def ts_branch(kind: str, source: str, placement: str) -> str:
    regions, text, items, refs = TS_KINDS[kind]
    region_text = ""
    trailing = "" if kind in ("method", "field") else "\n..."
    if regions:
        region_text = "- pattern-either:\n" + "".join(
            f"    - pattern-inside: |\n{ind(r + trailing, 8)}\n" for r in regions)
    if text == "$FUNC" and source == "inline":
        region_text += "- metavariable-pattern:\n    metavariable: $FUNC\n    pattern-either:\n" + shapes(ARROW, 6)
    if text != "$FUNC" and source == "const":
        # ... and returns the constant.
        region_text += "- pattern-either:\n" + "".join(
            f"    - pattern-inside: |\n{ind(r.replace('{ $...BODY }', '{ ... return $C; }') + trailing, 8)}\n"
            for r in regions)
    if kind == "factory" and source == "const":
        # ... and the closure it returns gives back the constant.
        region_text += "- pattern-either:\n" + "".join(
            f"    - pattern-inside: |\n{ind(r.replace('$FUNC', a) + trailing, 8)}\n"
            for r in regions for a in ("($...P) => $C", "async ($...P) => $C",
                                       "($...P) => { ... return $C; }", "async ($...P) => { ... return $C; }"))
    if placement == "literal":
        reg = "- pattern-either:\n" + "".join(
            f"    - pattern-inside: '{{..., hooks: [..., {i}, ...], ...}}'\n" for i in items)
        reg += "- pattern-either:\n" + "".join(f"    - pattern: {r}\n" for r in refs)
    else:
        lists = "".join(f"    - pattern-inside: |\n        {d} = [..., {i}, ...];\n        ...\n"
                        for i in items for d in ("const $L", "const $L: $LT"))
        reg = ("- pattern-either:\n" + lists +
               "- pattern-inside: '{..., hooks: $L, ...}'\n- pattern: $L\n")
    if kind == "inline":
        # The inline function is the array element itself: bind it first.
        if placement == "literal":
            pre = "- pattern-inside: '{..., hooks: [..., $FUNC, ...], ...}'\n- pattern: $FUNC\n"
        else:
            pre = ("- pattern-either:\n    - pattern-inside: |\n        const $L = [..., $FUNC, ...];\n        ...\n"
                   "    - pattern-inside: |\n        const $L: $LT = [..., $FUNC, ...];\n        ...\n"
                   "- pattern-inside: '{..., hooks: $L, ...}'\n- pattern: $L\n")
        region_text = pre + region_text
        reg = ""
    pre, body = ("", ts_allow_block(text)) if source == "inline" else ts_const_block(text, kind)
    return "- patterns:\n" + ind(pre + region_text + reg + body, 4)


TS_LABELS = {
    "inline": "An arrow function written in the hooks array",
    "arrow": "A const arrow function defined earlier in the file (typed `: HookCallback` or not)",
    "function": "A function declaration, or a const function expression",
    "method": "A class method registered as this.name (or this.name.bind(this))",
    "field": "A class field holding an arrow function, registered as this.name",
    "factory": "An arrow function returned by a factory in this file, registered as makeHook(...)",
    "factory-function": ("A function declared inside a factory in this file and returned by name "
                         "(`async function inner(input) {...} return inner;`), registered as "
                         "makeHook(...)"),
}


def ts_rule() -> str:
    branches = ""
    for kind in TS_KINDS:
        for source in ("inline", "const"):
            if kind == "inline" and source == "const":
                continue
            for placement in ("literal", "listvar"):
                what = TS_LABELS[kind]
                what += ", in a list kept in a const and passed as hooks:" if placement == "listvar" else ""
                what += (". It grants permission outside any `if` (an early `return {}` for another\n"
                         "# event or named tools leaves every other tool approved), or inside\n"
                         "# `if (tool_name === 'Bash')` and the like, which is the same as a matcher on that tool;\n"
                         "# and nothing else in it could decide otherwise (no other `if`, ternary, switch, throw,\n"
                         "# other decision, or a call that reads as a check)."
                         if source == "inline" else
                         ", that returns an allow object kept in a const, with no `if` other\n"
                         "# than the hook_event_name guard.")
                note = "".join(f"# {line}\n" for line in textwrap.fill(what.replace("\n# ", " "), 90).split("\n"))
                branches += ind(note + ts_branch(kind, source, placement), 10)
    return f"""rules:
  - id: agent-sdk-hook-auto-approves-ts
{GEN_NOTE}    languages: [typescript, javascript]
    severity: ERROR
{SDK_MESSAGE.format(q="'", allowed='allowedTools', can_use='canUseTool')}{test_excludes(TS_TEST_EXCLUDE)}    patterns:
      - pattern-either:
{branches}      # The matcher object's matcher reaches more than read-only tools.
      - pattern-either:
          # No matcher: every tool.
          - patterns:
              # The matcher object itself, so that the not-inside below sees it: a hooks array,
              # or a list kept in a const.
              - pattern-either:
                  - pattern-inside: '{{..., hooks: [...], ...}}'
                  - patterns:
                      - pattern-inside: '{{..., hooks: $L, ...}}'
                      - metavariable-regex:
                          metavariable: $L
                          regex: ^[A-Za-z_$][\\w$]*$
              - pattern-not-inside: '{{..., matcher: $ANY, ...}}'
          - patterns:
              - pattern-inside: '{{..., matcher: $M, ...}}'
              # undefined, a literal, or a const (constant propagation); a matcher read from
              # elsewhere is left alone.
              - metavariable-pattern:
                  metavariable: $M
                  pattern-either:
                    - pattern: undefined
                    - patterns:
                        - pattern: '"$MS"'
{ind(mvr("$MS", matcher_regex(False)), 24)}      # Bypass mode already approves everything; agent-sdk-bypass-permissions-ts reports it.
      - pattern-not-inside: '{{..., permissionMode: <... "bypassPermissions" ...>, ...}}'
{metadata("ai-code", "MEDIUM", "[claude-agent-sdk, anthropic]", [
        "https://code.claude.com/docs/en/agent-sdk/hooks",
        "https://code.claude.com/docs/en/agent-sdk/permissions",
        "https://code.claude.com/docs/en/hooks",
        "https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk/v/0.3.310",
        "https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md"])}"""


# ---- settings and plugin hook files (JSON) ---------------------------------------------------

def json_rule() -> str:
    return f"""rules:
  - id: claude-settings-hook-auto-approves
{GEN_NOTE}    languages: [json]
    severity: ERROR
{JSON_MESSAGE}    paths:
      include:
        - ".claude/settings.json"
        - ".claude/settings.local.json"
        - "managed-settings.json"
        # Claude Code plugins: hooks/hooks.json, other hook files plugin.json names (in public
        # plugins they sit under hooks/), and inline hooks in the manifest. The event names
        # matched below are Claude Code's, so other tools' hook files stay quiet.
        - "hooks/*.json"
        - ".claude-plugin/plugin.json"
      exclude:
        # GitHub Copilot's repository hook files: copilot-hook-auto-approves reads them.
        - ".github/hooks/*.json"
    # Hooks that run a script, and prompt, agent, http, and mcp_tool hooks, decide at run time
    # and are left alone; agent-hook-runs-local-script reports repo scripts.
    patterns:
      - pattern-either:
          - pattern-inside: '"PreToolUse": [...]'
          - pattern-inside: '"PermissionRequest": [...]'
      - pattern-either:
          # Shell form: the command line prints the decision and nothing in it could decide
          # otherwise.
          - patterns:
              - pattern: '{{..., "type": "command", "command": "$CMD", ...}}'
              - pattern-not: '{{..., "args": $ARGS, ...}}'
{ind(mvr("$CMD", COMMAND_REGEX), 14)}              - focus-metavariable: $CMD
          # Exec form: "command": "echo" (or printf) with the decision as an argument.
          - patterns:
              - pattern: '{{..., "type": "command", "command": "$CMD", "args": [..., "$ARG", ...], ...}}'
              - metavariable-regex:
                  metavariable: $CMD
                  regex: ^(?:/(?:usr/)?bin/)?(?:echo|printf)$
{ind(mvr("$ARG", ARG_REGEX), 14)}              - focus-metavariable: $ARG
      # A handler's `if` filter keeps the hook quiet only when it narrows the call (see IF_REGEX
      # in the script): Bash rules and whole-tool rules don't. On Claude Code 2.1.310
      # (2026-10-24), `if: "Bash(echo hello*)"` also ran its hook for `touch x && echo hello`.
      - pattern-either:
          - patterns:
              - pattern-inside: '{{..., "type": "command", ...}}'
              - pattern-not-inside: '{{..., "if": $IF, ...}}'
          - patterns:
              - pattern-inside: '{{..., "if": "$IFV", ...}}'
{ind(mvr("$IFV", IF_REGEX), 14)}      - pattern-either:
          # No matcher: every tool.
          - patterns:
              - pattern-inside: '{{..., "hooks": [...], ...}}'
              - pattern-not-inside: '{{..., "matcher": $ANY, "hooks": [...], ...}}'
              - pattern-not-inside: '{{..., "hooks": [...], "matcher": $ANY, ...}}'
          - patterns:
              - pattern-either:
                  - pattern-inside: '{{..., "matcher": "$MS", "hooks": [...], ...}}'
                  - pattern-inside: '{{..., "hooks": [...], "matcher": "$MS", ...}}'
{ind(mvr("$MS", matcher_regex(False)), 14)}{metadata("agent-config", "HIGH", "[claude-code]", [
        "https://code.claude.com/docs/en/hooks",
        "https://code.claude.com/docs/en/permissions",
        "https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md"])}"""


# ---- other agent clients' hook files ---------------------------------------------------------
#
# The same check for agent clients that copied Claude Code's hook format. Checked 2026-10-24:
#
# - Codex rust-v0.164.0: a PermissionRequest hook runs before the approval prompt and the auto
#   reviewer, and its decision.behavior "allow" approves the request (core/src/tools/approvals.rs,
#   hooks/src/events/permission_request.rs): commands that ask to leave the sandbox, network
#   access, patches, write_stdin, and MCP tool calls. A PreToolUse permissionDecision "allow"
#   only applies updatedInput and never approves anything (hooks/src/events/pre_tool_use.rs:
#   "unsupported permissionDecision:allow"), so PreToolUse is left alone. Hooks load from
#   .codex/hooks.json, [hooks] tables in .codex/config.toml, and plugins (hooks/hooks.json,
#   which claude-settings-hook-auto-approves already scans, or inline in the manifest). Each
#   non-managed hook runs only after the user trusts it, pinned by its hash
#   (hooks/src/engine/discovery.rs), so likelihood is LOW. Matchers: "*", "" or none match
#   every tool; letters, digits, _ and | are exact names; anything else is an unanchored regex.
# - GitHub Copilot CLI (docs and changelog, 1.0.103): a preToolUse permissionDecision "allow"
#   suppresses the approval prompt since 1.0.18; a permissionRequest behavior "allow"
#   short-circuits the rules engine and the prompt, except for requests to leave the sandbox.
#   Event names may be camelCase or PascalCase, entries flat or Claude-nested, and commands
#   bash, powershell, command, or exec plus args. Matchers are full-match regexes.
#   VS Code 1.143.1 (Local agent harness, chat.useHooks on by default) reads .github/hooks/
#   too, auto-approves on a PreToolUse hookSpecificOutput allow
#   (languageModelToolsService.ts), and drops matchers when it parses a hook entry
#   (hookSchema.ts extractHookCommandsFromItem), so a preToolUse allow is reported whatever its
#   matcher says.
# - Devin CLI (docs): a PermissionRequest hook "implements custom approval logic", and its
#   documented auto-approve example prints decision "approve". Whether a PreToolUse approve
#   skips the prompt isn't documented (closed source), so PreToolUse is left alone.
#
# Dropped, with sources: Gemini CLI v0.65.0 reads only ask, block, and deny from a BeforeTool
# hook (scheduler/hook-utils.ts, scheduler/scheduler.ts), so its "allow" changes nothing.
# Cursor's hooks only deny: "Returning allow from a hook does not override the MCP approval
# system", and a shell hook's allow doesn't run a command outside the allowlist (Cursor forum,
# 2.1.36 and 2.6.19, 2026-03-21; the hooks docs don't say allow approves; closed source).
# Windsurf / Devin Desktop and Kiro hooks can only block (exit code 2).

CODEX_RULE = ROOT / "rules" / "agent-config" / "permissions" / "codex-hook-auto-approves.yaml"
CODEX_TOML_RULE = ROOT / "rules" / "agent-config" / "permissions" / "codex-hook-auto-approves-toml.yaml"
COPILOT_RULE = ROOT / "rules" / "agent-config" / "permissions" / "copilot-hook-auto-approves.yaml"
DEVIN_RULE = ROOT / "rules" / "agent-config" / "permissions" / "devin-hook-auto-approves.yaml"

# Copilot CLI's own read-only tool names (the view and glob tools; reads never reach a
# permissionRequest hook anyway), next to the Claude names its Claude-format matchers use.
COPILOT_SAFE = SAFE.replace("(?: Read | Glob |", "(?: Read | Glob | view | glob |")
assert COPILOT_SAFE != SAFE

def folded_message(text: str) -> str:
    """A folded message: block, wrapped at 96 columns."""
    lines = textwrap.wrap(" ".join(text.split()), 90)
    return "    message: >-\n" + "".join(f"      {line}\n" for line in lines)


CLIENT_TAIL = ("A prompt injection in any file, issue, web page, or tool result the agent reads can "
               "then run commands or change files with the developer's credentials.")

CODEX_MESSAGE = folded_message(
    'This Codex hook approves every request it is registered for: its PermissionRequest command '
    'only prints a fixed `decision: {"behavior": "allow"}`, and its matcher covers every tool or '
    'one that runs commands, writes files, or calls an MCP server. Codex runs PermissionRequest '
    'hooks before it shows the approval prompt or the auto-reviewer, and an allow answers the '
    'request (Codex 0.164), so commands that ask to leave the sandbox, network access, patches, '
    'and MCP tool calls go through without anyone seeing them. Codex asks each developer to trust '
    'a project hook once, pinned by its hash; from then on the hook approves for them. '
    + CLIENT_TAIL + ' Approve the specific commands you trust with prefix rules in .codex/rules, '
    'or have a hook script check the request and print allow only for calls it has verified, '
    'returning nothing for the rest.')

COPILOT_MESSAGE = folded_message(
    'This GitHub Copilot hook approves every tool call it is registered for: its command only '
    'prints a fixed `permissionDecision: "allow"` (preToolUse) or `behavior: "allow"` '
    '(permissionRequest). Since Copilot CLI 1.0.18 a preToolUse allow suppresses the approval '
    'prompt, and a permissionRequest allow skips the permission rules and the prompt. VS Code\'s '
    'agent hooks read the same .github/hooks/ files, auto-approve on a PreToolUse allow, and '
    'ignore `matcher` (VS Code 1.143), so there a preToolUse allow approves every tool, whatever '
    'its matcher says. ' + CLIENT_TAIL + ' Approve the specific commands you trust with '
    '`--allow-tool` rules, or have a hook script check the tool input and print allow only for '
    'calls it has verified, returning nothing for the rest.')

DEVIN_MESSAGE = folded_message(
    'This Devin CLI hook approves every permission request it is registered for: its '
    'PermissionRequest command only prints a fixed `decision: "approve"` (or an allow), and its '
    'matcher covers every tool or one that runs commands, writes files, or reaches the network. '
    'Devin CLI runs PermissionRequest hooks when it needs a permission decision, and an approve '
    'answers it instead of the developer. ' + CLIENT_TAIL + ' Allow the specific commands you '
    'trust in the permission settings, or have a hook script check the tool input and approve '
    'only calls it has verified, returning nothing for the rest.')


def client_handler(cmd_keys: list[str], typed: bool, exec_key: str | None) -> str:
    """A command hook that only prints a fixed allow, bound as $OUT."""
    t = '"type": "command", ' if typed else ""
    shell = "- patterns:\n    - pattern-either:\n" + "".join(
        f"        - pattern: '{{..., {t}\"{k}\": \"$OUT\", ...}}'\n" for k in cmd_keys)
    if exec_key:
        shell += f"    - pattern-not: '{{..., \"{exec_key}\": $EXEC, ...}}'\n"
    shell += ind(mvr("$OUT", COMMAND_REGEX), 4)
    text = ("# Shell form: the command line prints the decision and nothing in it could decide\n"
            "# otherwise.\n" + shell)
    if exec_key:
        text += f"""# Exec form: "{exec_key}": "echo" (or printf) with the decision as an argument.
- patterns:
    - pattern: '{{..., "{exec_key}": "$PROG", "args": [..., "$OUT", ...], ...}}'
    - metavariable-regex:
        metavariable: $PROG
        regex: ^(?:/(?:usr/)?bin/)?(?:echo|printf)$
{ind(mvr("$OUT", ARG_REGEX), 4)}"""
    return "- pattern-either:\n" + ind(text, 4)


def client_matcher(cmd_keys: list[str], flat: bool, safe: str) -> str:
    """The entry's matcher reaches more than read-only tools."""
    text = f"""# A matcher that reaches more than read-only tools.
- patterns:
    - pattern-inside: '{{..., "matcher": "$MS", ...}}'
{ind(mvr("$MS", matcher_regex(False, safe)), 4)}# A Claude-style group with no matcher: every tool.
- patterns:
    - pattern-inside: '{{..., "hooks": [...], ...}}'
    - pattern-not-inside: '{{..., "matcher": $ANY, ...}}'
"""
    if flat:
        text += "# A flat entry (the handler itself) with no matcher.\n- patterns:\n    - pattern-either:\n"
        text += "".join(f"        - pattern-inside: '{{..., \"{k}\": $C, ...}}'\n" for k in cmd_keys)
        text += ("    - pattern-not-inside: '{..., \"matcher\": $ANY, ...}'\n"
                 "    - pattern-not-inside: '{..., \"hooks\": [...], ...}'\n")
    return "- pattern-either:\n" + ind(text, 4)


def client_rule(rid: str, message: str, paths: str, groups: list[tuple[str, list[str], bool]],
                cmd_keys: list[str], typed: bool, exec_key: str | None, flat: bool, safe: str,
                confidence: str, likelihood: str, technology: str, refs: list[str]) -> str:
    """groups: (comment, event keys, whether the matcher narrows the hook)."""
    branches = ""
    for comment, events, narrows in groups:
        body = "- pattern-either:\n" + "".join(
            f"    - pattern-inside: '\"{e}\": [...]'\n" for e in events)
        body += client_handler(cmd_keys, typed, exec_key)
        if narrows:
            body += client_matcher(cmd_keys, flat, safe)
        branches += "".join(f"# {line}\n" for line in comment.split("\n")) + "- patterns:\n" + ind(body, 4)
    return f"""rules:
  - id: {rid}
{GEN_NOTE}    languages: [json]
    severity: ERROR
{message}{paths}    # Hooks that run a script, and prompt, agent, http, and mcp_tool hooks, decide at run time
    # and are left alone; agent-hook-runs-local-script reports repo scripts.
    patterns:
      - pattern-either:
{ind(branches, 10)}      - focus-metavariable: $OUT
{metadata("agent-config", confidence, technology, refs, likelihood)}"""


CODEX_REFS = [
    "https://developers.openai.com/codex/hooks",
    "https://github.com/openai/codex/blob/rust-v0.164.0/codex-rs/hooks/src/events/permission_request.rs",
    "https://github.com/openai/codex/blob/rust-v0.164.0/codex-rs/core/src/tools/approvals.rs",
    "https://github.com/openai/codex/blob/rust-v0.164.0/codex-rs/hooks/src/engine/discovery.rs",
    "https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md",
]


def codex_rule() -> str:
    paths = """    paths:
      include:
        # Codex reads hooks.json next to each config layer: ~/.codex/ and every .codex/ folder
        # from the repo root down. Plugin hooks/hooks.json files are scanned by
        # claude-settings-hook-auto-approves, which reads PermissionRequest the same way.
        - ".codex/hooks.json"
        # Plugin manifests with inline hooks: .codex-plugin/plugin.json, or plugin.json at the
        # plugin root (the open agent plugin format). Codex also reads
        # .claude-plugin/plugin.json, which claude-settings-hook-auto-approves scans.
        - "plugin.json"
      exclude:
        - ".claude-plugin/plugin.json"
"""
    groups = [("Codex answers the approval with a PermissionRequest allow; a PreToolUse allow\n"
               "only rewrites the input.", ["PermissionRequest"], True)]
    return client_rule("codex-hook-auto-approves", CODEX_MESSAGE, paths, groups,
                       ["command", "commandWindows"], True, None, False, SAFE,
                       "HIGH", "LOW", "[codex]", CODEX_REFS)


# A string in TOML: basic (with escapes) or literal.
TOML_STR = r"""(?: " (?: [^"\\\n] | \\. )*+ " | ' [^'\n]*+ ' )"""
# A matcher = "<read-only tools>" key.
TOML_SAFE_MATCHER = r"\b matcher [\x20\t]*+ = [\x20\t]*+ [\"'] " + SAFE_MATCHER + r" [\"']"


def codex_toml_rule() -> str:
    # One range per [[hooks.PermissionRequest]] group whose matcher reaches more than read-only
    # tools, through its [[hooks.PermissionRequest.hooks]] handler tables.
    tables = rf"""(?xm)
(?(DEFINE)
  {SAFE}
  (?<pr> [\x20\t]*+ hooks [\x20\t]*+ \. [\x20\t]*+ ["']? PermissionRequest ["']? [\x20\t]*+ )
  (?<line> (?! [\x20\t]*+ \[ ) (?: [^\n]*+ \n | [^\n]++ \z ) )
)
^ [\x20\t]*+ \[\[ (?&pr) \]\] [^\n]*+ \n
(?! (?&line)*? [\x20\t]*+ {TOML_SAFE_MATCHER} [\x20\t]*+ (?: \#[^\n]*+ )? $ )
(?&line)*+
(?: [\x20\t]*+ \[\[ (?&pr) \. [\x20\t]*+ hooks [\x20\t]*+ \]\] [^\n]*+ (?: \n (?&line)*+ | \z ) )*+"""
    # One range per inline PermissionRequest array: under [hooks], or hooks.PermissionRequest
    # at the top level, through its entry lines.
    inline = rf"""(?xm)
(?(DEFINE)
  (?<entry> (?! [\x20\t]*+ (?: \[ | [\w"'-]++ [\x20\t]*+ = ) ) (?: [^\n]*+ \n | [^\n]++ \z ) )
)
(?:
    ^ [\x20\t]*+ \[ [\x20\t]*+ hooks [\x20\t]*+ \] [^\n]*+ \n (?: (?! [\x20\t]*+ \[ ) [^\n]*+ \n )*? [\x20\t]*+
  | ^ [\x20\t]*+ hooks [\x20\t]*+ \. [\x20\t]*+
)
\K ["']? PermissionRequest ["']? [\x20\t]*+ = [\x20\t]*+ \[ [^\n]*+ (?: \n (?&entry)*+ )?"""
    # A command line in that range, not commented out. TOML 1.0 inline tables sit on one line,
    # so an inline entry that names only read-only tools as its matcher is left alone.
    command = rf"""(?xm)
(?(DEFINE)
  {SAFE}
)
^ (?! [\x20\t]*+ \# ) (?! [^\n]*? {TOML_SAFE_MATCHER} )
[^\n\#]*? (?<![\w-]) command (?:Windows)? [\x20\t]*+ = [\x20\t]*+ \K (?<CMD> {TOML_STR} )"""
    return f"""rules:
  - id: codex-hook-auto-approves-toml
{GEN_NOTE}    # Regex, not a parser: OpenGrep has no TOML language. TOML comments start with #.
    languages: [regex]
    severity: ERROR
{CODEX_MESSAGE}    paths:
      include:
        # Codex reads [hooks] tables from ~/.codex/config.toml and every .codex/config.toml from
        # the repo root down (profile files are read only from $CODEX_HOME).
        - ".codex/config.toml"
    patterns:
      - pattern-either:
          # [[hooks.PermissionRequest]] groups and their [[hooks.PermissionRequest.hooks]]
          # handlers, when the group's matcher reaches more than read-only tools.
          - pattern-regex: |-
{ind(tables, 14)}
          # Inline tables: PermissionRequest = [{{ matcher = ..., hooks = [{{ ... }}] }}] under
          # [hooks], or hooks.PermissionRequest = [...].
          - pattern-regex: |-
{ind(inline, 14)}
      - pattern-regex: |-
{ind(command, 10)}
      # The command only prints a fixed allow.
{ind(mvr("$CMD", COMMAND_REGEX), 6)}{metadata("agent-config", "HIGH", "[codex]", CODEX_REFS, "LOW")}"""


COPILOT_PATHS = """    paths:
      include:
        # Repository hook files (Copilot CLI, the cloud agent, and VS Code agent hooks).
        - ".github/hooks/*.json"
        # Inline hooks in repository and user settings.
        - ".github/copilot/settings.json"
        - ".github/copilot/settings.local.json"
        - ".copilot/settings.json"
        # User hook files (~/.copilot/hooks/), in dotfiles repositories.
        - ".copilot/hooks/*.json"
        # Copilot CLI plugins keep hooks in a hooks.json next to plugin.json. This also scans
        # Claude Code plugins' hooks/hooks.json, which Copilot CLI and VS Code load as well, so
        # a fixed allow there is reported by claude-settings-hook-auto-approves too (a glob
        # that excluded hooks/hooks.json would drop .github/hooks/hooks.json). Other clients'
        # hooks.json files are left to their own rules.
        - "hooks.json"
      exclude:
        - ".codex/hooks.json"
        - ".cursor/hooks.json"
        - ".devin/hooks.json"
        - ".windsurf/hooks.json"
"""


def copilot_rule() -> str:
    groups = [
        ("preToolUse: Copilot CLI reads the matcher, but VS Code drops it, so any matcher counts.",
         ["preToolUse", "PreToolUse"], False),
        ("permissionRequest (Copilot CLI): the entry's matcher reaches more than read-only tools.",
         ["permissionRequest", "PermissionRequest"], True),
    ]
    return client_rule("copilot-hook-auto-approves", COPILOT_MESSAGE, COPILOT_PATHS, groups,
                       ["bash", "powershell", "command"], False, "exec", True, COPILOT_SAFE,
                       "HIGH", "MEDIUM", "[copilot-cli, github-copilot, vscode]", [
                           "https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-hooks-reference",
                           "https://github.com/github/copilot-cli/blob/main/changelog.md",
                           "https://code.visualstudio.com/docs/copilot/customization/hooks",
                           "https://github.com/microsoft/vscode/blob/1.143.1/src/vs/workbench/contrib/chat/browser/tools/languageModelToolsService.ts",
                           "https://github.com/microsoft/vscode/blob/1.143.1/src/vs/workbench/contrib/chat/common/promptSyntax/hookSchema.ts",
                           "https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md"])


def devin_rule() -> str:
    paths = """    paths:
      include:
        # Devin CLI: hooks.v1.json is the hooks object itself; config.json has a "hooks" key.
        # Devin also reads .claude/settings.json, which claude-settings-hook-auto-approves scans.
        - ".devin/hooks.v1.json"
        - ".devin/config.json"
        - ".devin/config.local.json"
"""
    groups = [("Devin answers a permission request with a PermissionRequest approve.",
               ["PermissionRequest"], True)]
    return client_rule("devin-hook-auto-approves", DEVIN_MESSAGE, paths, groups,
                       ["command"], True, None, False, SAFE,
                       "MEDIUM", "MEDIUM", "[devin-cli]", [
                           "https://docs.devin.ai/cli/extensibility/hooks/overview",
                           "https://docs.devin.ai/cli/extensibility/hooks/lifecycle-hooks",
                           "https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md"])


# ---- skill, command, and subagent frontmatter ------------------------------------------------

# The same list as agent-frontmatter-command-runs-local-script's (build.py SHARED_PATHS checks it).
FM_PATHS = ["SKILL.md", ".claude/agents/**", ".claude/commands/**", "commands/**/*.md"]
# opencode and Kilo Code folders, which Claude Code never reads (their plural commands/ dirs
# would otherwise match commands/**/*.md); agent-skill-load-time-shell-opencode covers them.
FM_EXCLUDE = [".opencode/**", ".kilo/**", ".kilocode/**"]


def fm_rule() -> str:
    paths = "".join(f'        - "{p}"\n' for p in FM_PATHS)
    excludes = "".join(f'        - "{p}"\n' for p in FM_EXCLUDE)
    return f"""rules:
  - id: claude-frontmatter-hook-auto-approves
{GEN_NOTE}    languages: [generic]
    severity: ERROR
{FM_MESSAGE}    # Frontmatter hooks use the settings-file format. Plugin subagents ignore hooks, so a
    # plugin's agents/ folder is left out.
    paths:
      include:
{paths}      # opencode and Kilo Code folders: Claude Code never reads them, and the plural commands/
      # dirs under them would otherwise match commands/**/*.md. agent-skill-load-time-shell-opencode
      # covers their ``!`cmd` `` injection.
      exclude:
{excludes}    patterns:
      # The frontmatter: from a leading --- line to the next --- line.
      - pattern-regex: \\A(?:\\x{{FEFF}})?---[ \\t]*\\r?\\n(?s:.*?)\\r?\\n---[ \\t]*(?:\\r?\\n|\\z)
      # Its top-level hooks: block, parsed alone so that another key a YAML parser rejects
      # (a description with ": " in it) doesn't hide the hooks or break other rules' matches.
      - pattern-regex: (?m)^(?<FM>hooks[ \\t]*:[^\\r\\n]*\\r?\\n(?:(?:[ \\t]+[^\\r\\n]*|-[ \\t][^\\r\\n]*|\\#[^\\r\\n]*|[ \\t]*)\\r?\\n)*)
      - metavariable-pattern:
          metavariable: $FM
          language: yaml
          patterns:
            - pattern-either:
                - pattern-inside: |
                    PreToolUse: $EV
                - pattern-inside: |
                    PermissionRequest: $EV
            - pattern-either:
                # Shell form: the command line prints the decision and nothing in it could
                # decide otherwise.
                - patterns:
                    - pattern: |
                        command: $OUT
                    - pattern-not-inside: |
                        ...
                        args: $ARGS
                        ...
{ind(mvr("$OUT", COMMAND_REGEX), 20)}                    - focus-metavariable: $OUT
                # Exec form: command: echo (or printf) with the decision as an argument.
                - patterns:
                    - pattern-inside: |
                        ...
                        command: $PROG
                        ...
                    - pattern-inside: |
                        ...
                        args: $ARGS
                        ...
                    - metavariable-regex:
                        metavariable: $PROG
                        regex: ^["']?(?:/(?:usr/)?bin/)?(?:echo|printf)["']?$
                    - pattern: $OUT
{ind(mvr("$OUT", YAML_ARG_REGEX), 20)}                    - focus-metavariable: $OUT
            # A handler's `if` filter keeps the hook quiet only when it narrows the call; a Bash
            # filter doesn't (tested on Claude Code 2.1.310, 2026-10-24).
            - pattern-either:
                - patterns:
                    - pattern-inside: |
                        ...
                        type: $TYPE
                        ...
                    - pattern-not-inside: |
                        ...
                        if: $IF
                        ...
                - patterns:
                    - pattern-inside: |
                        ...
                        if: $IFV
                        ...
{ind(mvr("$IFV", IF_REGEX), 20)}            - pattern-either:
                # A matcher group with no matcher: every tool. The group's hooks value is the
                # handler list; the frontmatter's own hooks key holds events.
                - patterns:
                    - pattern-inside: |
                        hooks: $H
                    - metavariable-regex:
                        metavariable: $H
                        regex: ^\\s*+[-\\[]
                    - pattern-not-inside: |
                        ...
                        matcher: $ANY
                        ...
                - patterns:
                    - pattern-inside: |
                        ...
                        matcher: $M
                        ...
{ind(mvr("$M", matcher_regex(True)), 20)}      - focus-metavariable: $OUT
{metadata("agent-config", "HIGH", "[claude-code]", [
        "https://code.claude.com/docs/en/hooks",
        "https://code.claude.com/docs/en/skills",
        "https://code.claude.com/docs/en/sub-agents",
        "https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM03_ExcessiveAgency.md"])}"""


def render() -> dict[Path, str]:
    """The rule files and the content this script generates for each."""
    return {PY_RULE: py_rule(), TS_RULE: ts_rule(), JSON_RULE: json_rule(), FM_RULE: fm_rule(),
            CODEX_RULE: codex_rule(), CODEX_TOML_RULE: codex_toml_rule(), COPILOT_RULE: copilot_rule(),
            DEVIN_RULE: devin_rule()}


def main() -> int:
    for path, content in render().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text() != content:
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
