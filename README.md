# cline-ai-rules

OpenGrep rules for AI application code, MCP servers, and agent config files, mapped to the
OWASP Top 10 for LLM Applications 2026, the OWASP Top 10 for Agentic Applications, and the
OWASP MCP Top 10. They also work with Semgrep.

## Why this exists

**Problem:** SAST does not know what a prompt is. It sees an f-string, not a system prompt with
user input glued into it. It does not know that model output is untrusted, or that a tool
handler is a privilege boundary. And it never looks at the files that steer coding agents:
`CLAUDE.md`, `AGENTS.md`, Cursor rules, agent settings.

**Built:** a rule pack for that gap, targeting Python and TypeScript code built on the OpenAI,
Anthropic, LiteLLM, LangChain, Vercel AI SDK, and MCP SDKs, Go MCP servers (mcp-go and the
official Go SDK), Java code built on Spring AI and LangChain4j, C# code built on Semantic
Kernel, Microsoft.Extensions.AI, and the OpenAI .NET library, plus agent instruction and
config files. Every rule maps to OWASP, and every rule has test fixtures.

**Yours:** MIT-licensed. Scanners are cheap, fast, and give the same answer every time, so use
them where you can and save the expensive AI review for what a pattern can't see.

> **Status:** in active development. The pack aims for quality over count: a rule ships only
> with fixtures showing what it catches and what it deliberately leaves alone, and every rule is
> also run against the realistic projects in [`testbeds/`](testbeds/). Rules still change as
> testing turns up false positives and misses, so pin a commit if you need stable results.

## Quick start

```sh
git clone https://github.com/ClineSec/cline-ai-rules
opengrep scan --config cline-ai-rules/rules.yaml path/to/your/repo
```

`rules.yaml` bundles every rule in one file, so `--config` can also point at its raw URL.
Add `--taint-intrafile` to follow model output, and files downloaded from a model hub, through
helper functions within a file; without it, flows that cross a function boundary are missed.
To run one area only, point `--config` at a directory, for example `rules/agent-config/`.

Agent-config rules only look at the files they are written for (`CLAUDE.md`, `AGENTS.md`,
`.cursor/rules/`, `.claude/settings.json`, and so on), so scanning a whole repository is safe.
The `ai-cli-bypass-flag-invocation` and `ai-cli-default-auto-approve` rules also read CI
workflows, shell scripts, Makefiles, and `package.json` scripts; the `gha-ai-agent-*` rules read
only CI workflows. Secret findings (`mcp-config-plaintext-secret`, `secret-in-system-prompt`)
point at the line and never repeat the credential, so their output is safe to upload as SARIF.

A few rules are audits that flag text a person should read rather than a proven bug:
`mcp-tool-description-instructions` (+ `-ts`) matches prose in tool descriptions, and
`mcp-config-paas-remote-host` (INFO) flags MCP servers on free-hosting domains such as
`onrender.com` or `vercel.app`, which legitimate servers use too. If one is noisy for your
codebase, drop it with `--exclude-rule <id>` rather than turning off the area.

OpenGrep gives each rule 5 seconds per file (`--timeout`) and skips files over 1 MB
(`--max-target-bytes`). The taint rules for MCP servers and model output can run out of time
on source files of several thousand lines. A rule that times out reports nothing for that
file, and a file over the size limit is skipped by every rule. For a thorough scan, raise both:
`--timeout 30 --max-target-bytes 0`.

## Rules

- [Rule list](docs/rules.md): every rule, grouped by what it scans, with its languages, severity,
  and OWASP IDs.
- [OWASP coverage](docs/owasp-coverage.md): how many rules map to each OWASP category.
- [OWASP mapping](docs/owasp-mapping.md): how rules carry OWASP, AISVS, and ATLAS tags.

## How rules are tested

- **Fixtures:** every rule has a fixture next to it with cases it must flag and near-misses it
  must leave alone (`opengrep test rules/`).
- **Testbeds:** small, deliberately vulnerable projects in [`testbeds/`](testbeds/) that look
  like real code, scanned with the whole pack. Every finding must be expected and every expected
  finding must appear, in both default and `--taint-intrafile` modes.

## License

[MIT](LICENSE)
