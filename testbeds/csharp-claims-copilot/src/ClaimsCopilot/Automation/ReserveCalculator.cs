using System.Globalization;
using ClaimsCopilot.Models;
using Microsoft.CodeAnalysis.CSharp.Scripting;
using Microsoft.CodeAnalysis.Scripting;
using Microsoft.Extensions.AI;

namespace ClaimsCopilot.Automation;

/// <summary>
/// Suggests an initial reserve. The model proposes a formula over the claim's figures and the
/// calculator evaluates it so the adjuster sees the arithmetic.
/// </summary>
public sealed class ReserveCalculator(IChatClient client)
{
    private static readonly ScriptOptions FormulaOptions = ScriptOptions.Default
        .WithImports("System", "System.Math");

    public async Task<ReserveEstimate> SuggestAsync(string claimId, string lossDescription, CancellationToken ct)
    {
        var estimate = await client.GetResponseAsync<ReserveEstimate>(
            $"Propose an initial reserve for claim {claimId}. Give a C# arithmetic formula that computes it. Loss: {lossDescription}",
            cancellationToken: ct);
        var amount = await EvaluateFormulaAsync(estimate.Result.Formula, ct);
        return estimate.Result with { Amount = amount };
    }

    public async Task<decimal> QuickReserveAsync(string lossDescription, CancellationToken ct)
    {
        var response = await client.GetResponseAsync(
            $"Reply with one number: a typical reserve in USD for this loss. Loss: {lossDescription}",
            cancellationToken: ct);
        var amount = decimal.Parse(response.Text.Trim(), NumberStyles.Currency, CultureInfo.InvariantCulture);
        return await EvaluateFormulaAsync($"Math.Round({amount}m * 1.1m, 2)", ct);
    }

    private static Task<decimal> EvaluateFormulaAsync(string formula, CancellationToken ct) =>
        CSharpScript.EvaluateAsync<decimal>(formula, FormulaOptions, cancellationToken: ct);
}
