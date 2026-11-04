#!/usr/bin/env python3
"""Generate the mcp-tool-description-hidden-unicode rules (Python and TypeScript) from their siblings.

The rules flag invisible Unicode in the text an MCP client hands the model as a tool's
description: tag characters, bidi controls, zero-width characters, variation-selector runs, and a
stray byte-order mark. Two siblings already own the pieces, so this script copies them instead of
keeping hand-synced copies:

- the characters and thresholds: the `hidden`, `strong` and `flag` groups of
  agent-instruction-hidden-unicode, between its "hidden Unicode characters" markers (build.py
  SHARED_REGEX also checks the copies);
- the description surfaces: the first entries of `patterns` in mcp-tool-description-instructions
  (+ -ts), which bind the description text as $D (build.py SHARED_BLOCKS also checks them).

What this script adds is the escape forms. A description written in source as "\\u200b" or
"\\U000E0041" (Python) or "\\u{E0041}" / "\\uDB40\\uDC41" (JavaScript, and what esbuild writes for
every non-ASCII character by default) reaches the model as the same invisible character, so an
escape counts as the character it decodes to, with the same thresholds. An escape that doesn't
decode does not count: a doubled backslash ("\\\\u200b"), a Python raw string, or String.raw.
ESCAPES below lists the same code points as the `hidden` group; render() fails when the two
disagree, so a change to the sibling's character set has to be made here too.

Edit this script (or the sibling rules), not the generated rule files. scripts/build.py
regenerates them, and scripts/build.py --check fails when a rule file differs from what this
script produces.

Usage:
    python3 scripts/gen_mcp_hidden_unicode.py    # rewrite the rule files
"""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CHARS_RULE = ROOT / "rules" / "agent-config" / "instruction-integrity" / "agent-instruction-hidden-unicode.yaml"
PY_SURFACE_RULE = ROOT / "rules" / "python" / "injection" / "mcp-tool-description-instructions.yaml"
TS_SURFACE_RULE = ROOT / "rules" / "typescript" / "injection" / "mcp-tool-description-instructions-ts.yaml"
PY_RULE = ROOT / "rules" / "python" / "injection" / "mcp-tool-description-hidden-unicode.yaml"
TS_RULE = ROOT / "rules" / "typescript" / "injection" / "mcp-tool-description-hidden-unicode-ts.yaml"

GROUP = "hidden Unicode characters"

# ---- the escape table ------------------------------------------------------------------------

STRONG, WEAK = "strong", "weak"
# Lookbehinds copied from the sibling's `strong` group: a character that is strong only outside a
# script that uses it. render() checks that each still appears there.
NOT_AFTER_SPACELESS = r"(?<![\p{Thai}\p{Lao}\p{Khmer}\p{Myanmar}\p{Han}\p{Hiragana}\p{Katakana}\p{Tibetan}])"
NOT_AFTER_NON_LATIN = r"(?<! (?=[\p{L}\p{M}]) \P{Latin} )"
NOT_AFTER_MONGOLIAN = r"(?<!\p{Mongolian})"
NOT_AFTER_KHMER = r"(?<!\p{Khmer})"
# The same contexts when the letter before is itself an escape (a bundler escapes all of them):
# BMP blocks of the scripts above, approximated by range ("non-Latin letter" is U+0370 and up,
# leaving out the Latin extension blocks).
ESCAPED_CONTEXT = {
    NOT_AFTER_SPACELESS: [(0x0E00, 0x0FFF), (0x1000, 0x109F), (0x1780, 0x17FF), (0x3040, 0x30FF),
                          (0x3400, 0x4DBF), (0x4E00, 0x9FFF), (0xF900, 0xFAFF)],
    NOT_AFTER_NON_LATIN: [(0x0370, 0x1DBF), (0x1F00, 0x1FFF), (0x2C00, 0x2C5F), (0x2C80, 0x2DFF),
                          (0x3040, 0x9FFF), (0xA000, 0xA6FF), (0xA800, 0xABFF), (0xAC00, 0xD7FF),
                          (0xFB1D, 0xFDFF), (0xFE70, 0xFEFC)],
    NOT_AFTER_MONGOLIAN: [(0x1800, 0x18AF)],
    NOT_AFTER_KHMER: [(0x1780, 0x17FF), (0x19E0, 0x19FF)],
}

