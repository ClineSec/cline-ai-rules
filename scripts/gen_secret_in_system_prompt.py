#!/usr/bin/env python3
"""Generate secret-in-system-prompt (Python) and secret-in-system-prompt-ts from one set of regexes.

Both rules decide what looks like a secret the same way: a variable, setting, key, or env var
whose name ends in a credential word (SECRET_NAME below), or a string literal holding a
credential (the known formats and URL shapes that gen_mcp_plaintext_secret.py also uses). Only
the language scaffolding (sources, sanitizers, and the SDK calls that fill the system slot)
differs.

Edit this script, not the rule files. scripts/build.py regenerates them, and
scripts/build.py --check fails when a rule file differs from what this script produces.

Usage:
    python3 scripts/gen_secret_in_system_prompt.py    # rewrite the two rule files
"""

from __future__ import annotations

import sys
from pathlib import Path

from gen_mcp_plaintext_secret import DEFINE, EMBEDDED, SECRET_WORD
from gen_mcp_unpinned import mvr, paren_guard

ROOT = Path(__file__).resolve().parent.parent
PY_RULE = ROOT / "rules" / "python" / "secrets" / "secret-in-system-prompt.yaml"
TS_RULE = ROOT / "rules" / "typescript" / "secrets" / "secret-in-system-prompt-ts.yaml"

# ---- what a secret's name looks like -------------------------------------------------------

# Words that end a credential's name: SECRET_WORD (shared with the mcp-config-plaintext-secret
# rules) plus the names that only make sense in code. Matched at the end, after a word boundary
# (start, _ - ., or a camelCase hump), so OPENAI_API_KEY, stripeSecretKey and db_pass match,
# while MAX_TOKENS, TOKENIZER_PATH, TOKEN_LIMIT, CACHE_KEY, AWS_ACCESS_KEY_ID and bypass don't.
WORDS = rf"""
      {SECRET_WORD}
    | passwort | pwd | pass | passphrase
    | (?:signing|encryption|master|account|subscription|admin) [_-]?key
    | credentials? | creds
      # <provider>_KEY, a common short form for a provider API key.
    | (?:openai|anthropic|claude|gemini|google|groq|mistral|cohere|together|fireworks|deepseek
        |xai|perplexity|openrouter|replicate|hf|huggingface|pinecone|tavily|serper|serpapi
        |stripe|sendgrid|twilio|mailgun|slack|github|gitlab|aws|azure|elevenlabs|voyage|jina
        |firecrawl|langsmith|wandb) [_-]?key
      # Connection strings, which carry the database password.
    | (?:database|db|postgres(?:ql)?|pg|psql|mysql|mariadb|mssql|sql|mongo(?:db)?|redis|amqp
        |rabbitmq|broker|cosmos(?:db)?) [_-]?(?:url|uri|dsn)
    | dsn | conn(?:ection)?[_-]?str(?:ing)? | connstr
      # Chat webhooks embed their secret in the URL.
    | (?:slack|discord|teams) [_-]?webhook(?:[_-]?url)?
"""

# Words that make the name a flag, a check, or a count rather than the secret itself
# (is_secret, hasApiKey, check_password, max_password_length never reaches the end anyway).
NOT_FIRST = (r"is|has|use|uses|enable|enabled|disable|disabled|require|requires|required|should"
             r"|allow|needs?|show|check|verify|validate|reset|set|change|forgot|confirm|hashed"
             r"|hash|mask|masked|redact|redacted|min|max|num|count|total|len|length|missing|no")

# Qualifiers that make a *_TOKEN name a model or tokenizer token, a count, or a page cursor.
NOT_TOKEN = (r"max|min|num|total|prompt|completion|input|output|context|reasoning|thinking"
             r"|cached|cache|eos|bos|pad|padding|sep|separator|unk|unknown|cls|mask|start|end"
             r"|special|stop|next|prev|previous|page|pagination|continuation|cursor|sync|first"
             r"|last|new|seq|sequence|chat|tool|bot|eot|im|split|default|progress|cancel"
             r"|cancellation|abort|idempotency|resume|lock")

# Qualifiers that make a *_PASS name a step of an algorithm (self._first_pass(), two_pass).
NOT_PASS = (r"first|second|third|final|last|next|prev|previous|single|multi|one|two|three|forward"
            r"|backward|reverse|initial|full|dry|render|review|refine|rerank|cleanup|lint")


def name_core(bare_excluded: str) -> str:
    """The name test, between the optional quotes. bare_excluded: names that only count with a
    prefix (a bare `token` variable is usually a model token; PWD is the working directory).
    Sentry DSNs are public by design, and GOOGLE_APPLICATION_CREDENTIALS holds a file path."""
    return rf"""(?! [\w$.-]*? (?i:public|publishable) )
(?! (?i:{NOT_FIRST}) (?: [_.-] | (?<=[a-z])(?=[A-Z]) ) )
(?! (?: [\w$.-]*? (?: [_.-] | (?<=[a-z0-9])(?=[A-Z]) ) )?
    (?i:{NOT_TOKEN}) [_-]? (?i:token) Q $ )
(?! (?: [\w$.-]*? (?: [_.-] | (?<=[a-z0-9])(?=[A-Z]) ) )?
    (?i:{NOT_PASS}) [_-]? (?i:pass) Q $ )
(?! (?: [\w$.-]*? (?: [_.-] | (?<=[a-z0-9])(?=[A-Z]) ) )?
    (?i: sentry[_-]?dsn | application[_-]?credentials ) Q $ )
(?! (?i:{bare_excluded}) Q $ )
(?: [\w$.-]*? (?: [_.-] | (?<=[a-z0-9])(?=[A-Z]) ) )?
(?i:{WORDS}) Q $"""


