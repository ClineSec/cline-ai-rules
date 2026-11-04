#!/usr/bin/env python3
"""Generate the agent-settings-endpoint-override rules from one host test.

A coding agent sends every prompt, the files it reads, and the developer's own credential (API
key, OAuth token, cloud token) to its model endpoint. Several agents let a project file move
that endpoint, and a committed project file is written by whoever last got a change merged:
Claude Code CVE-2026-21852 (GHSA-jh7p-qr78-84p7) was a repository's .claude/settings.json
setting env.ANTHROPIC_BASE_URL, which sent requests with the user's key to the attacker before
the trust prompt. The pre-trust part is fixed (v2.0.65); the setting itself still applies once
the folder is trusted, in every `claude -p` or Agent SDK run, and when only a parent folder was
trusted. Verified against primary sources on 2026-10-25:

- Claude Code (docs for v2.1.309: settings-reference `env`, env-vars, permissions "What runs
  before you trust a folder", llm-gateway): project and local settings may set the endpoint
  variables (ANTHROPIC_BASE_URL and the Bedrock, Bedrock Mantle, Claude Platform on AWS, Vertex
  and Foundry base URLs); they are not on the list of variables project settings can't set.
  With only ANTHROPIC_BASE_URL set, a saved claude.ai login stays the active credential and is
  sent to that host. Values are not expanded, so "${VAR}" stays literal and redirects nothing.
  OpenTelemetry endpoints are ignored in project settings since v2.1.282.
- Gemini CLI v0.65.0 (packages/cli/src/config/settings.ts findEnvFile / loadEnvironment,
  packages/core/src/core/contentGenerator.ts, code_assist/server.ts, telemetry/config.ts): in a
  trusted folder it loads the first of .gemini/.env or .env walking up from the working
  directory, without expansion and only for variables the shell hasn't set. GOOGLE_GEMINI_BASE_URL
  (API key auth; the key goes in x-goog-api-key), GOOGLE_VERTEX_BASE_URL (Vertex AI) and
  CODE_ASSIST_ENDPOINT (Login with Google, the default) move the model endpoint.
  Workspace .gemini/settings.json can set telemetry.otlpEndpoint, and logPrompts defaults to
  true, so prompts go wherever it points once telemetry is on; GEMINI_TELEMETRY_OTLP_ENDPOINT
  does the same from a .env file. settings.json has no model base URL key.
- Codex (codex-rs/config/src/loader/mod.rs): since 0.129.0 (2026-05-07) a project
  .codex/config.toml can't set openai_base_url, chatgpt_base_url, model_provider(s) or the
  realtime base URLs (PROJECT_LOCAL_CONFIG_DENYLIST; 0.164.0 warns at startup). Through 0.128.0
  a trusted project's file applied them, so the TOML rule is LOW confidence and only matters
  for those clients. Codex reads .env only from CODEX_HOME.
- opencode v1.19.4 and Kilo Code v7.8.17 (config/config.ts, provider/provider.ts,
  core/src/v1/config/provider.ts; Kilo kilocode/config/config.ts mergeProject): a project's
  opencode.json(c) / kilo.json(c) and .opencode/ / .kilo/ / .kilocode/ files are merged without
  a prompt. provider.<id>.options.baseURL (or the Bedrock "endpoint" alias, or a provider's or
  model's "api") sets where that provider's stored or environment key is sent. Kilo also lets a
  project set codebase indexing endpoints (indexing.<provider>.baseUrl, indexing.qdrant.url),
  which receive the indexed code. {env:VAR} is a reference, not a host. The shipped binaries are
  built with autoloadDotenv: false, so a project .env doesn't reach them.
- Qwen Code v0.26.1 (packages/cli/src/config/environment.ts, trustedFolders.ts,
  settingsSchema.ts, core/src/models/): folder trust is off by default, so .qwen/settings.json
  and .qwen/.env / .env load with no prompt. modelProviders.<auth>[].baseUrl, security.auth.baseUrl
  and OPENAI_BASE_URL / ANTHROPIC_BASE_URL (env block or .env) set the endpoint, and an entry's
  envKey picks which of the developer's keys is sent; telemetry.otlp*Endpoint and
  QWEN_TELEMETRY_OTLP_* set the exporter, with logPrompts on by default.
- Aider v0.86.0 (aider/main.py, args.py, models.py; LiteLLM 1.75 main.py): .aider.conf.yml
  (openai-api-base, set-env) and .aider.model.settings.yml (extra_params api_base) from the
  working directory and git root, and .env from both with override=True, so a project's
  OPENAI_API_BASE / *_API_BASE wins over the shell.
- Crush v0.98.2 (internal/config/load.go, config.go, shellconfig/provider.go; catwalk v0.52.49):
  crush.json / .crush.json / crushrc / .crushrc from the working directory up to the git root,
  and .crush/crush.json; providers.<id>.base_url replaces a built-in provider's endpoint and its
  key goes along. The shipped binary autoloads .env, where the catalog reads *_API_ENDPOINT and a
  CRUSH_ copy of any variable wins.
- Continue (VS Code extension v2.0.0, core/config/; cn CLI v1.5.45): workspace .continue/ YAML
  blocks and *.continuerc.json join the config once VS Code trusts the workspace (models[].apiBase);
  cn loads .env, where CONTINUE_API_BASE moves the hub API that receives its login token.
- Not redirectable from a project file (checked 2026-10-25):
  Zed 1.25.3: .zed/settings.json is parsed as ProjectSettingsContent, which has no
  language_models or agent; the edit-prediction endpoints it can hold
  (edit_predictions.{codestral,ollama,open_ai_compatible_api}.api_url, the Copilot proxy) are
  read with all_language_settings(None, ..), which returns user settings only.
  Goose 1.56.0: config comes from /etc/goose, GOOSE_ADDITIONAL_CONFIG_FILES and the user config
  dir; custom providers only from the user config dir; a project recipe sets only provider and
  model names; .goosehints is prompt text; dotenvy is a dev-dependency.
  GitHub Copilot CLI 1.0.103 (closed source, docs only: repo settings take a fixed key list) and
  Copilot in VS Code (endpoint settings are user-scope only).

Quiet on purpose: the hosts of the vendor whose credential the client sends (Anthropic and the
Bedrock, Claude Platform on AWS, Vertex and Foundry clouds for Claude Code; Google for Gemini
CLI; OpenAI and Azure OpenAI for Codex; Continue's hub for cn; any model vendor for the
bring-your-own-key clients, whose provider entries name the vendor and its key together), loopback, private and LAN addresses, private
names (.local, .internal, .lan, .ts.net, ...) and single-label hosts (a compose service), as in
the MCP remote-host rules (2026-10-22 LAN decision), and values that aren't a literal URL
(${VAR}, {env:VAR}, empty). Reported: a company gateway on a public name (the fix is to set it in
user or managed settings, where a pull request can't change it), relays outside the vendors' catalogs, and,
for Claude Code, other model vendors' Anthropic-compatible APIs. In 276 public
.claude/settings.json files with ANTHROPIC_BASE_URL (GitHub code search, 2026-10-25), most
pointed at localhost; the rest named relays, company gateways, and other vendors (Zhipu,
MiniMax, DeepSeek, OpenRouter, Xiaomi), and many set no token of their own, so a developer's
claude.ai login went with every request.

Edit this script, not the rule files. scripts/build.py regenerates them, and
scripts/build.py --check fails when a rule file differs from what this script produces.

Usage:
    python3 scripts/gen_agent_settings_endpoint.py    # rewrite the rule files
"""

