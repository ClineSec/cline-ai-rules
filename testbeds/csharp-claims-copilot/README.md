# csharp-claims-copilot (testbed)

**Intentionally vulnerable.** A small ASP.NET Core service that helps insurance claims
adjusters, built on Semantic Kernel with Microsoft.Extensions.AI and the OpenAI .NET library,
used to test `cline-ai-rules` against C# code that looks like a real project. Do not deploy it
or copy patterns from it, and do not build or run it (`dotnet` included): it is scanned as data.

Every payload is inert: hosts use `.invalid`, the model is the `example-org` placeholder, the
API key is read from configuration that holds nothing, the fixed tool recipes are `ls -l` and
`du -sh .`, and the model-written reporting SQL targets a made-up `loss_run_v` view.
Expected findings are listed in `expectations.yaml`.

What is in it (under `src/ClaimsCopilot/`):

- `Controllers/ClaimNotesController`: a note summary whose system prompt carries the
  `X-Adjuster-Region` gateway header through a `PromptLibrary` helper, next to a persona picked
  from a frozen table and a supervisor route that checks the region against the supported set
  first. A customer-letter preview renders the model's markdown with Markdig into a `text/html`
  response, next to an HtmlSanitizer-cleaned twin and a `text/markdown` one.
- `Endpoints/TriageEndpoints`: minimal APIs. A greeting route puts the route's channel into
  `ChatOptions.Instructions`; a first-notice handler (a method group) splices request fields into
  a raw-string `ChatRole.System` message. The triage handler parses the line of business into an
  enum and picks system text from a table, and stays quiet.
- `Hubs/AdjusterHub`: a SignalR hub whose `Ask` method builds a Semantic Kernel
  `ChatCompletionAgent` with the caller's specialty in `Instructions`, next to a persona lookup.
- `Reporting/LossRunReportService`: text-to-SQL. A prompt function held in a field writes a
  `WHERE` filter that Dapper runs, and an inline prompt's SQL goes into an Npgsql
  `CommandText`; next to an allowlisted sort column and EF Core's parameterized `ExecuteSqlAsync`.
- `Automation/ReserveCalculator`: a typed `IChatClient` response's formula is evaluated with
  Roslyn `CSharpScript`, next to a model number parsed with `decimal.Parse` first.
- `Automation/DocumentToolsRunner`: an OpenAI `ChatClient` completion's text parts, joined
  through a LINQ `Where`/`Select` chain, run through `/bin/sh -c` via `ProcessStartInfo.ArgumentList`, next to a recipe picked by name from a fixed
  table and a model-chosen file name passed to `pdftotext` as a plain argument.
- `Components/ClaimTimeline.razor.cs`: Blazor code-behind that wraps Markdig output of model
  text in a `MarkupString`, next to a sanitized tip and a plain-text summary.
- `Components/CoverageExplainer.razor`: a Blazor component whose `@code` block asks the kernel
  to explain the policy wording and whose markup wraps the Markdig output in a `MarkupString`,
  next to sanitized exclusions and an encoded disclaimer.

`tests/ClaimsCopilot.Tests` holds xUnit tests for the prompt library.