def name_regex(quoted: bool, bare_excluded: str) -> str:
    """A metavariable-regex for an identifier or attribute name (quoted=False) or for a quoted
    string key or env var name (quoted=True)."""
    core = name_core(bare_excluded)
    if quoted:
        return "(?x)\n^ [\"'`] (?=[\\w$.-]+ [\"'`] $)\n" + core.replace("Q", "[\"'`]")
    return "(?x)\n^ (?=[A-Za-z_$][\\w$]* $)\n" + core.replace(" Q ", " ")


# A variable, attribute, or dict key: `token`, `pwd`, `pass` and `dsn` need a prefix.
NAME = name_regex(False, "token|pwd|pass|dsn")
KEY = name_regex(True, "token|pwd|pass|dsn")
# An environment variable: TOKEN and PASS alone are secrets there, PWD is the working directory.
ENV = name_regex(True, "pwd|dsn")
ENV_ATTR = name_regex(False, "pwd|dsn")

# A string literal (or an f-string or template's literal text) holding a credential: a known
# format, a Bearer credential, a URL with a secret in it, or "password: <opaque literal>".
LITERAL = rf"""(?x)
{DEFINE}
^ .*? (?:
{EMBEDDED}
    # password: ..., API key = ..., the token is ...
  | (?<![A-Za-z0-9_-]) (?i: password | passwd | passphrase | secret | token | (?:api|access|private|auth)[ _-]?key )
    ["'`]? [ \t]* (?: [:=] | (?i:\s is) ) [ \t]* ["'`]? (?&opq)
)"""

# A template placeholder named like a secret, {api_key} or {{ db_password }}: a LangChain or
# str.format template that will be filled with the secret.
PLACEHOLDER = ("(?x)\n^ .*? \\{ \\{? [ \\t]* (?=[A-Za-z_$][\\w$]* [ \\t]* \\})\n"
               + name_core("token|pwd|pass|dsn").replace(" Q $", " (?=[ \\t]*\\})"))

# Callees that hash or mask a value, so their result no longer holds the secret.
MASKER = r"(?i)^(?:[\w$.]*\.)?[\w$]*(?:mask|redact|hash|digest|fingerprint|obfuscate|censor|anonymi[sz]e)[\w$]*$"

# Calls that render a prompt from keyword or object arguments; a secret passed to one stays in
# the text, so they never count as "used to authenticate".
RENDER = r"format|format_map|formatMessages|format_messages|format_prompt|formatPromptValue|render|substitute|safe_substitute|partial|replace|replaceAll|join|concat|dedent|indent|fill"

# A keyword or object key that hands a secret to a client, connection, or request: headers or
# auth, or a name that NAME accepts (api_key=, password=, apiKey:).
AUTH_KW = ("(?x)\n^ (?: (?i:headers|auth|cookies|basic_?auth|http_?auth) $\n| (?=[A-Za-z_$][\\w$]* $)\n"
           + name_core("pwd").replace(" Q ", " ") + "\n)")

# ---- shared text ---------------------------------------------------------------------------

SYNC_NOTE = """    # Generated by scripts/gen_secret_in_system_prompt.py, which holds the secret-name and
    # credential regexes shared with {other} (and, for literals, with the
    # mcp-config-plaintext-secret rules). Edit the script and run scripts/build.py;
    # build.py --check fails if this file drifts.
"""

MESSAGE = """    message: >-
      A secret reaches the model's system prompt or instructions: a variable, setting, or
      environment variable named like an API key, token, password, or connection string, or a
      literal credential. Anything in the context window can be extracted ("repeat everything
      above"), echoed into a reply or tool call, and stored in provider and tracing logs, so treat
      it as disclosed to everyone who can talk to the model, including through injected content.
      Keep the credential in the code that calls the tool or API (the client constructor, request
      headers, the tool function), give the model only an opaque name for the resource, and
      rotate this secret if the prompt has been served.
"""

OPTIONS = """    mode: taint
    options:
      # `key is not None`, `len(key)` and similar say something about a secret without holding it.
      taint_assume_safe_booleans: true
      taint_assume_safe_numbers: true
"""


def metadata(technology: str, refs: str, fp_note: str) -> str:
    return f"""    metadata:
      category: security
      subcategory: [vuln]
      pack-category: ai-code
      owasp-llm:
        - "LLM08:2026 - Hidden Context Exposure"
        - "LLM07:2025 - System Prompt Leakage"
      owasp-aisvs:
        - "v1.01-C9.5.4 - Agent Authorization, Delegation, and Continuous Enforcement"
      mitre-atlas:
        - "AML.T0056 - Extract LLM System Prompt"
        - "AML.T0055 - Unsecured Credentials"
      cwe:
        - "CWE-522: Insufficiently Protected Credentials"
        - "CWE-200: Exposure of Sensitive Information to an Unauthorized Actor"
      # The name decides what counts as a secret, so a well-named non-secret can match{fp_note}.
      confidence: MEDIUM
      likelihood: MEDIUM
      impact: HIGH
      technology: {technology}
      references:
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM08_HiddenContextExposure.md
        - https://cwe.mitre.org/data/definitions/522.html
{refs}"""


# ---- Python --------------------------------------------------------------------------------

GLOBAL_NOTE = """      # A module-level variable holding one of the above, used in a function or class defined
      # after it. With --taint-intrafile, OpenGrep drops module-level taint inside a function the
      # file never calls, so the variable's later uses are sources too. The region starts at an
      # assignment whose value contains one of the shapes above and runs to the end of its block;
      # the use must sit in a definition inside it, and a function that assigns the name itself
      # (a local) is left out. A region from every assignment to each later definition took
      # 25 s on a module of 4,000 constants (OpenGrep 1.30.2), and one from every assignment to
      # the end of the block over 100 s: the value's checks run only after the regions meet the
      # uses, so the regions must start at the shapes themselves.
"""


