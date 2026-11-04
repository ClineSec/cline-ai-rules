using Dapper;
using Jint;
using Microsoft.ClearScript.V8;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.ObjectPool;
using System.Data;

namespace Fixtures.Rules;

public class RuleEngine
{
    private readonly IChatClient _client;
    private readonly Engine _jint = new(options => options.TimeoutInterval(TimeSpan.FromSeconds(2)));
    private readonly IDbConnection _db;
    private readonly ObjectPool<Engine> _pool = ObjectPool.Create<Engine>();

    public RuleEngine(IChatClient client, IDbConnection db)
    {
        _client = client;
        _db = db;
    }

    public async Task<object> Jint(string request)
    {
        var response = await _client.GetResponseAsync($"Write a JavaScript expression for: {request}");
        // ruleid: llm-output-to-code-execution-csharp
        var value = _jint.Evaluate(response.Text);
        var engine = new Engine();
        // ruleid: llm-output-to-code-execution-csharp
        engine.Execute(response.Text, "rule.js");
        // ruleid: llm-output-to-code-execution-csharp
        new Engine().SetValue("limit", 100).Execute(response.Text);
        // ruleid: llm-output-to-code-execution-csharp
        engine.Modules.Add("rule", response.Text);
        var pooledEngine = _pool.Get();
        // ruleid: llm-output-to-code-execution-csharp
        pooledEngine.Evaluate(response.Text);
        // ok: llm-output-to-code-execution-csharp
        engine.SetValue("label", response.Text);
        // ok: llm-output-to-code-execution-csharp
        engine.Execute("label.toUpperCase()", response.Text);
        // ok: llm-output-to-code-execution-csharp
        _db.Execute("INSERT INTO rules (body) VALUES (@body)", new { body = response.Text });
        return value.ToObject()!;
    }

    public async Task ClearScript(string request)
    {
        var response = await _client.GetResponseAsync($"Write a JavaScript snippet for: {request}");
        using var v8 = new V8ScriptEngine();
        // ruleid: llm-output-to-code-execution-csharp
        v8.Execute("generated.js", response.Text);
        // ruleid: llm-output-to-code-execution-csharp
        var result = v8.Evaluate(response.Text);
        // ruleid: llm-output-to-code-execution-csharp
        v8.ExecuteCommand(response.Text);
        // ok: llm-output-to-code-execution-csharp
        v8.Execute(response.Text, "Math.max(1, 2)");
        // ok: llm-output-to-code-execution-csharp
        v8.Script.label = response.Text;
    }
}