# (first, last, kind, context lookbehind for a strong character, Python \N{...} names).
# Names are matched case-insensitively, as Python does, and include the NameAliases.txt
# abbreviations Python accepts (\N{ZWSP}, \N{RLO}). A byte-order mark is strong anywhere in a
# description; the sibling exempts only offset 0 of a file.
ESCAPES = [
    (0x00AD, 0x00AD, WEAK, None, r"SOFT[ ]HYPHEN | SHY"),
    (0x034F, 0x034F, WEAK, None, r"COMBINING[ ]GRAPHEME[ ]JOINER | CGJ"),
    (0x061C, 0x061C, WEAK, None, r"ARABIC[ ]LETTER[ ]MARK | ALM"),
    (0x115F, 0x1160, WEAK, None, r"HANGUL[ ]CHOSEONG[ ]FILLER | HANGUL[ ]JUNGSEONG[ ]FILLER"),
    (0x17B4, 0x17B5, STRONG, NOT_AFTER_KHMER, r"KHMER[ ]VOWEL[ ]INHERENT[ ]A[QA]"),
    (0x180B, 0x180F, STRONG, NOT_AFTER_MONGOLIAN,
     r"MONGOLIAN[ ]FREE[ ]VARIATION[ ]SELECTOR[ ](?:ONE|TWO|THREE|FOUR) | FVS[1-4]"
     r" | MONGOLIAN[ ]VOWEL[ ]SEPARATOR | MVS"),
    (0x200B, 0x200B, STRONG, NOT_AFTER_SPACELESS, r"ZERO[ ]WIDTH[ ]SPACE | ZWSP"),
    (0x200C, 0x200C, STRONG, NOT_AFTER_NON_LATIN, r"ZERO[ ]WIDTH[ ]NON-JOINER | ZWNJ"),
    (0x200D, 0x200F, WEAK, None,
     r"ZERO[ ]WIDTH[ ]JOINER | ZWJ | LEFT-TO-RIGHT[ ]MARK | LRM | RIGHT-TO-LEFT[ ]MARK | RLM"),
    (0x202A, 0x202E, STRONG, None,
     r"(?:LEFT-TO-RIGHT|RIGHT-TO-LEFT)[ ](?:EMBEDDING|OVERRIDE) | POP[ ]DIRECTIONAL[ ]FORMATTING"
     r" | LRE | RLE | PDF | LRO | RLO"),
    (0x2060, 0x206F, STRONG, None,
     r"WORD[ ]JOINER | WJ | FUNCTION[ ]APPLICATION | INVISIBLE[ ](?:TIMES|SEPARATOR|PLUS)"
     r" | (?:LEFT-TO-RIGHT|RIGHT-TO-LEFT|FIRST[ ]STRONG|POP[ ]DIRECTIONAL)[ ]ISOLATE | LRI | RLI | FSI | PDI"
     r" | (?:INHIBIT|ACTIVATE)[ ](?:SYMMETRIC[ ]SWAPPING|ARABIC[ ]FORM[ ]SHAPING) | NATIONAL[ ]DIGIT[ ]SHAPES"
     r" | NOMINAL[ ]DIGIT[ ]SHAPES"),
    (0x3164, 0x3164, WEAK, None, r"HANGUL[ ]FILLER"),
    (0xFE00, 0xFE0F, WEAK, None, r"VARIATION[ ]SELECTOR-\d++ | VS\d++"),
    (0xFEFF, 0xFEFF, STRONG, None, r"ZERO[ ]WIDTH[ ]NO-BREAK[ ]SPACE | BYTE[ ]ORDER[ ]MARK | BOM | ZWNBSP"),
    (0xFFA0, 0xFFA0, WEAK, None, r"HALFWIDTH[ ]HANGUL[ ]FILLER"),
    (0xFFF0, 0xFFF8, STRONG, None, None),
    (0x1BCA0, 0x1BCA3, STRONG, None,
     r"SHORTHAND[ ]FORMAT[ ](?:LETTER[ ]OVERLAP|CONTINUING[ ]OVERLAP|DOWN[ ]STEP|UP[ ]STEP)"),
    (0x1D173, 0x1D17A, STRONG, None, r"MUSICAL[ ]SYMBOL[ ](?:BEGIN|END)[ ](?:BEAM|TIE|SLUR|PHRASE)"),
    (0xE0000, 0xE00FF, STRONG, None, r"LANGUAGE[ ]TAG | CANCEL[ ]TAG | TAG[ ][A-Z0-9 -]++"),
    (0xE0100, 0xE01EF, WEAK, None, None),
    (0xE01F0, 0xE0FFF, STRONG, None, None),
]