def inside(pattern: str, n: int, negative: bool = False) -> str:
    key = "pattern-not-inside" if negative else "pattern-inside"
    pad = " " * n
    return f"{pad}- {key}: |\n" + "".join(f"{pad}    {line}\n" for line in pattern.splitlines())


def global_alias(assigns: list[str], scopes: list[str], local_scopes: list[str], object_rhs: str,
                 shapes: list[tuple[str, str | None, str | None]]) -> str:
    """Sources for uses of $G after an assignment (one of `assigns`, with {V} for the value)
    whose value contains one of `shapes` (pattern, metavariable, regex), inside one of `scopes`
    and not inside one of `local_scopes` (a definition that assigns $G itself). An assignment
    whose value passes `object_rhs` (an object built from the secret) doesn't count."""
    out = GLOBAL_NOTE + "      - patterns:\n          - pattern-either:\n"
    for pattern, var, regex in shapes:
        regions = [a.format(V=f"<... {pattern} ...>") + "\n..." for a in assigns]
        if var:
            out += "              - patterns:\n"
            if len(regions) > 1:
                out += "                  - pattern-either:\n" + "".join(inside(r, 22) for r in regions)
            else:
                out += inside(regions[0], 18)
            out += mvr(var, regex, 18, literal=True)
        else:
            if len(regions) > 1:
                out += "              - pattern-either:\n" + "".join(inside(r, 18) for r in regions)
            else:
                out += inside(regions[0], 14)
    out += "          - pattern-not-inside:\n              patterns:\n"
    if len(assigns) > 1:
        out += "                - pattern-either:\n"
        out += "".join(f"                    - pattern: |\n                        {a.format(V='$RHS')}\n                        ...\n" for a in assigns)
    else:
        out += f"                - pattern: |\n                    {assigns[0].format(V='$RHS')}\n                    ...\n"
    out += mvr("$RHS", object_rhs, 16, literal=True)
    out += "          - pattern-either:\n" + "".join(inside(s, 14) for s in scopes)
    out += "".join(inside(s, 10, negative=True) for s in local_scopes)
    out += "          - pattern: $G\n"
    return out


PY_ASSIGNS = ["$G = {V}"]
PY_SCOPES = ["def $FN(...):\n  ...", "async def $FN(...):\n  ...", "class $CLS:\n  ..."]
PY_LOCALS = [f"{d} $LOCAL_FN(...):\n  ...\n  $G = $VALUE\n  ..." for d in ("def", "async def")]
TS_ASSIGNS = ["const $G = {V};", "let $G = {V};"]
TS_SCOPES = ["function $FN(...) { ... }", "class $CLS { ... }", "const $FN = ($...ARGS) => $BODY;",
             "const $FN = async ($...ARGS) => $BODY;"]
TS_LOCALS = [f"{f}\n  ...\n  {k} $G = $VALUE;\n  ...\n}}" for k in ("const", "let")
             for f in ("function $LOCAL_FN(...) {", "($...LOCAL_ARGS) => {", "async ($...LOCAL_ARGS) => {")]
# A method's locals: the region is the class, so a name a method assigns locally isn't read from
# the module anywhere in that class.
TS_LOCALS += [f"class $LOCAL_CLS {{\n  ...\n  $LOCAL_M(...) {{\n    ...\n    {k} $G = $VALUE;\n    ...\n  }}\n  ...\n}}"
              for k in ("const", "let")]
# The value is the secret or text built around it, not an object built from it (a client
# constructed with the key): a call or `new` at the top, other than the env and secret readers,
# doesn't count.
PY_OBJECT_RHS = r"^[\w.]*\((?<!getenv\()(?<!config\()(?<!\.get\()(?<!get_secret_value\()"
TS_OBJECT_RHS = r"^(?:new\b|[\w$.]*\((?<!\.get\())"

PY_SOURCES = """    pattern-sources:
      # Environment variables named like a secret: os.environ["OPENAI_API_KEY"], os.getenv("DB_PASSWORD").
      - patterns:
          - pattern-either:
              - pattern: os.environ[$N]
              - pattern: os.environ.get($N, ...)
              - pattern: os.getenv($N, ...)
              - pattern: decouple.config($N, ...)
""" + mvr("$N", ENV, 10, literal=True) + """      # Variables, parameters, settings fields, and dict keys named like a secret:
      # api_key, settings.stripe_secret_key, st.secrets["DATABASE_URL"], body.get("password").
      - patterns:
          - pattern: $V
""" + mvr("$V", NAME, 10, literal=True) + """      - patterns:
          - pattern: $O.$F
""" + mvr("$F", NAME, 10, literal=True) + """      - patterns:
          - pattern-either:
              - pattern: $M[$N]
              - pattern: $M.get($N, ...)
""" + mvr("$N", KEY, 10, literal=True) + """      # pydantic SecretStr / SecretBytes unwrapped.
      - pattern: $X.get_secret_value()
      # A credential written into the code: sk-..., ghp_..., postgres://user:pass@host.
      - patterns:
          - pattern: '"$S"'
""" + mvr("$S", LITERAL, 10, literal=True) + """      # A template that will be filled with a secret: ("system", "... {db_password} ...").
      - patterns:
          - pattern: '"$S"'
""" + mvr("$S", PLACEHOLDER, 10, literal=True) + global_alias(
    PY_ASSIGNS, PY_SCOPES, PY_LOCALS, PY_OBJECT_RHS,
    [("os.environ[$N]", "$N", ENV), ("os.environ.get($N, ...)", "$N", ENV),
     ("os.getenv($N, ...)", "$N", ENV), ("decouple.config($N, ...)", "$N", ENV),
     ("$M[$N]", "$N", KEY), ("$M.get($N, ...)", "$N", KEY), ("$O.$F", "$F", NAME),
     ("$X.get_secret_value()", None, None)])