from __future__ import annotations

import sys
from pathlib import Path

from gen_kilo_opencode_permission import JSON_PATHS as OPENCODE_PATHS
from gen_mcp_remote_host import DEFINE as HOST_DEFINE
from gen_mcp_unpinned import ind, mvr, pregex

ROOT = Path(__file__).resolve().parent.parent
RULE_DIR = ROOT / "rules" / "agent-config" / "data-exposure"

# ---- the host test --------------------------------------------------------------------------

# The hosts that may receive a client's traffic without anyone else seeing it: the vendor whose
# credential the client sends. Only names whose subdomains the vendor alone controls are listed
# (Bedrock by service name and region, not all of amazonaws.com; DashScope and Model Studio, not
# all of aliyuncs.com). Azure, Databricks and Bedrock resource names belong to the customer.
ANTHROPIC = r"anthropic\.com | claude\.ai | claude\.com"
AWS = r"api\.aws"
GOOGLE = r"googleapis\.com"
AZURE = (r"openai\.azure\.com | services\.ai\.azure\.com | cognitiveservices\.azure\.com"
         r" | inference\.ai\.azure\.com | models\.ai\.azure\.com")
OPENAI = r"openai\.com | chatgpt\.com"
CONTINUE = r"continue\.dev"
# Model vendors and model marketplaces that bring-your-own-key clients (opencode, Kilo Code,
# Crush, Qwen Code, Aider, Continue) ship as built-in providers or that their users set up with
# that vendor's own key: the providers in Crush's catwalk catalog (v0.52.49) and the hosts seen
# in public opencode.json / kilo.jsonc files (2026-10-25). Those configs name the vendor and the
# vendor's key together, so pointing a provider at one of these sends nothing to a third party.
# Self-run gateways, company proxies, and relays outside these catalogs stay reported.
MODEL_VENDORS = (r"githubcopilot\.com | models\.github\.ai | openrouter\.ai | mistral\.ai | groq\.com"
                 r" | deepseek\.com | x\.ai | together\.xyz | together\.ai | fireworks\.ai | cerebras\.ai"
                 r" | perplexity\.ai | cohere\.com | cohere\.ai | huggingface\.co | api\.nvidia\.com | meta\.ai"
                 r" | ollama\.com | moonshot\.ai | moonshot\.cn | kimi\.com | z\.ai | bigmodel\.cn"
                 r" | minimax\.io | minimaxi\.com | minimax\.chat | xiaomimimo\.com | siliconflow\.cn | siliconflow\.com"
                 r" | longcat\.chat | dashscope(?:-intl|-us)?\.aliyuncs\.com | maas\.aliyuncs\.com"
                 r" | qwen\.ai | qwencloudapi\.com | replicate\.com | api\.cloudflare\.com"
                 r" | chutes\.ai | coralbricks\.ai | baseten\.co | venice\.ai | nebius\.com | synthetic\.new"
                 r" | scaleway\.ai | qnaigc\.com | pioneer\.ai | neuralwatt\.com | intelligence\.io\.solutions"
                 r" | cortecs\.ai | avian\.io | atlascloud\.ai | aihubmix\.com | ai-gateway\.vercel\.sh"
                 r" | opencode\.ai | kilo\.ai | kilocode\.ai | cline\.bot | charm\.land")
BEDROCK = r"""(?: vpce-[\w-]+\. )? bedrock (?: -runtime | -mantle | -agent-runtime )? (?: -fips )?
        \. (?&region) \. (?: vpce(?:-[\w-]+)?\. )? amazonaws\.com (?: \.cn )?"""
DATABRICKS = r"cloud\.databricks\.com | azuredatabricks\.net | gcp\.databricks\.com"
ARK = r"ark \. [\w-]+ \. volces\.com"

# Per client: the vendors its endpoint keys are meant for.
VENDORS = {
    # Claude Code: Anthropic, and the clouds its Bedrock, Claude Platform on AWS, Vertex and
    # Foundry variables point at. Gemini CLI telemetry to Google Cloud shares the JSON rule.
    "claude-gemini": (ANTHROPIC, AWS, GOOGLE, AZURE),
    # Gemini CLI: Google.
    "gemini": (GOOGLE,),
    # Codex: OpenAI, ChatGPT, and Azure OpenAI.
    "codex": (OPENAI, AZURE),
    # The Continue CLI's hub API.
    "continue": (CONTINUE,),
    # Bring-your-own-key clients: any model vendor.
    "byok": (ANTHROPIC, AWS, GOOGLE, AZURE, OPENAI, DATABRICKS, CONTINUE, MODEL_VENDORS),
}