# ---- hex ranges as regexes -------------------------------------------------------------------

HEX = "0123456789ABCDEF"
ANY = "[0-9a-fA-F]"


def any_hex(n: int) -> str:
    return "" if n == 0 else ANY if n == 1 else f"{ANY}{{{n}}}"


def digit_class(a: int, b: int) -> str:
    """Hex digits a..b, in either case."""
    if a == 0 and b == 15:
        return ANY
    if a == b:
        c = HEX[a]
        return c if c.isdigit() else f"[{c.lower()}{c}]"
    parts = []
    if a <= 9:
        hi = min(b, 9)
        parts.append(HEX[a] if a == hi else f"{HEX[a]}-{HEX[hi]}")
    if b >= 10:
        lo = max(a, 10)
        span = (lambda s: s[lo] if lo == b else f"{s[lo]}-{s[b]}")
        parts.append(span(HEX.lower()) + span(HEX))
    return "[" + "".join(parts) + "]"


def hex_range(lo: int, hi: int, width: int) -> str:
    """A regex for the width-digit hex numbers lo..hi."""
    if width == 0:
        return ""
    if lo == 0 and hi == 16 ** width - 1:
        return any_hex(width)
    p = 16 ** (width - 1)
    a, b, ra, rb = lo // p, hi // p, lo % p, hi % p
    if a == b:
        return digit_class(a, a) + hex_range(ra, rb, width - 1)
    alts = []
    if ra:
        alts.append(digit_class(a, a) + hex_range(ra, p - 1, width - 1))
        a += 1
    last = None
    if rb != p - 1:
        last = digit_class(b, b) + hex_range(0, rb, width - 1)
        b -= 1
    if a <= b:
        alts.append(digit_class(a, b) + any_hex(width - 1))
    if last:
        alts.append(last)
    return alts[0] if len(alts) == 1 else "(?:" + "|".join(alts) + ")"


def alt(parts: list[str]) -> str:
    return parts[0] if len(parts) == 1 else "(?:" + " | ".join(parts) + ")"