PY_SANITIZERS = """    pattern-sanitizers:
      # Facts about a secret are not the secret: presence, length, comparisons, hashes, masks.
      - pattern-either:
          - pattern: bool(...)
          - pattern: len(...)
          - pattern: $A == $B
          - pattern: $A != $B
          - pattern: $A in $B
          - pattern: $A not in $B
          - pattern: $X.startswith(...)
          - pattern: $X.endswith(...)
          - pattern: hashlib.$H(...)
          - pattern: hmac.$H(...)
      - patterns:
          - pattern: $F(...)
""" + mvr("$F", MASKER, 10, literal=True) + """      # A secret handed to a client, connection, or request is used correctly, and what that
      # object returns (a completion, rows, a fetched page) is data, not the secret. `exact`
      # keeps sinks inside the call's own arguments: SystemMessage(...), Agent(instructions=...).
      - exact: true
        patterns:
          - pattern-either:
              - patterns:
                  - pattern: $F(...)
                  - metavariable-regex:
                      metavariable: $F
                      regex: ^(?:[\\w.]*\\.)?(?:[A-Z]\\w*|connect|create_engine|create_async_engine|from_url|from_uri|from_dsn|from_connection_string|urlopen|request)$
              # A class's factory, Memory.from_config(settings), other than a prompt or message
              # template's (ChatPromptTemplate.from_messages holds the system slot).
              - patterns:
                  - pattern: $F(...)
                  - metavariable-regex:
                      metavariable: $F
                      regex: ^(?:[\\w.]*\\.)?(?![A-Za-z]*(?:Prompt|Message|Template))[A-Z]\\w*\\.from_\\w+$
              - pattern: requests.$M(...)
              - pattern: httpx.$M(...)
              # session.get(url) on a session that carries the auth header.
              - patterns:
                  - pattern: $S.$VERB($URL, ...)
                  - metavariable-regex:
                      metavariable: $VERB
                      regex: ^(get|post|put|patch|delete|head|request|stream|fetch)$
                  - metavariable-regex:
                      metavariable: $URL
                      regex: (?i)^(?:(?:f|rf|fr)?["'](?:https?://|/)|[\\w.]*(?:url|uri|endpoint|path|route)$)
              - patterns:
                  - pattern: $F(..., $KW=$V, ...)
                  - metavariable-regex:
                      metavariable: $F
                      regex: ^(?!(?:[\\w.]*\\.)?(?:""" + RENDER + """)$)
""" + mvr("$KW", AUTH_KW, 18, literal=True) + """          # Never a call that is itself a system slot (SystemMessage(...), Agent(instructions=...)):
          # OpenGrep drops taint from a source inside an exactly sanitized call's arguments.
          - pattern-not: $G(..., system_prompt=$X, ...)
          - pattern-not: $G(..., system_instruction=$X, ...)
          - pattern-not: $G(..., system_message=$X, ...)
          - pattern-not: $G(..., instructions=$X, ...)
          - pattern-not: $G(..., system=$X, ...)
          - pattern-not: $G(..., role=$X, ...)
          - pattern-not: SystemMessage(...)
"""

# The system role, as a string or an enum member (LlamaIndex MessageRole.SYSTEM).
ROLE = r"""^(?:["'](?:system|developer)["']|(?:[\w.]*\.)?(?i:system|developer)(?:_\w+)?|(?i:system|developer)_\w*)$"""