def vendor_define(client):
    """The vendor hosts of one client, as the named group `vendor`."""
    names = "\n      | ".join(VENDORS[client])
    extra = ""
    if client == "byok":
        extra = "\n    | " + ARK
    if client in ("claude-gemini", "byok"):
        extra += "\n    | " + BEDROCK
    return ("(?(DEFINE)\n  (?<region> [a-z]{2} (?: -[a-z]+ )+ -\\d )\n  (?<vendor> (?i:\n"
            "      (?: (?&lbl) \\. )*? (?:\n        " + names + " )" + extra + " ) )\n)")


# A literal http(s) or ws(s) URL whose host is someone other than the vendor and not this
# machine or a private network. HOST_DEFINE (gen_mcp_remote_host.py) supplies lbl, he,
# userinfo, private, pubip4 and pubip6, so the private-network test matches the MCP rules'.
# JSON text may escape the slashes (https:\/\/host).
REMOTE_URL = r"""(?i:https?|wss?) : (?: \\?+ / ){2} (?&userinfo)
(?! (?&vendor) \.? (?&he) )
(?: (?! (?:(?&lbl)\.)* (?&private) \.? (?&he) ) (?:(?&lbl)\.)+ [A-Za-z][A-Za-z0-9-]*+ \.?
  | (?&pubip4) | (?&pubip6) ) (?&he)"""


def defines(client):
    return HOST_DEFINE + "\n" + vendor_define(client)


def value_regex(client):
    """A metavariable-regex over a JSON string value (with or without its quotes)."""
    return "(?x)\n" + defines(client) + "\n^ \\s*+ \"?+ " + REMOTE_URL


# ---- shared rule text -----------------------------------------------------------------------

SYNC_NOTE = """# Generated by scripts/gen_agent_settings_endpoint.py, which holds the host test the
# agent-settings-endpoint-override rules share (with the private-network groups of
# gen_mcp_remote_host.py). Edit the script and run scripts/build.py; build.py --check fails if
# this file drifts.
"""

WHY = """      The prompts, the files the agent reads, and, for a model endpoint, the developer's own
      credential (API key, OAuth login, or cloud token) go to that host, and anyone who can get
      a change to this file merged, through a pull request, a compromised dependency, or a worm
      that writes into the repo, chooses it for everyone who opens the project (Claude Code
      CVE-2026-21852 was an override like this in a repository's .claude/settings.json). A
      company gateway belongs in user or managed settings, or in the shell that starts the
      agent, where a pull request can't change it; remove the override from the project file,
      or point it at the vendor's own API."""

METADATA = """    metadata:
      category: security
      subcategory: [audit]
      pack-category: agent-config
      owasp-llm:
        - "LLM02:2026 - Sensitive Information Disclosure"
        - "LLM02:2025 - Sensitive Information Disclosure"
      owasp-agentic:
        - "ASI03 - Identity and Privilege Abuse"
        - "ASI04 - Agentic Supply Chain Vulnerabilities"
      owasp-aisvs:
        - "v1.01-AC.11.2 - AI Code-Review & Assistant Bot Hardening"
      mitre-atlas:
        - "AML.T0081 - Modify AI Agent Configuration"
      cwe:
        - "CWE-923: Improper Restriction of Communication Channel to Intended Endpoints"
        - "CWE-522: Insufficiently Protected Credentials"
      confidence: {confidence}
      likelihood: LOW
      impact: HIGH
      technology: [{technology}]
      references:
        - https://github.com/anthropics/claude-code/security/advisories/GHSA-jh7p-qr78-84p7
{references}        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM02_SensitiveInformationDisclosure.md
"""


def header(rule_id, comment, language, severity="WARNING"):
    return (f"rules:\n  - id: {rule_id}\n" + ind(comment, 4) + ind(SYNC_NOTE, 4)
            + f"    languages: [{language}]\n    severity: {severity}\n")


def metadata(confidence, technology, references):
    refs = "".join(f"        - {r}\n" for r in references)
    return METADATA.format(confidence=confidence, technology=", ".join(technology), references=refs)


# ---- agent-settings-endpoint-override (Claude Code and Gemini CLI settings, JSON) ----------

CLAUDE_KEYS = ("ANTHROPIC_BASE_URL", "ANTHROPIC_BEDROCK_BASE_URL", "ANTHROPIC_BEDROCK_MANTLE_BASE_URL",
               "ANTHROPIC_AWS_BASE_URL", "ANTHROPIC_VERTEX_BASE_URL", "ANTHROPIC_FOUNDRY_BASE_URL")

JSON_COMMENT = """# Claude Code's env block (.claude/settings.json and settings.local.json) and Gemini CLI's
# telemetry exporter (.gemini/settings.json). The keys are the tools' own, so a match in the
# other tool's file means nothing and can't occur in practice.
"""

JSON_MESSAGE = """    message: >-
      This committed agent setting sends the agent's model traffic, or Gemini CLI's prompt
      telemetry, to a host that is not the model vendor's API and not on this machine or a
      private network. Claude Code applies a project's env block once the folder is trusted,
      in every `claude -p` and Agent SDK run (which never ask), and when only a parent folder
      was trusted; Gemini CLI applies workspace settings in a trusted folder and logs prompt
      text in telemetry by default.
""" + WHY + "\n"

JSON_PATHS = """    paths:
      include:
        - ".claude/settings.json"
        - ".claude/settings.local.json"
        - ".gemini/settings.json"
"""


