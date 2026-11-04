using System.Diagnostics;
using System.Management.Automation;
using Microsoft.Agents.AI;
using Microsoft.CodeAnalysis.CSharp;
using Microsoft.CodeAnalysis.CSharp.Scripting;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Chat;
using OpenAI.Responses;

namespace Fixtures.Automation;

public record Plan(string Operation, string Target);

public class RemediationRunner
{
    private const string Shell = "/bin/bash";
    private static readonly HashSet<string> SafeCommands = new() { "uptime", "df -h", "free -m" };
    private static readonly Dictionary<string, string> Playbooks = new()
    {
        ["disk"] = "df -h",
        ["load"] = "uptime",
    };

    private readonly IChatCompletionService _chat;
    private readonly IChatClient _client;
    private readonly ChatClient _openAi;
    private readonly ResponsesClient _responses;
    private readonly Kernel _kernel;
    private readonly KernelFunction _suggest;

    public RemediationRunner(IChatCompletionService chat, IChatClient client, ChatClient openAi, ResponsesClient responses, Kernel kernel)
    {
        _chat = chat;
        _client = client;
        _openAi = openAi;
        _responses = responses;
        _kernel = kernel;
        _suggest = kernel.CreateFunctionFromPrompt("Suggest one shell command that fixes: {{$symptom}}");
    }

    public async Task Suggested(string symptom)
    {
        var reply = await _chat.GetChatMessageContentAsync($"One shell command for: {symptom}");
        // ruleid: llm-output-to-code-execution-csharp
        Process.Start("bash", $"-c \"{reply.Content}\"");
        var text = reply.Content ?? "";
        // ruleid: llm-output-to-code-execution-csharp
        Process.Start(text);
        // ok: llm-output-to-code-execution-csharp
        Process.Start("git", $"log --oneline -n 5 -- {text}");
        // ok: llm-output-to-code-execution-csharp
        Process.Start("bash", $"-c \"echo {reply.Metadata?.Count}\"");
        if (!SafeCommands.Contains(text))
        {
            throw new InvalidOperationException("Not an approved command.");
        }
        // ok: llm-output-to-code-execution-csharp
        Process.Start("bash", $"-c \"{text}\"");
    }

    public async Task FromPrompt(string symptom)
    {
        var result = await _kernel.InvokePromptAsync($"One shell command for: {symptom}");
        var command = result.GetValue<string>() ?? "";
        var psi = new ProcessStartInfo
        {
            FileName = Shell,
            // ruleid: llm-output-to-code-execution-csharp
            Arguments = $"-c \"{command}\"",
            RedirectStandardOutput = true,
        };
        var cmd = new ProcessStartInfo("cmd.exe")
        {
            // ruleid: llm-output-to-code-execution-csharp
            Arguments = "/c " + command,
        };
        var pwsh = new ProcessStartInfo("pwsh") { UseShellExecute = false };
        pwsh.ArgumentList.Add("-Command");
        // ruleid: llm-output-to-code-execution-csharp
        pwsh.ArgumentList.Add(command);
        // ok: llm-output-to-code-execution-csharp
        var env = new ProcessStartInfo("git") { Arguments = "status", WorkingDirectory = command };
        // ok: llm-output-to-code-execution-csharp
        Process.Start("bash", $"-c \"{Playbooks[command]}\"");
    }

    public async Task FromFunction(string symptom)
    {
        var result = await _suggest.InvokeAsync(_kernel, new KernelArguments { ["symptom"] = symptom });
        // ruleid: llm-output-to-code-execution-csharp
        Process.Start("sh", ["-c", result.ToString()]);
        var again = await _kernel.InvokeAsync(_suggest, new() { ["symptom"] = symptom });
        // ruleid: llm-output-to-code-execution-csharp
        Process.Start("python3", new[] { "-c", again.GetValue<string>()! });
        // ok: llm-output-to-code-execution-csharp
        Process.Start("node", new[] { "-c", again.GetValue<string>()! });
    }

    public async Task Steps(string symptom)
    {
        var response = await _client.GetResponseAsync($"List shell steps for: {symptom}");
        var steps = response.Messages.Where(m => m.Role == ChatRole.Assistant).Select(m => m.Text).ToList();
        // ruleid: llm-output-to-code-execution-csharp
        Process.Start("bash", $"-c \"{string.Join(" && ", steps)}\"");
        // ok: llm-output-to-code-execution-csharp
        Process.Start("bash", $"-c \"echo {steps.Count(s => s.Length > 0)} steps\"");
        // ruleid: llm-output-to-code-execution-csharp
        steps.ForEach(step => Process.Start("sh", ["-c", step]));
    }

    public async Task<object?> Formula(string question)
    {
        var response = await _client.GetResponseAsync(question);
        // ruleid: llm-output-to-code-execution-csharp
        var value = await CSharpScript.EvaluateAsync<double>(response.Text);
        var plan = await _client.GetResponseAsync<Plan>(question);
        // ruleid: llm-output-to-code-execution-csharp
        await CSharpScript.RunAsync(plan.Result.Operation);
        // ok: llm-output-to-code-execution-csharp
        var usage = await CSharpScript.EvaluateAsync<long>($"{response.Usage?.TotalTokenCount ?? 0} * 2");
        return value;
    }

    public async Task PowerShellStep(string ticket)
    {
        ChatCompletion completion = await _openAi.CompleteChatAsync(new UserChatMessage(ticket));
        using var ps = PowerShell.Create();
        // ruleid: llm-output-to-code-execution-csharp
        ps.AddScript(completion.Content[0].Text);
        // ok: llm-output-to-code-execution-csharp
        ps.AddParameter("Ticket", completion.Content[0].Text);
        ps.Invoke();
    }

    public async Task ScriptFile(string ticket)
    {
        var response = await _responses.CreateResponseAsync("example-org/model", ticket);
        var code = response.Value.GetOutputText();
        var path = Path.Combine(Path.GetTempPath(), "fix.py");
        // ruleid: llm-output-to-code-execution-csharp
        await File.WriteAllTextAsync(path, code);
        Process.Start("python3", path);
        // ok: llm-output-to-code-execution-csharp
        File.WriteAllText(Path.Combine(Path.GetTempPath(), "notes.txt"), code);
    }

    public async Task Compile(string ticket)
    {
        var agent = new ChatCompletionAgent { Name = "coder", Instructions = "Write a C# class.", Kernel = _kernel };
        await foreach (var item in agent.InvokeAsync(ticket))
        {
            // ruleid: llm-output-to-code-execution-csharp
            var tree = CSharpSyntaxTree.ParseText(item.Message.Content!);
            var compilation = CSharpCompilation.Create("Generated", new[] { tree });
            using var ms = new MemoryStream();
            compilation.Emit(ms);
        }
    }

    public async Task<string> Review(string ticket)
    {
        // ok: llm-output-to-code-execution-csharp
        var tree = CSharpSyntaxTree.ParseText(ticket);
        var reviewAgent = _client.AsAIAgent(instructions: "Review the patch.");
        var verdict = await reviewAgent.RunAsync(ticket);
        // ruleid: llm-output-to-code-execution-csharp
        Process.Start("bash", "-c \"" + verdict.Text + "\"");
        return tree.ToString();
    }
}
