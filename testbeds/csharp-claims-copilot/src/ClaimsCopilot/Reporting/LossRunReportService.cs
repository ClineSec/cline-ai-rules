using System.Data;
using ClaimsCopilot.Data;
using ClaimsCopilot.Models;
using Dapper;
using Microsoft.EntityFrameworkCore;
using Microsoft.SemanticKernel;
using Npgsql;

namespace ClaimsCopilot.Reporting;

/// <summary>
/// "Ask the loss run" reporting: the model writes a filter for the loss_run_v view.
/// </summary>
public sealed class LossRunReportService(Kernel kernel, NpgsqlDataSource dataSource, ClaimsDbContext db)
{
    private static readonly Dictionary<string, string> SortColumns = new(StringComparer.OrdinalIgnoreCase)
    {
        ["paid"] = "paid",
        ["reserve"] = "reserve",
        ["region"] = "region",
    };

    private readonly KernelFunction _writeFilter = kernel.CreateFunctionFromPrompt(
        """
        Write a PostgreSQL boolean expression over the columns claim_id, region, paid, reserve
        that answers the question below. Reply with the expression only.
        Question: {{$question}}
        """);

    public async Task<IReadOnlyList<LossRunRow>> AskAsync(string question, CancellationToken ct)
    {
        var filter = await _writeFilter.InvokeAsync(kernel, new() { ["question"] = question }, ct);
        await using var connection = await dataSource.OpenConnectionAsync(ct);
        var rows = await connection.QueryAsync<LossRunRow>(
            $"SELECT claim_id, region, paid, reserve FROM loss_run_v WHERE {filter.GetValue<string>()} LIMIT 500");
        return rows.AsList();
    }

    public async Task<IReadOnlyList<LossRunRow>> SortedAsync(string region, string question, CancellationToken ct)
    {
        var pick = await kernel.InvokePromptAsync<string>(
            $"Which column should this report sort by: paid, reserve, or region? Question: {question}",
            cancellationToken: ct);
        var column = SortColumns.GetValueOrDefault(pick?.Trim() ?? "", "paid");
        await using var connection = await dataSource.OpenConnectionAsync(ct);
        var rows = await connection.QueryAsync<LossRunRow>(
            $"SELECT claim_id, region, paid, reserve FROM loss_run_v WHERE region = @region ORDER BY {column} DESC",
            new { region });
        return rows.AsList();
    }

    public async Task<int> ArchiveAsync(string question, CancellationToken ct)
    {
        var result = await kernel.InvokePromptAsync(
            $"Which region does this archive request refer to? Reply with the region only. Request: {question}",
            cancellationToken: ct);
        var region = result.GetValue<string>() ?? "";
        return await db.Database.ExecuteSqlAsync(
            $"UPDATE loss_run_archive SET archived = true WHERE region = {region}", ct);
    }

    public async Task<decimal> TotalPaidAsync(string question, CancellationToken ct)
    {
        var result = await kernel.InvokePromptAsync(
            $"Write a SQL query that returns one number, total paid, for: {question}",
            cancellationToken: ct);
        await using var command = dataSource.CreateCommand();
        command.CommandText = result.ToString();
        var total = await command.ExecuteScalarAsync(ct);
        return Convert.ToDecimal(total);
    }
}