def json_rule():
    s = header("agent-settings-endpoint-override", JSON_COMMENT, "json") + JSON_MESSAGE + JSON_PATHS
    s += "    patterns:\n"
    s += "      - pattern-either:\n"
    s += "          # Claude Code: the endpoint variables, in the env block of any settings file.\n"
    s += "          - patterns:\n"
    s += "              - pattern-inside: '\"env\": {...}'\n"
    s += "              - pattern: '\"$KEY\": \"$URL\"'\n"
    s += "              # A JSON key metavariable binds with its quotes.\n"
    s += mvr("$KEY", '^"(?:' + "|".join(CLAUDE_KEYS) + ')"$', 14)
    s += "          # Gemini CLI: the OTLP exporter that receives prompt telemetry.\n"
    s += "          - patterns:\n"
    s += "              - pattern-inside: '\"telemetry\": {...}'\n"
    s += "              - pattern: '\"otlpEndpoint\": \"$URL\"'\n"
    s += mvr("$URL", value_regex("claude-gemini"), 6, literal=True)
    s += metadata("MEDIUM", ["claude-code", "gemini-cli"], [
        "https://code.claude.com/docs/en/settings-reference#env",
        "https://code.claude.com/docs/en/env-vars",
        "https://code.claude.com/docs/en/permissions#what-runs-before-you-trust-a-folder",
        "https://code.claude.com/docs/en/llm-gateway",
        "https://github.com/google-gemini/gemini-cli/blob/v0.65.0/packages/core/src/telemetry/config.ts",
        "https://github.com/google-gemini/gemini-cli/blob/v0.65.0/docs/cli/telemetry.md",
    ])
    return s


# ---- agent-settings-endpoint-override-dotenv and -dotenv-generic (.env files) --------------

DOTENV_PATHS = """    paths:
      include:
        # .env at any depth, including .gemini/.env and .qwen/.env. The agents read no other
        # file names (.env.example, .env.production stay out).
        - ".env"
"""

# dotenv syntax: an optional export, KEY=value or KEY: value, an optional quote. A # comment
# line never matches, because the key must start the line.
DOTENV_REGEX = r"""(?xm)
{defines}
^ [ \t]*+ (?: export [ \t]++ )?+ (?: {vars} ) (?: [ \t]*+ = | : [ \t] ) [ \t]*+
\K ["'`]?+ """ + REMOTE_URL


def dotenv_patterns(groups, indent):
    """One pattern-regex per (client, variables) group, each with its client's vendors."""
    s = ""
    for comment, client, names in groups:
        s += " " * indent + "# " + comment + "\n"
        s += pregex(DOTENV_REGEX.replace("{defines}", defines(client)).replace("{vars}", " | ".join(names)), indent)
    return s


# Variable names only one agent uses, so a match is about that agent.
DOTENV_GROUPS = (
    ("Gemini CLI: the model endpoints and the telemetry exporter.", "gemini",
     ("GOOGLE_GEMINI_BASE_URL", "GOOGLE_VERTEX_BASE_URL", "CODE_ASSIST_ENDPOINT",
      "GEMINI_TELEMETRY_OTLP_ENDPOINT")),
    ("Qwen Code: the telemetry exporters (prompts are logged by default once telemetry is on).",
     "byok", ("QWEN_TELEMETRY_OTLP_ENDPOINT", "QWEN_TELEMETRY_OTLP_TRACES_ENDPOINT",
              "QWEN_TELEMETRY_OTLP_LOGS_ENDPOINT", "QWEN_TELEMETRY_OTLP_METRICS_ENDPOINT")),
    ("Aider (--openai-api-base) and Crush (a CRUSH_ copy wins over the shell's value).", "byok",
     ("AIDER_OPENAI_API_BASE", "CRUSH_OPENAI_API_ENDPOINT", "CRUSH_ANTHROPIC_API_ENDPOINT",
      "CRUSH_GEMINI_API_ENDPOINT", "CRUSH_AZURE_OPENAI_API_ENDPOINT")),
    ("The Continue CLI (cn): its hub API, which receives the login token.", "continue",
     ("CONTINUE_API_BASE",)),
)

DOTENV_COMMENT = """# Text rule over .env files, which Gemini CLI, Qwen Code, Aider, Crush and the Continue CLI
# load from the project. Only variable names that belong to one agent are matched here; the
# SDK-wide names those agents also read (OPENAI_BASE_URL, ANTHROPIC_BASE_URL, ...) are in
# agent-settings-endpoint-override-dotenv-generic, at LOW confidence, because a .env file
# often configures the application itself.
"""

DOTENV_MESSAGE = """    message: >-
      This committed .env file points a coding agent's model endpoint, login API, or prompt
      telemetry (Gemini CLI's GOOGLE_GEMINI_BASE_URL, GOOGLE_VERTEX_BASE_URL,
      CODE_ASSIST_ENDPOINT or GEMINI_TELEMETRY_OTLP_ENDPOINT; Qwen Code's
      QWEN_TELEMETRY_OTLP_*; Aider's AIDER_OPENAI_API_BASE; Crush's CRUSH_*_API_ENDPOINT; the
      Continue CLI's CONTINUE_API_BASE) at a host that is not the vendor's API and not on this
      machine or a private network. These agents load .env from the project they start in
      (Gemini CLI and Qwen Code .gemini/.env or .qwen/.env first), with no prompt in Qwen Code,
      Aider, Crush and cn, and in any trusted folder in Gemini CLI.
""" + WHY + "\n"


def dotenv_rule():
    s = header("agent-settings-endpoint-override-dotenv", DOTENV_COMMENT, "regex")
    s += DOTENV_MESSAGE + DOTENV_PATHS
    s += "    pattern-either:\n" + dotenv_patterns(DOTENV_GROUPS, 6)
    s += metadata("MEDIUM", ["gemini-cli", "qwen-code", "aider", "crush", "continue"], [
        "https://github.com/google-gemini/gemini-cli/blob/v0.65.0/packages/cli/src/config/settings.ts",
        "https://github.com/google-gemini/gemini-cli/blob/v0.65.0/packages/core/src/core/contentGenerator.ts",
        "https://github.com/google-gemini/gemini-cli/blob/v0.65.0/packages/core/src/code_assist/server.ts",
        "https://github.com/google-gemini/gemini-cli/blob/v0.65.0/docs/reference/configuration.md",
        "https://github.com/QwenLM/qwen-code/blob/v0.26.1/packages/cli/src/config/environment.ts",
        "https://github.com/QwenLM/qwen-code/blob/v0.26.1/packages/core/src/telemetry/config.ts",
        "https://github.com/Aider-AI/aider/blob/v0.86.0/aider/main.py",
        "https://github.com/charmbracelet/crush/blob/v0.98.2/internal/config/load.go",
        "https://github.com/continuedev/continue/blob/v1.5.45/extensions/cli/src/env.ts",
    ])
    return s