PY_SINKS = """    pattern-sinks:
      # Anthropic messages.create / stream / parse (also client.beta.messages and AsyncAnthropic).
      - patterns:
          - pattern-inside: $C.messages.$M(..., system=$X, ...)
          - metavariable-regex:
              metavariable: $M
              regex: ^(create|stream|parse)$
          - focus-metavariable: $X
      # Amazon Bedrock Converse.
      - patterns:
          - pattern-either:
              - pattern-inside: $C.converse(..., system=$X, ...)
              - pattern-inside: $C.converse_stream(..., system=$X, ...)
          - focus-metavariable: $X
      # OpenAI Responses and LiteLLM's responses(). The Assistants API (instructions=,
      # additional_instructions=) is not a sink: OpenAI removed it on 2026-08-26
      # (https://developers.openai.com/api/docs/deprecations, checked 2026-10-22).
      - patterns:
          - pattern-either:
              - patterns:
                  - pattern-inside: $C.responses.$M(..., instructions=$X, ...)
                  - metavariable-regex:
                      metavariable: $M
                      regex: ^(create|stream|parse)$
              - pattern-inside: litellm.responses(..., instructions=$X, ...)
              - pattern-inside: litellm.aresponses(..., instructions=$X, ...)
          - focus-metavariable: $X
      # Agent classes: OpenAI Agents SDK and Pydantic AI Agent(instructions=...), and others.
      - patterns:
          - pattern-inside: $AGENT(..., instructions=$X, ...)
          - metavariable-regex:
              metavariable: $AGENT
              regex: ^(?:[\\w.]*\\.)?\\w*Agent$
          - focus-metavariable: $X
      # Instructions given as a function (OpenAI Agents SDK dynamic instructions, Pydantic AI):
      # what a lambda or a function defined earlier in the file returns.
      - patterns:
          - pattern-either:
              - pattern-inside: '$AGENT(..., instructions=lambda $...ARGS: $X, ...)'
              - patterns:
                  - pattern-either:
                      - pattern-inside: |
                          def $FN(...):
                            ...
                      - pattern-inside: |
                          async def $FN(...):
                            ...
                  - pattern-either:
                      - pattern-inside: |
                          def $FN(...):
                            ...
                          ...
                          $AGENT(..., instructions=$FN, ...)
                      - pattern-inside: |
                          async def $FN(...):
                            ...
                          ...
                          $AGENT(..., instructions=$FN, ...)
                  - pattern: return $X
          - metavariable-regex:
              metavariable: $AGENT
              regex: ^(?:[\\w.]*\\.)?\\w*Agent$
          - focus-metavariable: $X
      # Keywords that are the system prompt wherever they appear: ClaudeAgentOptions,
      # Pydantic AI Agent, LangChain create_agent (system_prompt); Gemini GenerateContentConfig
      # (system_instruction); AutoGen agents (system_message).
      - patterns:
          - pattern-either:
              - pattern-inside: $F(..., system_prompt=$X, ...)
              - pattern-inside: $F(..., system_instruction=$X, ...)
              - pattern-inside: $F(..., system_message=$X, ...)
              - pattern-inside: create_react_agent(..., prompt=$X, ...)
          - focus-metavariable: $X
      # Chat messages with the system or developer role, as dicts (OpenAI, LiteLLM, Anthropic)
      # or keyword-built message objects.
      - patterns:
          - pattern-either:
              - patterns:
                  - pattern-inside: '{..., "role": $R, ...}'
                  - pattern-inside: '{..., "content": $X, ...}'
              - patterns:
                  - pattern-inside: $MSG(..., role=$R, ...)
                  - pattern-inside: $MSG(..., content=$X, ...)
""" + mvr("$R", ROLE, 10, literal=True) + """          - focus-metavariable: $X
      # A raw request body for the Anthropic, Bedrock, or Responses HTTP APIs, or a Realtime session.
      - patterns:
          - pattern-either:
              - patterns:
                  - pattern-inside: '{..., "messages": $MSGS, ...}'
                  - pattern-inside: '{..., "system": $X, ...}'
              - patterns:
                  - pattern-inside: '{..., "input": $IN, ...}'
                  - pattern-inside: '{..., "instructions": $X, ...}'
              # OpenAI Realtime session config (session.update, client_secrets.create).
              - patterns:
                  - pattern-inside: '{..., "type": "realtime", ...}'
                  - pattern-inside: '{..., "instructions": $X, ...}'
          - focus-metavariable: $X
      # LangChain system messages and prompt templates.
      - patterns:
          - pattern-either:
              - pattern-inside: SystemMessage($X, ...)
              - pattern-inside: SystemMessage(..., content=$X, ...)
              - pattern-inside: SystemMessagePromptTemplate.from_template($X, ...)
              - pattern-inside: ("system", $X)
          - focus-metavariable: $X
      # Pydantic AI dynamic system prompts and instructions, and LangChain 1.x @dynamic_prompt
      # agent middleware: what the decorated function returns.
      - patterns:
          - pattern-either:
              - pattern-inside: |
                  @dynamic_prompt
                  def $FN(...):
                    ...
              - pattern-inside: |
                  @dynamic_prompt
                  async def $FN(...):
                    ...
              - pattern-inside: |
                  @$A.system_prompt
                  def $FN(...):
                    ...
              - pattern-inside: |
                  @$A.system_prompt(...)
                  def $FN(...):
                    ...
              - pattern-inside: |
                  @$A.instructions
                  def $FN(...):
                    ...
              - pattern-inside: |
                  @$A.system_prompt
                  async def $FN(...):
                    ...
              - pattern-inside: |
                  @$A.system_prompt(...)
                  async def $FN(...):
                    ...
              - pattern-inside: |
                  @$A.instructions
                  async def $FN(...):
                    ...
          - pattern: return $X
          - focus-metavariable: $X
"""

PY_REFS = """        - https://github.com/anthropics/anthropic-sdk-python/blob/v2.1.0/src/anthropic/resources/messages/messages.py
        - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/types/chat/chat_completion_developer_message_param.py
        - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/resources/responses/responses.py
        - https://github.com/openai/openai-python/blob/v3.37.0/src/openai/types/realtime/realtime_session_create_request_param.py
        - https://github.com/openai/openai-agents-python/blob/v0.24.0/src/agents/agent.py
        - https://github.com/pydantic/pydantic-ai/blob/v2.59.0/pydantic_ai_slim/pydantic_ai/agent/__init__.py
        - https://github.com/anthropics/claude-agent-sdk-python/blob/v0.2.172/src/claude_agent_sdk/types.py
        - https://github.com/langchain-ai/langchain/blob/langchain-core%3D%3D1.7.0/libs/core/langchain_core/prompts/chat.py
        - https://github.com/langchain-ai/langchain/blob/langchain%3D%3D1.4.7/libs/langchain_v1/langchain/agents/factory.py
        - https://github.com/langchain-ai/langgraph/blob/prebuilt%3D%3D1.1.1/libs/prebuilt/langgraph/prebuilt/chat_agent_executor.py
        - https://github.com/BerriAI/litellm/blob/v1.106.2/litellm/responses/main.py
        - https://github.com/googleapis/python-genai/blob/v2.32.0/google/genai/types.py
        - https://github.com/boto/botocore/blob/1.43.118/botocore/data/bedrock-runtime/2023-09-30/service-2.json
"""


# The client factories the sanitizers recognize (Memory.from_config / Memory.fromConfig). Not in
# PY_REFS / TS_REFS, which the user-input and fetched-content rules reuse for their sinks.
MEM0_PY_REF = "        - https://github.com/mem0ai/mem0/blob/ts-v3.3.1/mem0/memory/main.py\n"
MEM0_TS_REF = "        - https://github.com/mem0ai/mem0/blob/ts-v3.3.1/mem0-ts/src/oss/src/memory/index.ts\n"


def py_rule() -> str:
    s = "rules:\n  - id: secret-in-system-prompt\n"
    s += SYNC_NOTE.format(other="secret-in-system-prompt-ts.yaml")
    s += "    languages: [python]\n    severity: ERROR\n" + MESSAGE + OPTIONS
    s += PY_SOURCES + PY_SANITIZERS + PY_SINKS
    s += metadata("[openai, anthropic, litellm, langchain, pydantic-ai, claude-agent-sdk, openai-agents, gemini, bedrock]", PY_REFS + MEM0_PY_REF,
                  ", and a\n      # pydantic SecretStr field interpolated without get_secret_value() prints asterisks")
    return s


