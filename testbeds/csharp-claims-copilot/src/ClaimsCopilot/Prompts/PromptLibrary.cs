using System.Collections.Frozen;

namespace ClaimsCopilot.Prompts;

/// <summary>
/// Server-side prompt text. Personas and regional guidance are picked from these tables by key,
/// so request values never become system text themselves.
/// </summary>
public static class PromptLibrary
{
    public static readonly FrozenDictionary<string, string> Personas = new Dictionary<string, string>
    {
        ["desk-adjuster"] = "You are a desk adjuster's assistant. Summarize claim notes factually and flag missing documents.",
        ["field-adjuster"] = "You are a field adjuster's assistant. Focus on inspection findings and photos still to request.",
        ["supervisor"] = "You are a claims supervisor's assistant. Highlight reserve changes and coverage questions.",
    }.ToFrozenDictionary();

    public static readonly FrozenSet<string> SupportedRegions = new[] { "northeast", "midwest", "south", "west" }.ToFrozenSet();

    public const string SummaryGuardrails =
        "Never state a coverage decision. Never include policyholder phone numbers or bank details.";

    public static string AdjusterPreamble(string region) =>
        $"You assist adjusters in the {region} region. {SummaryGuardrails}";

    public static string LetterInstructions(string tone) =>
        $"Draft a customer letter in markdown. Keep a {tone} tone and avoid legal conclusions.";
}
