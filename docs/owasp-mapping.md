# How rules map to OWASP

Each rule's metadata carries OWASP tags as lists, with IDs and titles written exactly as OWASP writes them:

```yaml
metadata:
  owasp-llm:
    - "LLM10:2026 - Improper Output Handling"
    - "LLM05:2025 - Improper Output Handling"   # 2025 compatibility tag
  owasp-agentic:
    - "ASI05 - Unexpected Code Execution (RCE)"
```

- The primary mapping is the latest OWASP release of each list. The previous edition's ID is
  kept as a compatibility tag, because the 2026 LLM list renumbered most categories.
- Agent and tool rules also carry Agentic Top 10 tags. MCP rules carry MCP Top 10 tags; that
  list is still in beta and its IDs may change.
- [`taxonomy/owasp.yaml`](../taxonomy/owasp.yaml) holds every allowed ID and title, and the build
  fails on anything else. The full metadata schema is in [CONTRIBUTING.md](../CONTRIBUTING.md).
- The generated `rules.yaml` also copies every OWASP tag into the standard `owasp` field, so
  SARIF consumers (GitHub code scanning, DevSecOps pipelines) see them as rule tags.

Rules can also carry two finer-grained mappings, each checked against a pinned release:

```yaml
  owasp-aisvs:        # OWASP AI Security Verification Standard 1.01: the requirement the code fails
    - "v1.01-C7.1.1 - Output Format Enforcement"
  mitre-atlas:        # MITRE ATLAS 2026.09: the attack technique the pattern enables
    - "AML.T0050 - Command and Scripting Interpreter"
```

AISVS tags use AISVS's own versioned citation form with the section title, and are copied into
the SARIF `owasp` tags too. ATLAS tags stay in the rule metadata (JSON output and `rules.yaml`),
since SARIF tags would label them as OWASP. The ID lists in
[`taxonomy/aisvs.yaml`](../taxonomy/aisvs.yaml) and [`taxonomy/atlas.yaml`](../taxonomy/atlas.yaml)
are generated from the upstream releases by `scripts/update_taxonomy.py`.