# ---- TypeScript / JavaScript ---------------------------------------------------------------

TS_SOURCES = """    pattern-sources:
      # Environment variables named like a secret: process.env.OPENAI_API_KEY, process.env["DB_PASSWORD"].
      - patterns:
          - pattern-either:
              - pattern: process.env.$E
              - pattern: Bun.env.$E
""" + mvr("$E", ENV_ATTR, 10, literal=True) + """      - patterns:
          - pattern-either:
              - pattern: process.env[$N]
              - pattern: Deno.env.get($N)
""" + mvr("$N", ENV, 10, literal=True) + """      # Variables, parameters, destructured env vars, config fields, and keys named like a
      # secret: apiKey, const { STRIPE_SECRET_KEY } = process.env, env.DATABASE_URL.
      - patterns:
          - pattern: $V
""" + mvr("$V", NAME, 10, literal=True) + """      - patterns:
          - pattern: $O.$F
""" + mvr("$F", NAME, 10, literal=True) + """      - patterns:
          - pattern-either:
              - pattern: $M[$N]
              - pattern: $M.get($N)
""" + mvr("$N", KEY, 10, literal=True) + """      # A credential written into the code: sk-..., ghp_..., postgres://user:pass@host.
      - patterns:
          - pattern: '"$S"'
""" + mvr("$S", LITERAL, 10, literal=True) + """      # A template that will be filled with a secret: ["system", "... {dbPassword} ..."].
      - patterns:
          - pattern: '"$S"'
""" + mvr("$S", PLACEHOLDER, 10, literal=True) + global_alias(
    TS_ASSIGNS, TS_SCOPES, TS_LOCALS, TS_OBJECT_RHS,
    [("process.env.$E", "$E", ENV_ATTR), ("Bun.env.$E", "$E", ENV_ATTR),
     ("process.env[$N]", "$N", ENV), ("Deno.env.get($N)", "$N", ENV),
     ("$M[$N]", "$N", KEY), ("$M.get($N)", "$N", KEY), ("$O.$F", "$F", NAME)])

TS_SANITIZERS = """    pattern-sanitizers:
      # Facts about a secret are not the secret: presence, length, comparisons, hashes, masks.
      - pattern-either:
          - pattern: Boolean(...)
          - pattern: $A === $B
          - pattern: $A !== $B
          - pattern: $A == $B
          - pattern: $A != $B
          - pattern: $X.startsWith(...)
          - pattern: $X.endsWith(...)
          - pattern: $X.includes(...)
          - pattern: $X.length
          - pattern: $X.digest(...)
          - pattern: createHash(...)
          - pattern: $C.createHash(...)
          - pattern: $C.createHmac(...)
          - pattern: createHmac(...)
      - patterns:
          - pattern: $F(...)
""" + mvr("$F", MASKER, 10, literal=True) + """      # A secret handed to a client, connection, or request is used correctly, and what that
      # object returns (a completion, rows, a fetched page) is data, not the secret. `exact`
      # keeps sinks inside the call's own arguments: new SystemMessage(...), new Agent({...}).
      - exact: true
        patterns:
          - pattern-either:
              - pattern: new $C(...)
              - pattern: fetch(...)
              - pattern: axios(...)
              - pattern: axios.$M(...)
              - pattern: got(...)
              - pattern: ky(...)
              # api.get("/me") on a client that carries the auth header.
              - patterns:
                  - pattern: $S.$VERB($URL, ...)
                  - metavariable-regex:
                      metavariable: $VERB
                      regex: ^(get|post|put|patch|delete|head|request|stream|fetch)$
                  - metavariable-regex:
                      metavariable: $URL
                      regex: (?i)^(?:["'`](?:https?://|/)|[\\w$.]*(?:url|uri|endpoint|path|route)$)
              - patterns:
                  - pattern: $F(...)
                  - metavariable-regex:
                      metavariable: $F
                      regex: ^(?:[\\w$.]*\\.)?(?:[A-Z][\\w$]*|connect|createClient|createPool|createConnection|createKysely|drizzle|postgres|neon|request)$
              # A class's factory, Memory.fromConfig(settings), other than a prompt or message
              # template's (ChatPromptTemplate.fromMessages holds the system slot).
              - patterns:
                  - pattern: $F(...)
                  - metavariable-regex:
                      metavariable: $F
                      regex: ^(?:[\\w$.]*\\.)?(?![A-Za-z$]*(?:Prompt|Message|Template))[A-Z][\\w$]*\\.from[A-Z][\\w$]*$
              - patterns:
                  - pattern: '$F(..., {..., $K: $V, ...}, ...)'
                  - metavariable-regex:
                      metavariable: $F
                      regex: ^(?!(?:[\\w$.]*\\.)?(?:""" + RENDER + """)$)
""" + mvr("$K", AUTH_KW, 18, literal=True) + """          # Never a call that is itself a system slot (new SystemMessage(...), new Agent({...})):
          # OpenGrep drops taint from a source inside an exactly sanitized call's arguments.
          - pattern-not: new SystemMessage(...)
          - pattern-not: '$G(..., {..., system: $X, ...}, ...)'
          - pattern-not: '$G(..., {..., instructions: $X, ...}, ...)'
          - pattern-not: '$G(..., {..., systemPrompt: $X, ...}, ...)'
          - pattern-not: '$G(..., {..., systemInstruction: $X, ...}, ...)'
          - pattern-not: 'new $G(..., {..., system: $X, ...}, ...)'
          - pattern-not: 'new $G(..., {..., instructions: $X, ...}, ...)'
          - pattern-not: 'new $G(..., {..., systemPrompt: $X, ...}, ...)'
          - pattern-not: 'new $G(..., {..., content: $X, ...}, ...)'
"""

