using System.Data;
using Dapper;
using Microsoft.Data.SqlClient;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Npgsql;

namespace Fixtures.Reporting;

public record Order(int Id, string Region, decimal Total);

public class ReportingAssistant
{
    private static readonly Dictionary<string, string> Columns = new()
    {
        ["revenue"] = "total_cents",
        ["orders"] = "order_count",
    };

    private readonly IChatCompletionService _chat;
    private readonly IChatClient _client;
    private readonly ShopContext _db;
    private readonly IDbConnection _connection;
    private readonly NpgsqlDataSource _dataSource;

    public ReportingAssistant(IChatCompletionService chat, IChatClient client, ShopContext db, IDbConnection connection, NpgsqlDataSource dataSource)
    {
        _chat = chat;
        _client = client;
        _db = db;
        _connection = connection;
        _dataSource = dataSource;
    }

    public async Task<IEnumerable<Order>> Dapper(string question)
    {
        var history = new ChatHistory("Write one PostgreSQL SELECT statement.");
        history.AddUserMessage(question);
        var reply = await _chat.GetChatMessageContentAsync(history);
        var sql = reply.Content!.Trim().Trim('`');
        // ruleid: llm-output-to-sql-csharp
        var rows = await _connection.QueryAsync<Order>(sql);
        // ruleid: llm-output-to-sql-csharp
        await _connection.ExecuteAsync(sql: sql, param: new { region = "emea" });
        // ok: llm-output-to-sql-csharp
        var safe = await _connection.QueryAsync<Order>("SELECT id, region, total FROM orders WHERE region = @region", new { region = sql });
        return rows;
    }

    public async Task<List<Order>> EfCore(string question)
    {
        var response = await _client.GetResponseAsync(question);
        var where = response.Text;
        // ruleid: llm-output-to-sql-csharp
        var raw = await _db.Orders.FromSqlRaw("SELECT * FROM orders WHERE " + where).ToListAsync();
        // ok: llm-output-to-sql-csharp
        var interpolated = await _db.Orders.FromSql($"SELECT * FROM orders WHERE region = {where}").ToListAsync();
        // ruleid: llm-output-to-sql-csharp
        await _db.Database.ExecuteSqlRawAsync($"DELETE FROM carts WHERE {where}");
        // ok: llm-output-to-sql-csharp
        await _db.Database.ExecuteSqlAsync($"DELETE FROM carts WHERE region = {where}");
        // ok: llm-output-to-sql-csharp
        await _db.Database.ExecuteSqlRawAsync("DELETE FROM carts WHERE region = {0}", where);
        return raw;
    }

    public async Task<int> AdoNet(string question)
    {
        var reply = await _chat.GetChatMessageContentAsync(question);
        var text = reply.Content ?? "";
        await using var conn = new SqlConnection("Server=db.example.com;Database=shop;Integrated Security=true");
        // ruleid: llm-output-to-sql-csharp
        using var cmd = new SqlCommand(text, conn);
        using var update = conn.CreateCommand();
        // ruleid: llm-output-to-sql-csharp
        update.CommandText = $"UPDATE orders SET status = 'held' WHERE {text}";
        // ok: llm-output-to-sql-csharp
        update.Parameters.AddWithValue("@note", text);
        // ruleid: llm-output-to-sql-csharp
        await using var npg = _dataSource.CreateCommand(text);
        return await cmd.ExecuteNonQueryAsync();
    }

    public async Task<IEnumerable<dynamic>> Metric(string question)
    {
        var reply = await _chat.GetChatMessageContentAsync(question);
        var column = Columns[reply.Content!.Trim()];
        // ok: llm-output-to-sql-csharp
        return await _connection.QueryAsync($"SELECT region, {column} FROM daily_metrics");
    }

    public async Task<IEnumerable<Order>> Helper(string question)
    {
        var reply = await _chat.GetChatMessageContentAsync(question);
        // ruleid: llm-output-to-sql-csharp
        return await RunReport($"SELECT id, region, total FROM orders WHERE {reply.Content} LIMIT 100");
    }

    private Task<IEnumerable<Order>> RunReport(string statement)
    {
        return _connection.QueryAsync<Order>(statement);
    }
}