def merge(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    out: list[list[int]] = []
    for lo, hi in sorted(ranges):
        if out and lo <= out[-1][1] + 1:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return [(lo, hi) for lo, hi in out]


def escape(ranges: list[tuple[int, int]], names: list[str], lang: str) -> str:
    """Every escape that decodes to a character in ranges, in Python ("py") or JavaScript source."""
    x, u4, u8, brace, pairs = [], [], [], [], {}
    for lo, hi in merge(ranges):
        if hi <= 0xFF:
            x.append(hex_range(lo, hi, 2))
        if hi <= 0xFFFF:
            u4.append(hex_range(lo, hi, 4))
        u8.append(hex_range(lo, hi, 8))
        width = len(f"{hi:X}")
        assert len(f"{lo:X}") == width, (lo, hi)
        brace.append(hex_range(lo, hi, width))
        # UTF-16 surrogate pairs, one high surrogate at a time; highs sharing a low range merge.
        cp = max(lo, 0x10000)
        while cp <= hi:
            high, low = divmod(cp - 0x10000, 0x400)
            last = min(hi - 0x10000, high * 0x400 + 0x3FF) % 0x400
            pairs.setdefault((0xDC00 + low, 0xDC00 + last), []).append((0xD800 + high, 0xD800 + high))
            cp = 0x10000 + high * 0x400 + last + 1
    # Octal (Python, and JavaScript outside strict code): \255 is U+00AD; \0255 is U+0015 and "5".
    octal = []
    for lo, hi in merge(ranges):
        for cp in range(lo, min(hi, 0o377) + 1):
            digits = f"{cp:o}"
            octal += [d if len(d) == 3 else d + "(?![0-7])" for d in (digits.zfill(w) for w in range(len(digits), 4))]
    forms = []
    if octal:
        forms.append(alt(octal))
    if x:
        forms.append("x" + alt(x))
    if lang == "py":
        if u4:
            forms.append("u" + alt(u4))
        forms.append("U" + alt(u8))
        if names:
            forms.append(r"N\{(?i:" + " | ".join(names) + r")\}")
    else:
        u = u4 + [alt([hex_range(a, b, 4) for a, b in merge(highs)]) + r"\\u" + hex_range(lo, hi, 4)
                  for (lo, hi), highs in sorted(pairs.items(), key=lambda kv: min(kv[1]))]
        forms.append("u" + alt(u))
        forms.append(r"u\{0*+" + alt(brace) + r"\}")
    # The scan consumes escaped backslashes in pairs, so "\\\\u200b" (a backslash and the text u200b)
    # never reaches this.
    return r"\\" + alt(forms)


def escape_defines(lang: str) -> str:
    hidden = escape([(lo, hi) for lo, hi, *_ in ESCAPES], [n for *_, n in ESCAPES if n], lang)
    plain = [(lo, hi, n) for lo, hi, kind, ctx, n in ESCAPES if kind == STRONG and ctx is None]
    strong = [escape([(lo, hi) for lo, hi, _ in plain], [n for *_, n in plain if n], lang)]
    contexts: dict[str, list[tuple[int, int, str | None]]] = {}
    for lo, hi, kind, ctx, n in ESCAPES:
        if kind == STRONG and ctx:
            contexts.setdefault(ctx, []).append((lo, hi, n))
    for ctx, entries in contexts.items():
        letters = alt([hex_range(lo, hi, 4) for lo, hi in merge(ESCAPED_CONTEXT[ctx])])
        after = rf"(?<! \\u{letters} | \\U0000{letters} )" if lang == "py" else rf"(?<! \\u{letters} )"
        strong.append(ctx + " " + after + " " + escape([(lo, hi) for lo, hi, _ in entries],
                                                      [n for *_, n in entries if n], lang))
    if lang == "py":
        flag_emoji = r"\x{1F3F4} | \\U0001[fF]3[fF]4"
        forms = "\\xAD, \\u200B, \\U000E0041, and \\N{...} names (with their aliases)"
    else:
        flag_emoji = r"\x{1F3F4} | \\u\{1[fF]3[fF]4\} | \\u[dD]83[cC]\\u[dD][fF][fF]4"
        forms = "\\xAD, \\u200B, \\u{E0041}, and UTF-16 surrogate pairs (\\uDB40\\uDC41)"
    tag_letter = escape([(0xE0061, 0xE007A)], [r"TAG[ ]LATIN[ ]SMALL[ ]LETTER[ ][A-Z]"], lang)
    tag_digit = escape([(0xE0030, 0xE0039)], [r"TAG[ ]DIGIT[ ][A-Z]++"], lang)
    cancel = escape([(0xE007F, 0xE007F)], [r"CANCEL[ ]TAG"], lang)
    lines = [
        f"# The same characters written as escapes: {forms}.",
        f"(?<ehidden> {hidden} )",
        "(?<estrong>",
        "    " + "\n  | ".join(strong) + " )",
        "# A subdivision flag (England, Scotland, Wales) written as escapes.",
        f"(?<etagletter> {tag_letter} )",
        f"(?<etagdigit> {tag_digit} )",
        f"(?<eflag> (?<= {flag_emoji} )",
        "  (?: (?&etagletter){2} | (?&etagdigit){3} ) (?: (?&etagletter) | (?&etagdigit) ){1,4}",
        f"  {cancel} (?!(?&h)) )",
    ]
    return "\n".join(lines)


# ---- reading the siblings --------------------------------------------------------------------

def char_block() -> str:
    """The sibling's character groups, markers included, dedented."""
    text = CHARS_RULE.read_text()
    m = re.search(rf"^([ \t]*)# --- {re.escape(GROUP)} \(begin\).*?# --- {re.escape(GROUP)} \(end\) ---\n",
                  text, re.S | re.M)
    if not m:
        raise SystemExit(f"{CHARS_RULE.relative_to(ROOT)}: no '{GROUP}' markers")
    return textwrap.dedent(m.group(0))


def ranges_in(cls: str) -> list[tuple[int, int]]:
    out = []
    for m in re.finditer(r"\\x\{([0-9A-F]+)\}(?:-\\x\{([0-9A-F]+)\})?", cls):
        lo = int(m.group(1), 16)
        out.append((lo, int(m.group(2), 16) if m.group(2) else lo))
    return out


def hidden_class(block: str) -> str:
    """The inside of the sibling's `hidden` character class."""
    m = re.search(r"\(\?<hidden>\s*\[([^\n]*)\]", block)
    if not m:
        raise SystemExit("gen_mcp_hidden_unicode.py: can't find the hidden group")
    return m.group(1)


def check_table(block: str) -> None:
    """ESCAPES must describe the same characters as the sibling's literal groups."""
    hidden = re.search(r"\(\?<hidden>\s*(\[[^\n]*\])", block)
    strong = re.search(r"\(\?<strong>(.*?)\(\?<flag>", block, re.S)
    if not hidden or not strong:
        raise SystemExit("gen_mcp_hidden_unicode.py: can't find the hidden and strong groups")
    problems = []
    if merge(ranges_in(hidden.group(1))) != merge([(lo, hi) for lo, hi, *_ in ESCAPES]):
        problems.append("the hidden group's code points differ from ESCAPES")
    # Context-free strong classes are the strong group's lines that are a class on their own.
    plain = [ranges_in(line) for line in strong.group(1).splitlines()
             if re.fullmatch(r"\s*(?:\|\s*)?\[[^\]]*\]\s*", line)]
    want = merge([(lo, hi) for lo, hi, kind, ctx, _ in ESCAPES if kind == STRONG and ctx is None])
    got = merge([r for rs in plain for r in rs] + [(0xFEFF, 0xFEFF)])
    if got != want:
        problems.append("the strong group's context-free classes differ from ESCAPES")
    for ctx in (NOT_AFTER_SPACELESS, NOT_AFTER_NON_LATIN, NOT_AFTER_MONGOLIAN, NOT_AFTER_KHMER):
        if ctx not in strong.group(1):
            problems.append(f"the strong group no longer has {ctx}")
    if problems:
        raise SystemExit(f"{CHARS_RULE.relative_to(ROOT)} and scripts/gen_mcp_hidden_unicode.py disagree: "
                         + "; ".join(problems) + ". Update ESCAPES to match.")


def surface(path: Path, through: str | None) -> tuple[str, int]:
    """The leading `patterns` entries of a sibling, as text, and how many entries that is."""
    lines = path.read_text().splitlines(keepends=True)
    start = lines.index("    patterns:\n") + 1
    end = next(i for i in range(start, len(lines)) if lines[i].startswith("      - metavariable-regex:"))
    if through:
        end = next(i for i in range(start, end + 1) if lines[i].rstrip("\n") == through) + 1
    text = "".join(lines[start:end])
    entries = yaml.safe_load(textwrap.dedent(text))
    body = yaml.safe_load(path.read_text())["rules"][0]["patterns"]
    if entries != body[:len(entries)]:
        raise SystemExit(f"gen_mcp_hidden_unicode.py: misread the patterns of {path.relative_to(ROOT)}")
    return text, len(entries)


# ---- the rules -------------------------------------------------------------------------------

# A literal that doesn't process escapes, consumed whole: only characters count inside it. It
# starts at its opening quote (the scan stops at every quote); Python's prefix is checked behind.
PY_RAWLIT = r"""(?<= (?<![\w"'])[rR] | (?<![\w"'])[rR][bBfF] | (?<![\w"'])[bBfF][rR] ) (?:
      Q3 (?: [^"CLS]++ | "(?!"") | (?!(?&litrun)) (?&hidden)++ )*+ Q3
    | A3 (?: [^'CLS]++ | '(?!'') | (?!(?&litrun)) (?&hidden)++ )*+ A3
    | " (?: [^"\\\nCLS]++ | \\[^\nCLS] | (?!(?&litrun)) (?&hidden)++ )*+ "
    | ' (?: [^'\\\nCLS]++ | \\[^\nCLS] | (?!(?&litrun)) (?&hidden)++ )*+ ' )""".replace(
    "Q3", '"' * 3).replace("A3", "'" * 3)
JS_RAWLIT = r"""(?<= (?<![\w$.])String\.raw )
    ` (?: [^`\\CLS]++ | \\[^CLS] | (?!(?&litrun)) (?&hidden)++ )*+ `"""
QUOTES = {"py": "\"'", "js": "`"}


def define(lang: str) -> str:
    block = char_block()
    check_table(block)
    return "\n".join([block.rstrip("\n"), escape_defines(lang),
                      "# One character of a run, as itself or as an escape.",
                      "(?<h> (?&hidden) | (?&ehidden) )",
                      "# At the start of a run: one that holds a strong character or is at least three long",
                      "# and isn't a subdivision flag, counting characters only or escapes too.",
                      r"(?<litrun> (?!(?&flag)) (?= (?&hidden){3} | (?&hidden)*? (?: (?&strong) | \x{FEFF} ) ) )",
                      r"(?<anyrun> (?! (?&flag) | (?&eflag) )",
                      r"  (?= (?&h){3} | (?&h)*? (?: (?&strong) | (?&estrong) | \x{FEFF} ) ) )",
                      "# A literal that doesn't process escapes (Python raw strings, String.raw), whole.",
                      "(?<rawlit> " + (PY_RAWLIT if lang == "py" else JS_RAWLIT).replace("CLS", hidden_class(block))
                      + " )"])


def regex(lang: str) -> str:
    cls = hidden_class(char_block())
    q = QUOTES[lang]
    return "\n".join([
        "(?x)",
        "(?(DEFINE)",
        textwrap.indent(define(lang), "  "),
        ")",
        "# The first run that counts. The scan is possessive (it never backtracks, so long descriptions",
        "# stay under PCRE's limits): raw literals whole, other text in chunks up to a backslash, a",
        "# quote, or a hidden character, an escaped backslash as a pair (so the text after it isn't",
        "# read as an escape), and runs that don't count whole.",
        r"\A (?: (?&rawlit) | [^\\" + q + cls + r"]++ | [" + q + r"] | \\\\ | (?!(?&h)) \\ (?!\\)",
        r"  | (?!(?&anyrun)) (?&h)++ )*+ (?&anyrun)",
    ])


MESSAGE = """\
    message: >-
      This tool description (or an MCP prompt's or resource's, a parameter description, or the
      server instructions) contains invisible Unicode: tag characters (which the model reads as
      ASCII text that no editor, diff, or MCP client shows), bidirectional controls that display
      the text in a different order than the model reads it, zero-width characters, a run of
      variation selectors that can encode hidden bytes, or a byte-order mark, written as the
      characters themselves or as escapes that decode to them. MCP clients and agent frameworks
      put this text in the model's context as trusted, so a hidden instruction there steers
      every agent that loads the tool while the user approving it sees only the visible text
      (tool poisoning). Decode the text (print it with non-ASCII characters escaped, as Python's
      ascii() does) to see what it says, remove the characters, and if the server came from
      someone else, don't connect it until you know who added them. To mention such a character
      in a description, name it ("U+200B") or double the backslash.
"""

METADATA = """\
    metadata:
      category: security
      subcategory: [audit]
      pack-category: mcp-server
      owasp-llm:
        - "LLM01:2026 - Prompt Injection"
        - "LLM01:2025 - Prompt Injection"
      owasp-agentic:
        - "ASI04 - Agentic Supply Chain Vulnerabilities"
        - "ASI01 - Agent Goal Hijack"
      owasp-mcp:
        - "MCP03:2025 - Tool Poisoning"
      owasp-aisvs:
        - "v1.01-C10.4.2 - Schema, Message, and Input Validation"
      mitre-atlas:
        - "AML.T0011.002 - User Execution: Poisoned AI Agent Tool"
        - "AML.T0068 - LLM Prompt Obfuscation"
      cwe:
        - "CWE-1427: Improper Neutralization of Input Used for LLM Prompting"
        - "CWE-451: User Interface (UI) Misrepresentation of Critical Information"
      confidence: MEDIUM
      likelihood: MEDIUM
      impact: HIGH
      technology: [{technology}]
      references:
        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP03-2025%E2%80%93Tool-Poisoning.md
        - https://embracethered.com/blog/posts/2024/hiding-and-finding-text-with-unicode-tags/
        - https://trojansource.codes/
        - https://www.unicode.org/Public/18.0.0/ucd/DerivedCoreProperties.txt
{references}"""

HEADER = """\
# Generated by scripts/gen_mcp_hidden_unicode.py from agent-instruction-hidden-unicode (the
# characters) and {surface} (the description surfaces).
# Edit those rules, or the script, not this file.
rules:
  - id: {id}
"""


def rule(rule_id: str, surface_rule: Path, through: str | None, language: str,
         comment: str, extra: str, technology: str, references: str) -> str:
    surface_text, _ = surface(surface_rule, through)
    body = regex("py" if language == "[python]" else "js")
    return (HEADER.format(surface=surface_rule.stem, id=rule_id)
            + textwrap.indent(comment.strip("\n"), "    # ") .replace("    # \n", "    #\n") + "\n"
            + f"    languages: {language}\n"
            + "    severity: ERROR\n"
            + MESSAGE
            + "    patterns:\n"
            + surface_text
            + extra
            + "      - metavariable-regex:\n"
            + "          metavariable: $D\n"
            + "          regex: |-\n"
            + textwrap.indent(body, " " * 12) + "\n"
            + METADATA.format(technology=technology, references=references))


PY_COMMENT = """\
The text an MCP client shows the model for each tool, prompt, and resource, and the server's
instructions: the same surfaces as mcp-tool-description-instructions (MCP Python SDK v2.3.0
and v1.30.0, fastmcp 4.1.3, Claude Agent SDK 0.2.173 @tool), whose description is the
`description=` argument or else `fn.__doc__`, passed on unchanged. A finding is one per
description: a run of invisible characters that holds a strong one (tag characters, bidi
embeddings, overrides and isolates, ZWSP outside Thai and CJK text, ...) or is three or more
long, with the thresholds of agent-instruction-hidden-unicode, so emoji ZWJ sequences, a
single VS16, subdivision flags, and Persian ZWNJ stay quiet. Escapes ("\\u200b", "\\U000E0041",
"\\N{ZERO WIDTH SPACE}", octal "\\255") count as the character they decode to. In a raw string
they are text, judged literal by literal, so a raw piece doesn't hide the rest of a
concatenation. OpenGrep binds a docstring's text with "\\\\" already turned into one backslash,
so the pattern-not-regex drops a docstring whose source holds no hidden character and no escape
that decodes to one."""

TS_COMMENT = """\
JavaScript/TypeScript twin of mcp-tool-description-hidden-unicode: the same surfaces as
mcp-tool-description-instructions-ts (MCP TypeScript SDK v2.3.1 and 1.32.1, punkpeye fastmcp,
Claude Agent SDK tool(), Vercel AI SDK tool()); McpServer still lists descriptions unchanged in
SDK v2.4.0. Escapes count as the character they decode to: "\\u200b", "\\u{E0041}", octal
"\\255", and UTF-16 surrogate pairs ("\\uDB40\\uDC41"), which is how bundlers such as esbuild
write non-ASCII text by default, so a bundled server is covered too (OpenGrep's default ignore
list skips dist/ and vendor/ folders). String.raw text is not decoded, judged literal by literal."""

# OpenGrep binds a docstring's text with simple escapes processed (an escaped backslash becomes
# one backslash, \n a newline) but \u, \U, \x and \N{} left as written, so the text "\\u200b"
# reads like the escape "\u200b"; a raw docstring is also bound once without its quotes (and
# prefix). This drops, by its source text, a docstring (a string right after a line ending in
# ":", or after comments, and not continued by another string) that holds no hidden character
# and no escape that decodes to one.
DOC_END = r"""[ \t]*+ (?: \# [^\n]*+ )?+ (?: \n | \z )
              (?! (?: [ \t]*+ (?: \# [^\n]*+ )?+ \n )*+ [ \t]*+ [rRbBfFuU]{0,2}+ ["'] )"""
PY_DOCSTRING = r"""      # A docstring whose escapes don't decode (an escaped backslash, a raw or bytes docstring).
      - pattern-not-regex: |-
          (?x)
          (?(DEFINE)
{define}
          )
          (?m) ^ [^\n]*? : [ \t]*+ (?: \# [^\n]*+ )?+ \n (?: [ \t]*+ \# [^\n]*+ \n )*+ [ \t]*+ (?:
              (?: [rR][bBuU]?+ | [bBuU][rR] | [bB] ) (?:
                  Q3 \K (?: [^"CLS]++ | "(?!"") )*+ (?=Q3 END)
                | A3 \K (?: [^'CLS]++ | '(?!'') )*+ (?=A3 END)
                | "(?!") \K (?: [^"\\\nCLS]++ | \\[^\n] )*+ (?=" END)
                | '(?!') \K (?: [^'\\\nCLS]++ | \\[^\n] )*+ (?=' END) )
            | [uU]?+ (?:
                  Q3 \K (?: [^"\\CLS]++ | "(?!"") | (?!(?&ehidden)) \\[\s\S] )*+ (?=Q3 END)
                | A3 \K (?: [^'\\CLS]++ | '(?!'') | (?!(?&ehidden)) \\[\s\S] )*+ (?=A3 END)
                | "(?!") \K (?: [^"\\\nCLS]++ | (?!(?&ehidden)) \\[^\n] )*+ (?=" END)
                | '(?!') \K (?: [^'\\\nCLS]++ | (?!(?&ehidden)) \\[^\n] )*+ (?=' END) ) )
""".replace(" END", " " + DOC_END).replace("Q3", '"' * 3).replace("A3", "'" * 3)


def py_rule() -> str:
    extra = (PY_DOCSTRING.replace("{define}", textwrap.indent(define("py"), " " * 12))
             .replace("CLS", hidden_class(char_block())))
    return rule(
        "mcp-tool-description-hidden-unicode", PY_SURFACE_RULE, None, "[python]",
        PY_COMMENT, extra, "mcp, fastmcp, claude-agent-sdk",
        "        - https://github.com/modelcontextprotocol/python-sdk/blob/v2.3.0/src/mcp/server/mcpserver/tools/base.py\n")


def ts_rule() -> str:
    return rule(
        "mcp-tool-description-hidden-unicode-ts", TS_SURFACE_RULE,
        "      - focus-metavariable: $D", "[typescript, javascript]",
        TS_COMMENT, "", "mcp, fastmcp, claude-agent-sdk, vercel-ai-sdk",
        "        - https://github.com/modelcontextprotocol/typescript-sdk/blob/v2.4.0/packages/server/src/server/mcp.ts\n"
        "        - https://esbuild.github.io/api/#charset\n")


def render() -> dict[Path, str]:
    """The rule files and the content this script generates for each."""
    return {PY_RULE: py_rule(), TS_RULE: ts_rule()}


def main() -> int:
    for path, content in render().items():
        if not path.exists() or path.read_text() != content:
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