# SDK-wide names: Qwen Code reads OPENAI_BASE_URL and ANTHROPIC_BASE_URL; Aider hands every
# LiteLLM *_API_BASE (and OPENAI_BASE_URL / ANTHROPIC_BASE_URL) to LiteLLM 1.75; Crush's catalog
# fills its built-in providers from *_API_ENDPOINT.
GENERIC_VARS = ("OPENAI_BASE_URL", "OPENAI_API_BASE", "ANTHROPIC_BASE_URL", "ANTHROPIC_API_BASE",
                "AZURE_API_BASE", "AZURE_AI_API_BASE", "GEMINI_API_BASE", "VERTEXAI_API_BASE",
                "OPENROUTER_API_BASE", "MISTRAL_API_BASE", "GROQ_API_BASE", "COHERE_API_BASE",
                "DATABRICKS_API_BASE", "NEBIUS_API_BASE", "OLLAMA_API_BASE",
                "OPENAI_API_ENDPOINT", "ANTHROPIC_API_ENDPOINT", "GEMINI_API_ENDPOINT",
                "AZURE_OPENAI_API_ENDPOINT")

GENERIC_COMMENT = """# Text rule over .env files for the SDK-wide endpoint names that Qwen Code, Aider and Crush
# read from a project .env. LOW confidence: the same names often configure the application
# itself, and a developer who runs one of these agents in the repo still sends it their key.
# Agent-specific names are in agent-settings-endpoint-override-dotenv.
"""

GENERIC_MESSAGE = """    message: >-
      This committed .env file sets an OpenAI- or Anthropic-style endpoint variable to a host
      that is not a model vendor's API and not on this machine or a private network. Coding
      agents that load a project's .env without asking pick it up: Qwen Code (OPENAI_BASE_URL,
      ANTHROPIC_BASE_URL, for variables the shell hasn't set), Aider (the LiteLLM *_API_BASE
      names, overriding the shell), and Crush (*_API_ENDPOINT), and send the developer's own
      API key with each request. If the variable is for the application, keep the committed
      value local or on the vendor's API, and set the real one outside the repository.
""" + WHY + "\n"


def dotenv_generic_rule():
    s = header("agent-settings-endpoint-override-dotenv-generic", GENERIC_COMMENT, "regex")
    s += GENERIC_MESSAGE + DOTENV_PATHS
    s += dotenv_patterns([("SDK-wide endpoint variables.", "byok", GENERIC_VARS)], 4).replace(
        "    - pattern-regex", "    pattern-regex", 1)
    s += metadata("LOW", ["qwen-code", "aider", "crush"], [
        "https://github.com/QwenLM/qwen-code/blob/v0.26.1/packages/cli/src/config/environment.ts",
        "https://github.com/QwenLM/qwen-code/blob/v0.26.1/packages/core/src/models/constants.ts",
        "https://github.com/Aider-AI/aider/blob/v0.86.0/aider/main.py",
        "https://github.com/BerriAI/litellm/blob/v1.75.0-nightly/litellm/main.py",
        "https://github.com/charmbracelet/crush/blob/v0.98.2/main.go",
        "https://github.com/charmbracelet/catwalk/tree/v0.52.49/internal/providers/configs",
    ])
    return s


# ---- agent-settings-endpoint-override-toml (Codex .codex/config.toml) ----------------------

TOML_COMMENT = """# Regex, not a parser: OpenGrep has no TOML language. TOML comments start with #, so a key
# after a # on its line is commented out and skipped.
"""

TOML_MESSAGE = """    message: >-
      This committed Codex setting points the model endpoint (openai_base_url,
      chatgpt_base_url, a realtime base URL, or a model provider's base_url) at a host that is
      not OpenAI's API and not on this machine or a private network. Codex 0.128 and earlier
      apply a trusted project's .codex/config.toml, and the provider receives the developer's
      OpenAI key or ChatGPT login; Codex 0.129 and later ignore these keys in project files and
      warn at startup, so this matters for teams on older clients.
""" + WHY + "\n"

TOML_PATHS = """    paths:
      include:
        # Codex reads .codex/config.toml in every folder from the repo root down to where it
        # starts (profile files only from $CODEX_HOME).
        - ".codex/config.toml"
"""

# A key outside any comment, on its own or dotted / inline-table form, with a basic or literal
# string value. Keys may be quoted.
TOML_KEY = r"""^ [^\n\#]*? (?<![\w-]) ["']? (?: {keys} ) ["']? [\x20\t]*+ = [\x20\t]*+ \K ["']{{1,3}}+ """

TOML_TOP = r"""(?xm)
""" + "{defines}" + "\n" + TOML_KEY.format(keys="openai_base_url | chatgpt_base_url | experimental_realtime_ws_base_url | experimental_realtime_webrtc_call_base_url") + REMOTE_URL

# A provider's base_url: inside a [model_providers...] table (up to the next table header), or
# as a dotted key that names model_providers on its own line.
TOML_PROVIDER_TABLE = r"""(?xm)
^ [\x20\t]*+ \[ [\x20\t]*+ ["']? model_providers ["']? [\x20\t]*+ [.\]] [^\n]*+ \n
(?: (?! [\x20\t]*+ \[ ) [^\n]*+ (?: \n | \z ) )*+"""

TOML_PROVIDER_KEY = r"""(?xm)
""" + "{defines}" + "\n" + TOML_KEY.format(keys="base_url") + REMOTE_URL

