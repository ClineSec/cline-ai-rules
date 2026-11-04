# java-ops-desk (testbed)

**Intentionally vulnerable.** A small Spring Boot service that helps an IT operations team
triage incidents, used to test `cline-ai-rules` against Java code that looks like a real
project. Do not deploy it or copy patterns from it.

Every payload is inert: suggested commands are harmless (`uptime`, `df -h`), hosts use
`example.com` and `.invalid`, models use the `example-org` placeholder, keys come from
environment variables that hold nothing real, and the model-written reporting SQL runs against a
made-up, read-only incident warehouse. Expected findings are listed in `expectations.yaml`.

What is in it:

- `web/RunbookController`: Spring AI `ChatClient` routes. A runbook Q&A endpoint puts the
  caller's team and tier headers into the system prompt (through a helper and a
  `PromptSystemSpec` template parameter), next to a persona picked from a constant table and an
  answer that stays in the user turn. A summary page returns model text from a GET handler with
  no `produces`, which Spring serves as `text/html` to a browser, next to a plain-text twin and
  a JSON one.
- `web/StatusPageController`: a status-page preview that renders the model's markdown with
  commonmark into an HTML `ResponseEntity`, and a servlet-style export, next to a renderer with
  `escapeHtml(true)` and `sanitizeUrls(true)` and an `HtmlUtils`-escaped fragment.
- `handoff/ShiftHandoffController`: a LangChain4j AI service declared in the same file, whose
  `@SystemMessage` template takes the team name from the request (by parameter name, as Spring
  Boot compiles with `-parameters`), and an `AiServices` builder whose system message provider
  reads a request field; the tone variable and the user message are server-chosen or in the
  user turn.
- `diagnostics/DiagnosticsService`: a Spring AI `ChatModel` suggests a shell command that
  runs through `sh -c`, next to an allowlisted command and a `git` argument.
- `diagnostics/AlertRuleEvaluator`: the model rewrites an alert rule as a SpEL condition that
  is evaluated with SpEL's default context, next to the same condition evaluated read-only with a
  `SimpleEvaluationContext`.
- `reporting/ReportQueryService`: text-to-SQL on LangChain4j's `ChatModel`, run through
  `JdbcTemplate` and through a native-query helper on JPA, next to bound parameters, an
  allowlisted column, and a checked table name.
- `crush.json`: Crush setup for the team, with the built-in Anthropic provider moved to a
  caching gateway, next to a local Ollama provider.
