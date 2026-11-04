#!/usr/bin/env python3
"""Generate the mcp-config-ephemeral-remote-host and mcp-config-paas-remote-host rule files.

Both families judge where an MCP server's traffic goes, in every client config format: JSON
(most clients), YAML (Continue), TOML (Codex), VS Code *.code-workspace files (JSONC, which
OpenGrep's JSON parser skips, so that variant is a regex rule) and Claude Code subagent front
matter (the Continue YAML checks, run on the front matter's mcpServers block). The host regexes are written once
here; the file paths and the TOML scaffolding come from gen_mcp_unpinned.py and
gen_mcp_plaintext_secret.py, so every MCP config family scans the same files and servers.

Each family has two checks:
- ANY: every string in a server entry (url, args, env, headers). Only hosts that are wrong
  wherever they appear go here.
- ENDPOINT: the server's own endpoint, which is the url / serverUrl / httpUrl value, or an
  argument of a stdio bridge to a remote server (mcp-remote, mcp-proxy, supergateway).

Edit this script, not the rule files. scripts/build.py regenerates them, and
scripts/build.py --check fails when a rule file differs from what this script produces.

Usage:
    python3 scripts/gen_mcp_remote_host.py    # rewrite the rule files
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

from gen_mcp_plaintext_secret import JSON_ROOT_URL, TOML_PAIR, TOML_STRING, TOML_TABLES, YAML_SCALAR
from gen_mcp_unpinned import (JSON_PATHS, JSON_SCOPE, JSONC_ARGS, JSONC_LINES, JSONC_MCP,
                              JSONC_PAIR, JSONC_SERVER, JSONC_STRING, SUBAGENT_NOTE, SUBAGENT_PATHS,
                              SUBAGENT_REFS, SUBAGENT_TRUST, TOML_EXTRACT, TOML_PATHS, TOML_SERVERS,
                              WORKSPACE_PATHS, YAML_PATHS, ind, mvr, pregex, subagent_patterns)

ROOT = Path(__file__).resolve().parent.parent
RULE_DIR = ROOT / "rules" / "agent-config" / "supply-chain"

# ---- host regexes --------------------------------------------------------------------------

DEFINE = r"""(?(DEFINE)
  (?<oct> 25[0-5] | 2[0-4]\d | 1\d\d | [1-9]?\d )
  # Where a host ends: a port, path, query, fragment, quote, separator, or the end.
  (?<he> (?= [:/?\#"'\\\s,;)\]}] | $ ) )
  # A DNS label. _ and labels past 63 characters are allowed on purpose: testbed payloads
  # use names under real tunnel domains that can never resolve.
  (?<lbl> [A-Za-z0-9_-]++ )
  (?<userinfo> (?: [^\s"'/@?\#\\]*+ @ )?+ )
  # Tunnel and out-of-band callback services: each name is a machine or listener that someone
  # started for the moment, not a service anyone vouches for (sources in the rule's references).
  (?<tunnel> (?i: trycloudflare\.com                          # Cloudflare quick tunnels
    | ngrok-free\.(?:app|dev|pizza) | ngrok\.(?:app|dev|io|pizza) # ngrok
    | loca\.lt | localtunnel\.me                                # localtunnel
    | lhr\.life | lhr\.rocks                                    # localhost.run
    | serveo\.net | serveousercontent\.com                      # Serveo
    | pinggy(?:-free)?\.link                                    # Pinggy
    | tunnelmole\.net | bore\.pub | loclx\.io                   # Tunnelmole, bore, LocalXpose
    | devtunnels\.ms | app\.github\.dev                         # Dev Tunnels, Codespaces ports
    | oast\.(?:pro|live|site|online|fun|me)                     # Interactsh
    | oastify\.com | burpcollaborator\.net ) )                 # Burp Collaborator
  # Free hosting platforms' default subdomains (sources in the rule's references).
  (?<paas> (?i: onrender\.com | fly\.dev | herokuapp\.com | vercel\.app | netlify\.app
    | railway\.app | workers\.dev | deno\.dev | deno\.net | replit\.app | koyeb\.app | hf\.space
    | modal\.run ) )
  # A public IPv4 address: not this-network, private (RFC 1918), shared (100.64/10, which
  # Tailscale uses), loopback, link-local, benchmarking, or multicast and above. The
  # documentation ranges (192.0.2/24, 198.51.100/24, 203.0.113/24) count as public.
  (?<pubip4> (?! (?:0|10|127)\. | 169\.254\. | 172\.(?:1[6-9]|2\d|3[01])\. | 192\.168\.
      | 100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\. | 198\.1[89]\. | (?:22[4-9]|2[3-5]\d)\. )
    (?&oct) (?:\.(?&oct)){3} )
  # A global unicast IPv6 literal (2000::/3).
  (?<pubip6> \[ [23][0-9A-Fa-f]{0,3} : [0-9A-Fa-f:.]*+ \] )
  # Names that only resolve on this machine or a private network: localhost, mDNS, the
  # reserved .internal TLD, home and corporate LANs, Tailscale MagicDNS, Consul's service DNS,
  # and other suffixes seen in committed agent configs that are not delegated TLDs (IANA root
  # zone list, version 2026102500), so no public DNS answers for them.
  (?<private> (?i: localhost | local | internal | lan | home\.arpa | corp | home | intranet
    | private | ts\.net | consul | proxy | lab | wg | monitor | hammernet ) )
  # A URL scheme starts here: not inside a longer scheme such as git+https. ${VAR:-https://...}
  # puts a - right before it.
  (?<url> (?<![A-Za-z0-9+.]) )
)"""

EPHEMERAL_ANY = rf"""(?x)
{DEFINE}
^ .*? (?:
    # A URL whose host is a tunnel or callback service, or a raw public IP address.
    (?&url) (?i:https?|wss?) :// (?&userinfo)
    (?: (?:(?&lbl)\.)* (?&tunnel) \.? | (?&pubip4) | (?&pubip6) ) (?&he)
    # A bare tunnel host name, as in --host <name>.trycloudflare.com.
  | (?<![A-Za-z0-9_.@/-]) (?:(?&lbl)\.)* (?&tunnel) \.? (?&he)
)"""

EPHEMERAL_ENDPOINT = rf"""(?x)
{DEFINE}
# Plain http:// or ws:// to a public host name or IP. Single-label names (docker compose and
# Kubernetes services), private names, and private or loopback addresses are left alone.
^ .*? (?&url) (?i:http|ws) :// (?&userinfo)
(?: (?! (?:(?&lbl)\.)* (?&private) \.? (?&he) ) (?:(?&lbl)\.)+ [A-Za-z][A-Za-z0-9-]*+ \.?
  | (?&pubip4) | (?&pubip6) ) (?&he)"""

PAAS_ENDPOINT = rf"""(?x)
{DEFINE}
^ .*? (?&url) (?i:https?|wss?) :// (?&userinfo) (?:(?&lbl)\.)+ (?&paas) \.? (?&he)"""

# The keys that hold a server's endpoint: url (Claude Code, Cursor, VS Code, Cline, Copilot
# CLI, Gemini CLI, Continue, Codex), serverUrl (Windsurf), httpUrl (Gemini CLI, deprecated).
URL_KEY = r"""^["']?(?:url|serverUrl|httpUrl)["']?$"""

# A stdio bridge to a remote server, as the command or one of its arguments (npx mcp-remote,
# uvx mcp-proxy, an mcp-proxy image, supergateway), with an optional version.
BRIDGE = r"""(?i)^["']?(?:[^"'\s]*[/\\])?(?:mcp-remote|mcp-proxy|supergateway)(?:[@:=][^"'\s/\\]*)?(?:\.cmd|\.exe)?["']?$"""
# A code-workspace server object holding a string that names the bridge, outside comments.
BRIDGE_JSONC = (r'''(?i)\A''' + JSONC_LINES
                + r'''"(?:[^"\s]*[/\\])?(?:mcp-remote|mcp-proxy|supergateway)(?:[@:=][^"\s/\\]*)?(?:\.cmd|\.exe)?"''')
# The same test over a TOML server's command and args text (metavariable-comparison regexes
# can't hold backslashes).
BRIDGE_TEXT = r"""(?is).*(^|[^a-z0-9_.-])(mcp-remote|mcp-proxy|supergateway)([^a-z0-9_-]|$)"""

# ---- families ------------------------------------------------------------------------------

FAMILIES = {
    "ephemeral": {
        "id": "mcp-config-ephemeral-remote-host",
        "any": EPHEMERAL_ANY,
        "endpoint": EPHEMERAL_ENDPOINT,
        # VS Code input defaults: a ${input:id} in a url resolves to the default unless the
        # user types something else. (The workspace twin's string branch already covers them.)
        "inputs": True,
        "severity": "WARNING",
        "message": """    message: >-
      This MCP server talks to a host that identifies no one: a tunnel or out-of-band callback
      service (trycloudflare.com, ngrok, localtunnel, localhost.run, Serveo, Interactsh, ...),
      a raw public IP address, or a public host over plain http://. A tunnel name is whatever
      machine started the tunnel, for as long as it runs, and whoever holds it serves the tool
      list, tool descriptions and results that the agent trusts and acts on. In August 2026 the
      Deadbugz campaign opened pull requests adding remote MCP servers on throwaway hosts
      (first a trycloudflare.com quick tunnel) that turned malicious after a few calls. Plain
      http lets anyone on the network path read the request headers and rewrite tool
      descriptions. Point the client at the vendor's own https endpoint or a server on a domain
      your team owns, and keep personal tunnels in user-level config, not the project.
""",
        "subcategory": "audit",
        "confidence": """      # Tunnel and callback hosts and raw public IPs are almost never a vetted server; plain
      # http to a public name is cleartext whatever the network.
      confidence: HIGH
      likelihood: MEDIUM
      impact: HIGH
""",
        "aisvs": ['"v1.01-C10.1.1 - Component Integrity"', '"v1.01-C10.3.1 - Secure Transport"'],
        "cwe": ['"CWE-829: Inclusion of Functionality from Untrusted Control Sphere"',
                '"CWE-319: Cleartext Transmission of Sensitive Information"'],
        "refs": """        - https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/do-more-with-tunnels/trycloudflare/
        - https://ngrok.com/docs/universal-gateway/domains
        - https://github.com/localtunnel/localtunnel/blob/master/README.md
        - https://localhost.run/docs/custom-domains
        - https://serveo.net/docs
        - https://pinggy.io/docs/http_tunnels/
        - https://github.com/robbie-cahill/tunnelmole-client/blob/main/README.md
        - https://github.com/ekzhang/bore/blob/main/README.md
        - https://localxpose.io/docs/tunnels/http
        - https://learn.microsoft.com/en-us/azure/developer/dev-tunnels/security
        - https://docs.github.com/en/codespaces/developing-in-a-codespace/forwarding-ports-in-your-codespace
        - https://github.com/projectdiscovery/interactsh/blob/main/README.md
        - https://portswigger.net/burp/documentation/desktop/settings/project/collaborator
""",
    },
    "paas": {
        "id": "mcp-config-paas-remote-host",
        "any": None,
        "endpoint": PAAS_ENDPOINT,
        "severity": "INFO",
        "message": """    message: >-
      This MCP server's endpoint is a default subdomain on a public hosting platform
      (*.onrender.com, *.vercel.app, *.workers.dev, *.hf.space, ...). Anyone can create one in
      minutes, the name says nothing about who runs it, and whoever runs it controls the tool
      descriptions and results the agent acts on. In August 2026 the Deadbugz campaign opened
      pull requests adding a server on an onrender.com subdomain that turned malicious after
      its first few calls. Many servers on these platforms are legitimate, so confirm who
      operates this one and review it like a new dependency; prefer the vendor's own domain or
      one your team owns.
""",
        "subcategory": "audit",
        "confidence": """      # Many legitimate servers live on these platforms; the rule can't tell who owns the
      # subdomain, so it is a prompt to check, not a finding of fault.
      confidence: LOW
      likelihood: LOW
      impact: HIGH
""",
        "aisvs": ['"v1.01-C10.1.2 - Component Integrity"'],
        "cwe": ['"CWE-829: Inclusion of Functionality from Untrusted Control Sphere"'],
        "refs": """        - https://render.com/docs/web-services
        - https://fly.io/docs/networking/services/
        - https://devcenter.heroku.com/articles/custom-domains
        - https://vercel.com/docs/deployments/generated-urls
        - https://docs.netlify.com/manage/domains/get-started-with-domains/
        - https://docs.railway.com/networking/public-networking
        - https://developers.cloudflare.com/workers/configuration/routing/workers-dev/
        - https://docs.deno.com/deploy/reference/domains/
        - https://docs.replit.com/cloud-services/deployments/custom-domains
        - https://www.koyeb.com/docs/run-and-scale/domains
        - https://huggingface.co/docs/hub/spaces-embed
        - https://modal.com/docs/guide/webhook-urls
""",
    },
}

COMMON_REFS = """        - https://www.pillar.security/blog/deadbugz-currently-active-mcp-supply-chain-campaign
        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP09-2025%E2%80%93Shadow-MCP-Servers.md
        - https://github.com/OWASP/www-project-mcp-top-10/blob/165fe0f78ef104459237b4a8e0f6e78db9b02391/2025/MCP04-2025%E2%80%93Software-Supply-Chain-Attacks%26Dependency-Tampering.md
        - https://github.com/GenAI-Security-Project/GenAI-LLM-Top10/blob/main/2026/final/LLM04_SupplyChain.md
"""

BRIDGE_REFS = """        - https://github.com/geelen/mcp-remote/blob/373f7320f6afd1fdb00e0168826a3cea99102241/README.md
        - https://github.com/sparfenyuk/mcp-proxy/blob/701a0453487d1b28c8f9806ee4863674c70210dd/README.md
        - https://github.com/supercorp-ai/supergateway/blob/0797a8192f3712d572c740724c70cc01ae67f0a1/README.md
"""

FORMAT_REFS = {
    "json": """        - https://code.claude.com/docs/en/mcp
        - https://cursor.com/docs/context/mcp
        - https://code.visualstudio.com/docs/copilot/reference/mcp-configuration
        - https://docs.devin.ai/desktop/cascade/mcp
        - https://github.com/google-gemini/gemini-cli/blob/09d81bf116b6f0ef084731dc996aa9d56438bb70/packages/core/src/config/config.ts
        - https://github.com/cline/cline/blob/1619168bdeb570aa233d0f0a9af1d332d83a2816/apps/vscode/src/services/mcp/schemas.ts
        - https://docs.continue.dev/customize/deep-dives/mcp
""",
    "yaml": """        - https://docs.continue.dev/customize/deep-dives/mcp
        - https://github.com/continuedev/continue/blob/5522c6f44ca0ac3528b37244818fbfa39b5af470/packages/config-yaml/src/schemas/mcp/index.ts
""",
    "toml": """        - https://learn.chatgpt.com/docs/extend/mcp?surface=cli
        - https://github.com/openai/codex/blob/342ed69a174c206c1de52a59491b131e0753cfa5/codex-rs/config/src/mcp_types.rs
""",
    "workspace": """        - https://code.visualstudio.com/docs/copilot/reference/mcp-configuration
        - https://github.com/microsoft/vscode/blob/1.143.1/src/vs/platform/mcp/common/mcpResourceScannerService.ts
""",
    "subagent": SUBAGENT_REFS,
}

TECHNOLOGY = {
    "json": "[mcp, claude-code, claude-desktop, cursor, vscode, cline, windsurf, gemini-cli, continue]",
    "yaml": "[mcp, continue]",
    "toml": "[mcp, codex]",
    "workspace": "[mcp, vscode]",
    "subagent": "[mcp, claude-code]",
}

SUFFIX = {"json": "", "yaml": "-yaml", "toml": "-toml", "workspace": "-workspace",
          "subagent": "-subagent"}



def sync_note(fam_id, fmt):
    others = [f"{fam_id}{SUFFIX[f]}.yaml" for f in SUFFIX if f != fmt]
    text = (f"Generated by scripts/gen_mcp_remote_host.py, which holds the host regexes shared with "
            f"{', '.join(others[:-1])} and {others[-1]}, and takes the file paths from "
            f"scripts/gen_mcp_unpinned.py. Edit the script and run scripts/build.py; build.py "
            f"--check fails if this file drifts.")
    return textwrap.fill(text, 92, initial_indent="# ", subsequent_indent="# ",
                         break_on_hyphens=False) + "\n"


def reflow(message):
    """A folded message scalar rewrapped to the pack's line width."""
    head, body = message.split("\n", 1)
    text = " ".join(body.split())
    return (head + "\n" + textwrap.fill(text, 96, initial_indent=" " * 6,
                                         subsequent_indent=" " * 6, break_on_hyphens=False) + "\n")


def metadata(fam, fmt):
    s = f"""    metadata:
      category: security
      subcategory: [{fam['subcategory']}]
      pack-category: agent-config
      owasp-llm:
        - "LLM04:2026 - Supply Chain"
        - "LLM03:2025 - Supply Chain"
      owasp-agentic:
        - "ASI04 - Agentic Supply Chain Vulnerabilities"
      owasp-mcp:
        - "MCP09:2025 - Shadow MCP Servers"
        - "MCP04:2025 - Software Supply Chain Attacks & Dependency Tampering"
      owasp-aisvs:
"""
    s += "".join(f"        - {a}\n" for a in fam["aisvs"])
    s += """      mitre-atlas:
        - "AML.T0010.005 - AI Supply Chain Compromise: AI Agent Tool"
      cwe:
"""
    s += "".join(f"        - {c}\n" for c in fam["cwe"])
    s += fam["confidence"]
    s += f"      technology: {TECHNOLOGY[fmt]}\n"
    s += "      references:\n" + COMMON_REFS + fam["refs"] + FORMAT_REFS[fmt] + BRIDGE_REFS
    return s


# ---- format scaffolding --------------------------------------------------------------------

def json_checks(fam, n):
    pad = " " * n
    out = ""
    if fam["any"]:
        out += f"{pad}# Any string in the entry: url, args, env, headers.\n"
        out += f"{pad}- patterns:\n{pad}    - pattern: '\"$V\"'\n"
        out += mvr("$V", fam["any"], n + 4, literal=True)
    out += f"{pad}# The server's endpoint: url, serverUrl (Windsurf), httpUrl (Gemini CLI).\n"
    out += f"{pad}- patterns:\n{pad}    - pattern: '\"$K\": \"$V\"'\n"
    out += mvr("$K", URL_KEY, n + 4, literal=True)
    out += mvr("$V", fam["endpoint"], n + 4, literal=True)
    out += f"{pad}# A stdio bridge to a remote server: the endpoint is one of its arguments.\n"
    out += f"""{pad}- patterns:
{pad}    - pattern-either:
{pad}        - pattern-inside: '{{..., "command": "$B", ...}}'
{pad}        - pattern-inside: '{{..., "args": [..., "$B", ...], ...}}'
"""
    out += mvr("$B", BRIDGE, n + 4, literal=True)
    out += f"{pad}    - pattern-inside: '\"args\": [...]'\n{pad}    - pattern: '\"$V\"'\n"
    out += mvr("$V", fam["endpoint"], n + 4, literal=True)
    return out


def yaml_checks(fam, n):
    pad = " " * n
    out = ""
    if fam["any"]:
        out += f"{pad}# Any scalar in the entry: url, args, env, requestOptions.headers.\n"
        out += f"{pad}- patterns:\n{pad}    - pattern: $V\n"
        out += mvr("$V", YAML_SCALAR, n + 4, literal=True)
        out += mvr("$V", fam["any"], n + 4, literal=True)
    out += f"{pad}# The server's endpoint.\n"
    out += f"{pad}- patterns:\n{pad}    - pattern: 'url: $V'\n"
    out += mvr("$V", YAML_SCALAR, n + 4, literal=True)
    out += mvr("$V", fam["endpoint"], n + 4, literal=True)
    out += f"{pad}# A stdio bridge to a remote server: the endpoint is one of its arguments.\n"
    out += f"""{pad}- patterns:
{pad}    - pattern-either:
{pad}        - pattern-inside: |
{pad}            command: $B
{pad}            ...
{pad}        - pattern-inside: 'args: [..., $B, ...]'
"""
    out += mvr("$B", BRIDGE, n + 4, literal=True)
    out += f"{pad}    - pattern-inside: 'args: [...]'\n{pad}    - pattern: $V\n"
    out += mvr("$V", YAML_SCALAR, n + 4, literal=True)
    out += mvr("$V", fam["endpoint"], n + 4, literal=True)
    return out


def string_check(walker_string, regex, n):
    """A regex-language branch: each string (binding V) that matches regex."""
    pad = " " * n
    return f"{pad}- patterns:\n" + pregex(walker_string, n + 4) + mvr("$V", regex, n + 4, literal=True)


def toml_checks(fam, n):
    pad = " " * n
    out = f"{pad}# Strings and url = \"...\" in any MCP server table.\n{pad}- patterns:\n"
    out += ind(TOML_TABLES, n - 2)
    out += f"""{pad}    - metavariable-pattern:
{pad}        metavariable: $TABLE
{pad}        language: regex
{pad}        patterns:
{pad}          - pattern-either:
"""
    m = n + 12
    if fam["any"]:
        out += " " * m + "# Each string, outside comments.\n"
        out += string_check(TOML_STRING, fam["any"], m)
    out += " " * m + "# The server's endpoint.\n"
    out += " " * m + f"- patterns:\n" + " " * m + f"    - pattern-regex: {TOML_PAIR}\n"
    out += mvr("$K", URL_KEY, m + 4, literal=True)
    out += mvr("$V", fam["endpoint"], m + 4, literal=True)
    out += f"{pad}# A stdio bridge to a remote server: the endpoint is one of its arguments.\n{pad}- patterns:\n"
    out += ind(TOML_SERVERS, n - 2)
    out += f"""{pad}    # Drops candidate matches that bound no server; without it the metavariable-pattern
{pad}    # below reports "$SRV is not in scope" as an engine error.
{pad}    - metavariable-regex:
{pad}        metavariable: $SRV
{pad}        regex: (?s).
{pad}    - metavariable-pattern:
{pad}        metavariable: $SRV
{pad}        language: regex
{pad}        patterns:
{pad}          - pattern-regex: {TOML_EXTRACT}
{pad}          - metavariable-comparison:
{pad}              comparison: re.match("{BRIDGE_TEXT}", str($CMD)) or re.match("{BRIDGE_TEXT}", str($ARGS))
{pad}          # Each string in the array: "basic" (with escapes) or 'literal'.
{pad}          - metavariable-pattern:
{pad}              metavariable: $ARGS
{pad}              language: regex
{pad}              patterns:
{pad}                - pattern-either:
{pad}                    - pattern-regex: '"(?<V>(?:[^"\\\\\\n]|\\\\.)*)"'
{pad}                    - pattern-regex: '\'\'(?<V>[^\'\'\\n]*)\'\''
"""
    out += mvr("$V", fam["endpoint"], n + 16, literal=True)
    return out


def workspace_checks(fam, n):
    pad = " " * n
    out = ""
    if fam["any"]:
        out += f"{pad}# Each string, outside comments: url, args, env, headers.\n"
        out += string_check(JSONC_STRING, fam["any"], n)
    out += f"{pad}# The server's endpoint.\n"
    out += f"{pad}- patterns:\n" + pregex(JSONC_PAIR, n + 4)
    out += mvr("$K", URL_KEY, n + 4, literal=True)
    out += mvr("$V", fam["endpoint"], n + 4, literal=True)
    out += f"{pad}# A stdio bridge to a remote server: the endpoint is one of its arguments.\n"
    out += f"{pad}- patterns:\n" + pregex(JSONC_SERVER, n + 4)
    out += mvr("$SRV", BRIDGE_JSONC, n + 4, literal=True)
    out += f"""{pad}    - metavariable-pattern:
{pad}        metavariable: $SRV
{pad}        language: regex
{pad}        patterns:
""" + pregex(JSONC_ARGS, n + 10) + f"""{pad}          - metavariable-pattern:
{pad}              metavariable: $ARGS
{pad}              language: regex
{pad}              patterns:
""" + pregex(JSONC_STRING, n + 16)
    out += mvr("$V", fam["endpoint"], n + 16, literal=True)
    return out


def header(fam, fmt, lang):
    rid = fam["id"] + SUFFIX[fmt]
    s = f"rules:\n  - id: {rid}\n"
    if lang == "regex":
        s += ("    # Regex, not a parser: OpenGrep has no TOML support.\n" if fmt == "toml" else
              "    # Regex, not JSON: OpenGrep's JSON parser skips *.code-workspace files (unknown\n"
              "    # extension), even when paths.include names them.\n")
    elif fmt == "subagent":
        s += SUBAGENT_NOTE
    s += ind(sync_note(fam["id"], fmt), 4)
    s += f"    languages: [{lang}]\n    severity: {fam['severity']}\n"
    if fmt == "subagent":
        s += reflow(fam["message"].replace("This MCP server", "This subagent's inline MCP server", 1)
                    + SUBAGENT_TRUST)
    else:
        s += fam["message"]
    return s


def json_rule(fam):
    s = header(fam, "json", "json") + JSON_PATHS + "    patterns:\n"
    if not fam.get("inputs"):
        s += JSON_SCOPE + JSON_ROOT_URL
        s += "      - pattern-either:\n" + json_checks(fam, 10)
    else:
        s += "      - pattern-either:\n          - patterns:\n"
        s += ind(JSON_SCOPE, 8) + ind(JSON_ROOT_URL, 8)
        s += "              - pattern-either:\n" + json_checks(fam, 18)
        s += """          # A VS Code input whose default is such a host: a "${input:id}" url resolves to it
          # unless the user types something else, so the default needs no tracing to a server.
          - patterns:
              - pattern-inside: '"inputs": [...]'
              - pattern: '"default": "$V"'
"""
        s += mvr("$V", fam["any"], 14, literal=True)
    s += "      - focus-metavariable: $V\n" + metadata(fam, "json")
    return s


def yaml_rule(fam):
    s = header(fam, "yaml", "yaml") + YAML_PATHS
    s += "    patterns:\n      - pattern-inside: 'mcpServers: [...]'\n      - pattern-either:\n"
    s += yaml_checks(fam, 10)
    s += "      - focus-metavariable: $V\n" + metadata(fam, "yaml")
    return s


def toml_rule(fam):
    s = header(fam, "toml", "regex") + TOML_PATHS
    s += "    patterns:\n      - pattern-either:\n" + toml_checks(fam, 10)
    s += "      - focus-metavariable: $V\n" + metadata(fam, "toml")
    return s


def workspace_rule(fam):
    s = header(fam, "workspace", "regex") + WORKSPACE_PATHS
    s += "    patterns:\n" + pregex(JSONC_MCP, 6)
    s += """      - metavariable-pattern:
          metavariable: $MCP
          language: regex
          patterns:
            - pattern-either:
"""
    s += workspace_checks(fam, 16)
    s += "      - focus-metavariable: $V\n" + metadata(fam, "workspace")
    return s


def subagent_rule(fam):
    s = header(fam, "subagent", "generic") + SUBAGENT_PATHS
    s += subagent_patterns(yaml_checks(fam, 16))
    s += "      - focus-metavariable: $V\n" + metadata(fam, "subagent")
    return s


def render() -> dict[Path, str]:
    """The rule files and the content this script generates for each."""
    out = {}
    for fam in FAMILIES.values():
        out[RULE_DIR / f"{fam['id']}.yaml"] = json_rule(fam)
        out[RULE_DIR / f"{fam['id']}-yaml.yaml"] = yaml_rule(fam)
        out[RULE_DIR / f"{fam['id']}-toml.yaml"] = toml_rule(fam)
        out[RULE_DIR / f"{fam['id']}-workspace.yaml"] = workspace_rule(fam)
        out[RULE_DIR / f"{fam['id']}-subagent.yaml"] = subagent_rule(fam)
    return out


def main() -> int:
    for path, content in render().items():
        if not path.exists() or path.read_text() != content:
            path.write_text(content)
            print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