TOML_PROVIDER_DOTTED = r"""(?xm)
""" + "{defines}" + r"""
^ [^\n\#]*? (?<![\w-]) ["']? model_providers ["']? [\x20\t]*+ \. [^\n\#=]*? (?<![\w-]) ["']? base_url ["']?
[\x20\t]*+ = [\x20\t]*+ \K ["']{1,3}+ """ + REMOTE_URL


def toml_rule():
    d = defines("codex")
    s = header("agent-settings-endpoint-override-toml", TOML_COMMENT, "regex") + TOML_MESSAGE + TOML_PATHS
    s += "    pattern-either:\n"
    s += "      # Top-level endpoint keys (also inside a [profiles.<name>] table).\n"
    s += pregex(TOML_TOP.replace("{defines}", d), 6)
    s += "      # base_url inside a [model_providers.<id>] table, or an inline table in [model_providers].\n"
    s += "      - patterns:\n"
    s += pregex(TOML_PROVIDER_TABLE, 10)
    s += pregex(TOML_PROVIDER_KEY.replace("{defines}", d), 10)
    s += "      # model_providers.<id>.base_url as a dotted key.\n"
    s += pregex(TOML_PROVIDER_DOTTED.replace("{defines}", d), 6)
    s += metadata("LOW", ["codex"], [
        "https://github.com/openai/codex/blob/rust-v0.164.0/codex-rs/config/src/loader/mod.rs",
        "https://github.com/openai/codex/blob/rust-v0.128.0/codex-rs/config/src/loader/mod.rs",
        "https://developers.openai.com/codex/config-reference",
    ])
    return s


# ---- agent-settings-endpoint-override-opencode (opencode and Kilo Code config) -------------

OPENCODE_COMMENT = """# Text rule over opencode.json(c) and kilo.json(c): OpenGrep's JSON parser skips .jsonc files.
"""

OPENCODE_MESSAGE = """    message: >-
      This committed opencode / Kilo Code setting points a model provider (options.baseURL, the
      Bedrock "endpoint" alias, or "api") or Kilo's codebase index (indexing baseUrl or the
      Qdrant url) at a host that is not a model vendor's API and not on this machine or a
      private network. A project's opencode.json(c), kilo.json(c), and .opencode/ or .kilo/
      files are loaded without a prompt and override the developer's own config, and the
      provider's stored or environment key is sent to that host (opencode 1.19, Kilo Code 7.8).
""" + WHY + "\n"

# Comments and whitespace between JSONC tokens, and a balanced object.
JSONC_DEFINE = r"""(?(DEFINE)
  (?<c> (?: \s++ | //[^\n]*+ | /\*(?s:.*?)\*/ )*+ )
  (?<obj> \{ (?: [^{}"/]++ | "(?:[^"\\]|\\.)*+" | //[^\n]*+ | /\*(?s:.*?)\*/ | / | (?&obj) )*+ \} )
)"""


def jsonc_region(key):
    """The object a top-level or nested member named `key` holds, outside comments."""
    return (r"""(?xm)
""" + JSONC_DEFINE + r"""
(?: ^[ \t]*+ | [{,] [ \t]*+ ) "{key}" (?&c) : (?&c) \K (?&obj)""").replace("{key}", key)


def jsonc_member(keys, client="byok"):
    """A member with one of `keys` and a remote URL value, on a line that isn't commented out.
    The walk to the key steps over strings, so a key name inside a string never matches."""
    return (r"""(?xm)
""" + defines(client) + r"""
^ (?: [^\n"/] | "(?:[^"\\\n]|\\.)*+" | /(?![/*]) )*? \K
" (?: """ + keys + r""" ) " [ \t]*+ : [ \t]*+ " """ + REMOTE_URL)


def opencode_rule():
    s = header("agent-settings-endpoint-override-opencode", OPENCODE_COMMENT, "regex")
    s += OPENCODE_MESSAGE + OPENCODE_PATHS
    s += "    pattern-either:\n"
    s += "      # provider.<id>.options.baseURL / endpoint, provider.<id>.api, and a model's provider.api.\n"
    s += "      - patterns:\n"
    s += pregex(jsonc_region("provider"), 10)
    s += pregex(jsonc_member("baseURL | endpoint | api"), 10)
    s += "      # Kilo Code codebase indexing: an embedding provider's baseUrl and the Qdrant url.\n"
    s += "      - patterns:\n"
    s += pregex(jsonc_region("indexing"), 10)
    s += pregex(jsonc_member("baseUrl | url"), 10)
    s += metadata("MEDIUM", ["opencode", "kilo-code"], [
        "https://github.com/anomalyco/opencode/blob/v1.19.4/packages/web/src/content/docs/providers.mdx",
        "https://github.com/anomalyco/opencode/blob/v1.19.4/packages/opencode/src/config/config.ts",
        "https://github.com/anomalyco/opencode/blob/v1.19.4/packages/opencode/src/provider/provider.ts",
        "https://github.com/Kilo-Org/kilocode/blob/v7.8.17/packages/opencode/src/config/config.ts",
        "https://github.com/Kilo-Org/kilocode/blob/v7.8.17/packages/opencode/src/kilocode/config/config.ts",
    ])
    return s


# ---- agent-settings-endpoint-override-qwen (Qwen Code .qwen/settings.json) -----------------

QWEN_ENV_KEYS = ("OPENAI_BASE_URL", "ANTHROPIC_BASE_URL", "QWEN_TELEMETRY_OTLP_ENDPOINT",
                 "QWEN_TELEMETRY_OTLP_TRACES_ENDPOINT", "QWEN_TELEMETRY_OTLP_LOGS_ENDPOINT",
                 "QWEN_TELEMETRY_OTLP_METRICS_ENDPOINT")

QWEN_COMMENT = """# Qwen Code's workspace settings: a model provider's baseUrl, the API-key login's baseUrl, the
# endpoint variables in the env block, and the telemetry exporters. Separate from the Claude
# Code / Gemini CLI rule because Qwen Code reads OPENAI_BASE_URL from its env block and Claude
# Code doesn't.
"""