TS_ROLE = r"""^(?:["'`](?:system|developer)["'`]|(?:[\w$.]*\.)?(?i:system|developer)(?:_\w+)?|(?i:system|developer)_\w*)$"""

TS_SINKS = """    pattern-sinks:
      # Request objects: Anthropic messages.create / stream, Bedrock ConverseCommand, AI SDK
      # generateText / streamText / generateObject / streamObject (system is deprecated in
      # favor of instructions in AI SDK 7), OpenAI Responses, and OpenAI Realtime sessions. The
      # Assistants API is not a sink: OpenAI removed it on 2026-08-26
      # (https://developers.openai.com/api/docs/deprecations, checked 2026-10-22).
      - patterns:
          - pattern-either:
              - patterns:
                  - pattern-inside: '{..., system: $X, ...}'
                  - pattern-either:
                      - pattern-inside: '{..., messages: $IN, ...}'
                      - pattern-inside: '{..., prompt: $IN, ...}'
              - patterns:
                  - pattern-inside: '{..., instructions: $X, ...}'
                  - pattern-either:
                      - pattern-inside: '{..., messages: $IN, ...}'
                      - pattern-inside: '{..., prompt: $IN, ...}'
                      - pattern-inside: '{..., input: $IN, ...}'
              - pattern-inside: '$C.messages.$M({..., system: $X, ...}, ...)'
              - pattern-inside: '$C.responses.$M({..., instructions: $X, ...}, ...)'
              # OpenAI Realtime session config (session.update, clientSecrets.create).
              - patterns:
                  - pattern-inside: '{..., type: "realtime", ...}'
                  - pattern-inside: '{..., instructions: $X, ...}'
          - focus-metavariable: $X
      # Agent classes: OpenAI Agents SDK new Agent({ instructions }), AI SDK ToolLoopAgent, Mastra.
      - patterns:
          - pattern-either:
              - pattern-inside: 'new $AGENT({..., instructions: $X, ...}, ...)'
              - pattern-inside: 'new $AGENT({..., system: $X, ...}, ...)'
          - metavariable-regex:
              metavariable: $AGENT
              regex: ^(?:[\\w$.]*\\.)?[\\w$]*Agent$
          - focus-metavariable: $X
      # Instructions given as a function (OpenAI Agents SDK dynamic instructions, Mastra): what
      # an inline function, or a function declared or assigned to a const earlier in the file,
      # returns. Only the function's own returns count, not what a tool's execute() returns (a
      # tool result, which the model reads as data) or the body of a callback inside the
      # function (docs.map((d) => d.title)). Its final return always counts, and so does an
      # earlier one (inside an if or a loop) unless it sits in a callback, a function passed as
      # an argument. An inline or const function is bound as $FNX and its returns are matched
      # with metavariable-pattern, so the callback test sees only that function, not a route
      # handler the agent is built in; the paren guard before it is OpenGrep's String.sub crash
      # (gen_mcp_unpinned.py).
      - patterns:
          - pattern-either:
              - pattern-inside: 'new $AGENT({..., instructions: ($...ARGS) => $X, ...}, ...)'
              - pattern-inside: 'new $AGENT({..., instructions: async ($...ARGS) => $X, ...}, ...)'
              - pattern-inside: |
                  const $FN = ($...P) => $X;
                  ...
                  new $AGENT({..., instructions: $FN, ...}, ...);
              - pattern-inside: |
                  const $FN = async ($...P) => $X;
                  ...
                  new $AGENT({..., instructions: $FN, ...}, ...);
              - pattern-inside: 'new $AGENT({..., instructions: ($...ARGS) => { $...BODY; return $X; }, ...}, ...)'
              - pattern-inside: 'new $AGENT({..., instructions: async ($...ARGS) => { $...BODY; return $X; }, ...}, ...)'
              - pattern-inside: 'new $AGENT({..., instructions: function ($...ARGS) { $...BODY; return $X; }, ...}, ...)'
              - pattern-inside: 'new $AGENT({..., instructions: async function ($...ARGS) { $...BODY; return $X; }, ...}, ...)'
              - pattern-inside: |
                  function $FN($...P) { $...BODY; return $X; }
                  ...
                  new $AGENT({..., instructions: $FN, ...}, ...);
              - pattern-inside: |
                  async function $FN($...P) { $...BODY; return $X; }
                  ...
                  new $AGENT({..., instructions: $FN, ...}, ...);
              - pattern-inside: |
                  const $FN = ($...P) => { $...BODY; return $X; };
                  ...
                  new $AGENT({..., instructions: $FN, ...}, ...);
              - pattern-inside: |
                  const $FN = async ($...P) => { $...BODY; return $X; };
                  ...
                  new $AGENT({..., instructions: $FN, ...}, ...);
              - pattern-inside: |
                  const $FN = function ($...P) { $...BODY; return $X; };
                  ...
                  new $AGENT({..., instructions: $FN, ...}, ...);
              - pattern-inside: |
                  const $FN = async function ($...P) { $...BODY; return $X; };
                  ...
                  new $AGENT({..., instructions: $FN, ...}, ...);
              - patterns:
                  - pattern-either:
                      - pattern-inside: 'new $AGENT({..., instructions: $FNX, ...}, ...)'
                      - pattern-inside: |
                          const $FN = $FNX;
                          ...
                          new $AGENT({..., instructions: $FN, ...}, ...);
""" + paren_guard("$FNX", 18) + """                  - metavariable-pattern:
                      metavariable: $FNX
                      patterns:
                        - pattern: return $X;
                        - pattern-not-inside: '$F(..., ($...A) => $B, ...)'
                        - pattern-not-inside: '$F(..., async ($...A) => $B, ...)'
                        - pattern-not-inside: '$F(..., function ($...A) { ... }, ...)'
                        - pattern-not-inside: '$F(..., async function ($...A) { ... }, ...)'
              - patterns:
                  - pattern-either:
                      - pattern-inside: |
                          function $FN($...P) { ... return $X; ... }
                          ...
                          new $AGENT({..., instructions: $FN, ...}, ...);
                      - pattern-inside: |
                          async function $FN($...P) { ... return $X; ... }
                          ...
                          new $AGENT({..., instructions: $FN, ...}, ...);
                  - pattern: return $X;
                  - pattern-not-inside: '$F(..., ($...A) => $B, ...)'
                  - pattern-not-inside: '$F(..., async ($...A) => $B, ...)'
                  - pattern-not-inside: '$F(..., function ($...A) { ... }, ...)'
                  - pattern-not-inside: '$F(..., async function ($...A) { ... }, ...)'
          - metavariable-regex:
              metavariable: $AGENT
              regex: ^(?:[\\w$.]*\\.)?[\\w$]*Agent$
          - focus-metavariable: $X
      # Keys that are the system prompt wherever they appear: Claude Agent SDK options and
      # LangChain createAgent (systemPrompt), Gemini config (systemInstruction), and the Claude
      # Agent SDK preset's append and custom prompt; LangGraph createReactAgent (prompt).
      - patterns:
          - pattern-either:
              - pattern-inside: '{..., systemPrompt: $X, ...}'
              - pattern-inside: '{..., systemInstruction: $X, ...}'
              - pattern-inside: '{..., system_prompt: $X, ...}'
              - patterns:
                  - pattern-inside: '{..., type: "preset", ...}'
                  - pattern-inside: '{..., append: $X, ...}'
              - patterns:
                  - pattern-inside: '{..., type: "custom", ...}'
                  - pattern-inside: '{..., prompt: $X, ...}'
              - pattern-inside: 'createReactAgent({..., prompt: $X, ...})'
          - focus-metavariable: $X
      # Chat messages with the system or developer role (OpenAI, AI SDK, Anthropic, LiteLLM).
      - patterns:
          - pattern-inside: '{..., role: $R, ...}'
          - pattern-inside: '{..., content: $X, ...}'
""" + mvr("$R", TS_ROLE, 10, literal=True) + """          - focus-metavariable: $X
      # LangChain.js system messages and prompt templates.
      - patterns:
          - pattern-either:
              - pattern-inside: new SystemMessage($X, ...)
              - pattern-inside: 'new SystemMessage({..., content: $X, ...}, ...)'
              - pattern-inside: SystemMessagePromptTemplate.fromTemplate($X, ...)
              - pattern-inside: '["system", $X]'
          - focus-metavariable: $X
      # LangChain.js 1.x dynamicSystemPromptMiddleware: what the callback returns becomes the
      # system prompt of each model call.
      - patterns:
          - pattern-either:
              - pattern-inside: 'dynamicSystemPromptMiddleware(($...ARGS) => $X)'
              - pattern-inside: 'dynamicSystemPromptMiddleware(async ($...ARGS) => $X)'
              # The final return of a block body: with `{ ... }` and `return $X;`, the
              # expression body of a nested arrow function (docs.map((d) => d.text)) matches too.
              - pattern-inside: 'dynamicSystemPromptMiddleware(($...ARGS) => { $...BODY; return $X; })'
              - pattern-inside: 'dynamicSystemPromptMiddleware(async ($...ARGS) => { $...BODY; return $X; })'
              - pattern-inside: |
                  function $FN($...P) { $...BODY; return $X; }
                  ...
                  <... dynamicSystemPromptMiddleware($FN) ...>;
              - pattern-inside: |
                  async function $FN($...P) { $...BODY; return $X; }
                  ...
                  <... dynamicSystemPromptMiddleware($FN) ...>;
          - focus-metavariable: $X
"""

