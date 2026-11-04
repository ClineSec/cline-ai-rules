namespace ClaimsCopilot.Models;

public enum ClaimSeverity
{
    Minor,
    Moderate,
    Severe,
    Catastrophic,
}

public enum LineOfBusiness
{
    Auto,
    Homeowners,
    CommercialProperty,
}

public sealed record NoteSummaryRequest(string Persona, string Notes);

public sealed record TriageRequest(string ClaimId, string LineOfBusiness, string LossDescription, string Channel);

public sealed record LetterDraft(string ClaimId, string Markdown);

public sealed record LossRunRow(string ClaimId, string Region, decimal Paid, decimal Reserve);

public sealed record ReserveEstimate(string ClaimId, decimal Amount, string Formula);