QWEN_MESSAGE = """    message: >-
      This committed Qwen Code setting points the model endpoint (a modelProviders entry's
      baseUrl, security.auth.baseUrl, or OPENAI_BASE_URL / ANTHROPIC_BASE_URL in env) or the
      telemetry exporter at a host that is not a model vendor's API and not on this machine or
      a private network. Qwen Code 0.26 loads the project's .qwen/settings.json with no prompt
      (folder trust is off by default), and a provider entry's envKey names which of the
      developer's keys is sent to that host; telemetry logs prompt text by default once on.
""" + WHY + "\n"


def qwen_rule():
    s = header("agent-settings-endpoint-override-qwen", QWEN_COMMENT, "json") + QWEN_MESSAGE
    s += '    paths:\n      include:\n        - ".qwen/settings.json"\n'
    s += "    patterns:\n"
    s += "      - pattern-either:\n"
    s += "          # modelProviders.<auth type>[].baseUrl\n"
    s += "          - patterns:\n"
    s += "              - pattern-inside: '\"modelProviders\": {...}'\n"
    s += "              - pattern: '\"baseUrl\": \"$URL\"'\n"
    s += "          # security.auth.baseUrl (the OpenAI-compatible API key login)\n"
    s += "          - patterns:\n"
    s += "              - pattern-inside: '\"security\": {...}'\n"
    s += "              - pattern-inside: '\"auth\": {...}'\n"
    s += "              - pattern: '\"baseUrl\": \"$URL\"'\n"
    s += "          # The env block, applied for each variable the shell and .env haven't set.\n"
    s += "          - patterns:\n"
    s += "              - pattern-inside: '\"env\": {...}'\n"
    s += "              - pattern: '\"$KEY\": \"$URL\"'\n"
    s += mvr("$KEY", '^"(?:' + "|".join(QWEN_ENV_KEYS) + ')"$', 14)
    s += "          # The OTLP exporters.\n"
    s += "          - patterns:\n"
    s += "              - pattern-inside: '\"telemetry\": {...}'\n"
    s += "              - pattern: '\"$KEY\": \"$URL\"'\n"
    s += mvr("$KEY", '^"otlp(?:Traces|Logs|Metrics)?Endpoint"$', 14)
    s += mvr("$URL", value_regex("byok"), 6, literal=True)
    s += metadata("MEDIUM", ["qwen-code"], [
        "https://github.com/QwenLM/qwen-code/blob/v0.26.1/packages/cli/src/config/settingsSchema.ts",
        "https://github.com/QwenLM/qwen-code/blob/v0.26.1/packages/cli/src/config/trustedFolders.ts",
        "https://github.com/QwenLM/qwen-code/blob/v0.26.1/packages/core/src/models/modelConfigResolver.ts",
        "https://github.com/QwenLM/qwen-code/blob/v0.26.1/packages/core/src/telemetry/config.ts",
        "https://github.com/QwenLM/qwen-code/blob/v0.26.1/docs/users/configuration/auth.md",
    ])
    return s


# ---- agent-settings-endpoint-override-crush (Crush crush.json and crushrc) ----------------

CRUSH_COMMENT = """# Text rule over Crush's project config: crush.json / .crush.json (JSON, and the workspace
# .crush/crush.json) and crushrc / .crushrc (Bash with Crush builtins). One text rule covers
# both formats.
"""

CRUSH_MESSAGE = """    message: >-
      This committed Crush setting points a model provider (providers.<id>.base_url, or
      `provider add ... --base-url` in crushrc) at a host that is not a model vendor's API and
      not on this machine or a private network. Crush 0.98 loads crush.json and crushrc from
      every folder between where it starts and the repository root with no prompt, and a
      built-in provider whose base_url is overridden keeps sending its usual key (for example
      the OPENAI_API_KEY variable) to the new host.
""" + WHY + "\n"

CRUSHRC = r"""(?xm)
""" + "{defines}" + r"""
# provider add <id> ... --base-url URL, on one line or continued with backslashes. The match
# starts at the command, so a finding on a continued line points at its first line.
^ [ \t]*+ provider [ \t]++ add [ \t]++ (?: [^\n\\] | \\ (?s:.) )*? (?<![\w-]) --base-url (?: = | [ \t]++ )
["']?+ """ + REMOTE_URL


def crush_rule():
    s = header("agent-settings-endpoint-override-crush", CRUSH_COMMENT, "regex") + CRUSH_MESSAGE
    s += ('    paths:\n      include:\n        - "crush.json"\n        - ".crush.json"\n'
          '        - "crushrc"\n        - ".crushrc"\n')
    s += "    pattern-either:\n"
    s += "      # providers.<id>.base_url in crush.json.\n"
    s += "      - patterns:\n"
    s += pregex(jsonc_region("providers"), 10)
    s += pregex(jsonc_member("base_url"), 10)
    s += "      # provider add <id> --base-url <url> in crushrc.\n"
    s += pregex(CRUSHRC.replace("{defines}", defines("byok")), 6)
    s += metadata("MEDIUM", ["crush"], [
        "https://github.com/charmbracelet/crush/blob/v0.98.2/internal/config/load.go",
        "https://github.com/charmbracelet/crush/blob/v0.98.2/internal/config/config.go",
        "https://github.com/charmbracelet/crush/blob/v0.98.2/internal/shellconfig/provider.go",
        "https://github.com/charmbracelet/crush/blob/v0.98.2/docs/config/README.md",
    ])
    return s


# ---- agent-settings-endpoint-override-aider (Aider .aider.conf.yml, model settings) --------

AIDER_COMMENT = """# Text rule over Aider's YAML config files. Aider reads each from the working directory, the
# git root and the home folder; the project's copies win.
"""

AIDER_MESSAGE = """    message: >-
      This committed Aider setting points the model endpoint (openai-api-base, a set-env entry
      such as OPENAI_API_BASE=..., or a model's extra_params api_base) at a host that is not a
      model vendor's API and not on this machine or a private network. Aider 0.86 loads
      .aider.conf.yml and .aider.model.settings.yml from the working directory and the git
      root with no prompt, and LiteLLM sends the developer's own provider key (OPENAI_API_KEY,
      ANTHROPIC_API_KEY, ...) to that host.
""" + WHY + "\n"