TS_REFS = """        - https://github.com/anthropics/anthropic-sdk-typescript/blob/sdk-v1.1.0/src/resources/messages/messages.ts
        - https://github.com/openai/openai-node/blob/v7.42.0/src/resources/chat/completions/completions.ts
        - https://github.com/openai/openai-node/blob/v7.42.0/src/resources/responses/responses.ts
        - https://github.com/openai/openai-node/blob/v7.42.0/src/resources/realtime/realtime.ts
        - https://www.npmjs.com/package/ai/v/7.0.150
        - https://www.npmjs.com/package/@openai/agents-core/v/0.21.0
        - https://www.npmjs.com/package/@anthropic-ai/claude-agent-sdk/v/0.3.308
        - https://www.npmjs.com/package/langchain/v/1.5.19
        - https://www.npmjs.com/package/@langchain/core/v/1.3.0
        - https://www.npmjs.com/package/@langchain/langgraph/v/1.5.2
        - https://www.npmjs.com/package/@google/genai/v/2.30.0
        - https://github.com/boto/botocore/blob/1.43.118/botocore/data/bedrock-runtime/2023-09-30/service-2.json
"""


def ts_rule() -> str:
    s = "rules:\n  - id: secret-in-system-prompt-ts\n"
    s += SYNC_NOTE.format(other="secret-in-system-prompt.yaml")
    s += "    languages: [typescript, javascript]\n    severity: ERROR\n" + MESSAGE + OPTIONS
    s += TS_SOURCES + TS_SANITIZERS + TS_SINKS
    s += metadata("[openai, anthropic, vercel-ai-sdk, langchain, claude-agent-sdk, openai-agents, gemini, bedrock]", TS_REFS + MEM0_TS_REF, "")
    return s


def render() -> dict[Path, str]:
    """The two rule files and the content this script generates for each."""
    return {PY_RULE: py_rule(), TS_RULE: ts_rule()}


def main() -> int:
    for path, content in render().items():
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists() or path.read_text() != content:
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
