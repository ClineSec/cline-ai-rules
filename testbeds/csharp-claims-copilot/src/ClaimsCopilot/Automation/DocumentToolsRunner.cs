using System.Diagnostics;
using OpenAI.Chat;

namespace ClaimsCopilot.Automation;

/// <summary>
/// Prepares uploaded claim documents (photos, PDFs) with command-line tools on the worker host.
/// </summary>
public sealed class DocumentToolsRunner(ChatClient chat, ILogger<DocumentToolsRunner> logger)
{
    private static readonly Dictionary<string, string[]> Recipes = new()
    {
        ["list-documents"] = ["ls", "-l"],
        ["folder-size"] = ["du", "-sh", "."],
    };

    public async Task<int> PrepareAsync(string folder, string request, CancellationToken ct)
    {
        ChatCompletion completion = await chat.CompleteChatAsync(
            [
                new SystemChatMessage("Reply with one POSIX shell command that prepares the claim documents in the current folder."),
                new UserChatMessage(request),
            ],
            cancellationToken: ct);

        var psi = new ProcessStartInfo("/bin/sh")
        {
            WorkingDirectory = folder,
            RedirectStandardOutput = true,
        };
        var command = string.Join(" ", completion.Content
            .Where(part => part.Kind == ChatMessageContentPartKind.Text)
            .Select(part => part.Text.Trim()));
        psi.ArgumentList.Add("-c");
        psi.ArgumentList.Add(command);
        using var process = Process.Start(psi)!;
        await process.WaitForExitAsync(ct);
        logger.LogInformation("Prepared documents in {Folder}: exit {Code}", folder, process.ExitCode);
        return process.ExitCode;
    }

    public async Task<int> RunRecipeAsync(string folder, string request, CancellationToken ct)
    {
        ChatCompletion completion = await chat.CompleteChatAsync(
            [
                new SystemChatMessage("Pick one recipe name: list-documents or folder-size. Reply with the name only."),
                new UserChatMessage(request),
            ],
            cancellationToken: ct);

        if (!Recipes.TryGetValue(completion.Content[0].Text.Trim(), out var recipe))
        {
            return -1;
        }

        var psi = new ProcessStartInfo(recipe[0]) { WorkingDirectory = folder };
        foreach (var argument in recipe.Skip(1))
        {
            psi.ArgumentList.Add(argument);
        }
        using var process = Process.Start(psi)!;
        await process.WaitForExitAsync(ct);
        return process.ExitCode;
    }

    public async Task<int> OcrAsync(string folder, string request, CancellationToken ct)
    {
        ChatCompletion completion = await chat.CompleteChatAsync(
            [
                new SystemChatMessage("Name the one PDF in this claim folder that holds the repair estimate. Reply with the file name only."),
                new UserChatMessage(request),
            ],
            cancellationToken: ct);

        var psi = new ProcessStartInfo("pdftotext") { WorkingDirectory = folder };
        psi.ArgumentList.Add("-layout");
        psi.ArgumentList.Add(Path.GetFileName(completion.Content[0].Text.Trim()));
        psi.ArgumentList.Add("estimate.txt");
        using var process = Process.Start(psi)!;
        await process.WaitForExitAsync(ct);
        return process.ExitCode;
    }
}