LITELLM_VARS = tuple(v for v in GENERIC_VARS if not v.endswith("_API_ENDPOINT"))

AIDER_KEY = r"""(?xm)
""" + "{defines}" + r"""
^ [ \t]*+ ["']?+ openai-api-base ["']?+ [ \t]*+ : [ \t]++ \K ["']?+ """ + REMOTE_URL

AIDER_SET_ENV = r"""(?xm)
""" + "{defines}" + r"""
# A NAME=value entry of set-env, in block or flow style, outside a # comment.
^ [^\n\#]*? (?<![\w-]) (?: """ + " | ".join(LITELLM_VARS) + r""" ) [ \t]*+ = [ \t]*+ \K """ + REMOTE_URL

AIDER_API_BASE = r"""(?xm)
""" + "{defines}" + r"""
# extra_params: {api_base: ...} in .aider.model.settings.yml, block or flow style.
^ [^\n\#]*? (?<![\w-]) ["']?+ api_base ["']?+ [ \t]*+ : [ \t]++ \K ["']?+ """ + REMOTE_URL


def aider_rule():
    d = defines("byok")
    s = header("agent-settings-endpoint-override-aider", AIDER_COMMENT, "regex") + AIDER_MESSAGE
    s += ('    paths:\n      include:\n        - ".aider.conf.yml"\n'
          '        - ".aider.model.settings.yml"\n')
    s += "    pattern-either:\n"
    s += "      # openai-api-base: <url>\n"
    s += pregex(AIDER_KEY.replace("{defines}", d), 6)
    s += "      # set-env: [OPENAI_API_BASE=<url>, ...] with LiteLLM's endpoint variables.\n"
    s += pregex(AIDER_SET_ENV.replace("{defines}", d), 6)
    s += "      # A model's extra_params, passed straight to LiteLLM.\n"
    s += pregex(AIDER_API_BASE.replace("{defines}", d), 6)
    s += metadata("MEDIUM", ["aider"], [
        "https://github.com/Aider-AI/aider/blob/v0.86.0/aider/main.py",
        "https://github.com/Aider-AI/aider/blob/v0.86.0/aider/args.py",
        "https://github.com/Aider-AI/aider/blob/v0.86.0/aider/models.py",
        "https://github.com/BerriAI/litellm/blob/v1.75.0-nightly/litellm/main.py",
    ])
    return s


# ---- agent-settings-endpoint-override-continue (Continue .continue/ blocks, .continuerc.json)

CONTINUE_COMMENT = """# Text rule over Continue's workspace config: YAML blocks under .continue/ and the legacy
# .continuerc.json. apiBase only occurs on a model, so the key alone is enough.
"""

CONTINUE_MESSAGE = """    message: >-
      This committed Continue model sets apiBase to a host that is not a model vendor's API and
      not on this machine or a private network. Continue 2.0 merges the workspace's .continue/
      blocks (and .continuerc.json) into the developer's config once VS Code trusts the
      workspace, and a model whose apiKey names one of the developer's secrets
      (${{ secrets.NAME }}) sends it to that host when the model is in use. LOW confidence:
      the model has to be selected, or be the only one for its role.
""" + WHY + "\n"

CONTINUE_KEY = r"""(?xm)
""" + "{defines}" + r"""
# The walk to the key steps over strings and stops at a # or // comment.
^ (?: [^\n"'\#/] | "(?:[^"\\\n]|\\.)*+" | '[^'\n]*+' | /(?![/*]) )*? (?<![\w-]) \K
["']?+ apiBase ["']?+ [ \t]*+ : [ \t]*+ ["']?+ """ + REMOTE_URL


def continue_rule():
    s = header("agent-settings-endpoint-override-continue", CONTINUE_COMMENT, "regex") + CONTINUE_MESSAGE
    s += ('    paths:\n      include:\n        - ".continue/**/*.yaml"\n        - ".continue/**/*.yml"\n'
          '        # Continue reads every name ending in .continuerc.json; the glob needs the bare name too.\n'
          '        - ".continuerc.json"\n        - "*.continuerc.json"\n')
    s += pregex(CONTINUE_KEY.replace("{defines}", defines("byok")), 4).replace(
        "    - pattern-regex", "    pattern-regex", 1)
    s += metadata("LOW", ["continue"], [
        "https://github.com/continuedev/continue/blob/v2.0.0-vscode/core/config/loadLocalAssistants.ts",
        "https://github.com/continuedev/continue/blob/v2.0.0-vscode/core/config/yaml/loadYaml.ts",
        "https://github.com/continuedev/continue/blob/v2.0.0-vscode/core/config/yaml/LocalPlatformClient.ts",
        "https://github.com/continuedev/continue/blob/v2.0.0-vscode/core/config/json/loadRcConfigs.ts",
        "https://github.com/continuedev/continue/blob/v2.0.0-vscode/packages/config-yaml/src/schemas/models.ts",
    ])
    return s


def render() -> dict[Path, str]:
    """The rule files and the content this script generates for each."""
    return {
        RULE_DIR / "agent-settings-endpoint-override.yaml": json_rule(),
        RULE_DIR / "agent-settings-endpoint-override-dotenv.yaml": dotenv_rule(),
        RULE_DIR / "agent-settings-endpoint-override-toml.yaml": toml_rule(),
        RULE_DIR / "agent-settings-endpoint-override-opencode.yaml": opencode_rule(),
        RULE_DIR / "agent-settings-endpoint-override-dotenv-generic.yaml": dotenv_generic_rule(),
        RULE_DIR / "agent-settings-endpoint-override-qwen.yaml": qwen_rule(),
        RULE_DIR / "agent-settings-endpoint-override-crush.yaml": crush_rule(),
        RULE_DIR / "agent-settings-endpoint-override-aider.yaml": aider_rule(),
        RULE_DIR / "agent-settings-endpoint-override-continue.yaml": continue_rule(),
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
