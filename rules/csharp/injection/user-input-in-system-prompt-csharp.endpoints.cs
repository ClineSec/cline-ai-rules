using Grpc.Core;
using Microsoft.Agents.AI;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Fixtures.Endpoints;

public record DraftRequest(string Audience, string Notes);

public static class DraftEndpoints
{
    private const string ReleaseTemplate = """
        <message role="system">You draft release notes for {{$audience}}.</message>
        <message role="user">{{$notes}}</message>
        """;

    public static void MapDraftEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapPost("/drafts", async (DraftRequest req, IChatCompletionService chat) =>
        {
            var history = new ChatHistory();
            // ruleid: user-input-in-system-prompt-csharp
            history.AddSystemMessage($"Write for {req.Audience}.");
            history.AddUserMessage(req.Notes);
            var reply = await chat.GetChatMessageContentAsync(history);
            return Results.Ok(reply.Content);
        });

        // ruleid: user-input-in-system-prompt-csharp
        app.MapGet("/drafts/style", (string style, IChatClient client) => client.GetResponseAsync(new[] { new ChatMessage(ChatRole.System, style) }));

        app.MapGet("/drafts/count", async (int count, Kernel kernel, IChatCompletionService chat) =>
        {
            var history = new ChatHistory();
            // ok: user-input-in-system-prompt-csharp
            history.AddSystemMessage($"Write exactly {count} bullet points.");
            // ok: user-input-in-system-prompt-csharp
            history.AddSystemMessage(kernel.Plugins.Count.ToString());
            var reply = await chat.GetChatMessageContentAsync(history);
            return reply.Content;
        });

        app.MapPost("/drafts/agent", CreateAgentDraft);
        app.MapPost("/drafts/template", RenderTemplate);
    }

    private static async Task<IResult> CreateAgentDraft(DraftRequest req, IChatClient client)
    {
        // ruleid: user-input-in-system-prompt-csharp
        AIAgent agent = client.AsAIAgent(instructions: "Audience: " + req.Audience);
        // ruleid: user-input-in-system-prompt-csharp
        var second = new ChatClientAgent(client, $"Audience: {req.Audience}", "drafter");
        // ok: user-input-in-system-prompt-csharp
        var third = client.AsAIAgent(new ChatClientAgentOptions { Name = req.Audience });
        var response = await agent.RunAsync(req.Notes);
        return Results.Ok(response.Text);
    }

    private static async Task<IResult> RenderTemplate(DraftRequest req, Kernel kernel)
    {
        // ok: user-input-in-system-prompt-csharp
        var result = await kernel.InvokePromptAsync(ReleaseTemplate, new KernelArguments { ["audience"] = req.Audience, ["notes"] = req.Notes });
        return Results.Ok(result.ToString());
    }
}

public class DraftHub : Hub
{
    private readonly IChatCompletionService _chat;

    public DraftHub(IChatCompletionService chat) => _chat = chat;

    public async Task Draft(string audience, string notes)
    {
        var history = new ChatHistory();
        // ruleid: user-input-in-system-prompt-csharp
        history.AddSystemMessage("Audience: " + audience);
        // ok: user-input-in-system-prompt-csharp
        history.AddUserMessage(notes);
        var reply = await _chat.GetChatMessageContentAsync(history);
        await Clients.Caller.SendAsync("draft", reply.Content);
    }

    public override async Task OnDisconnectedAsync(Exception? exception)
    {
        var history = new ChatHistory();
        // ok: user-input-in-system-prompt-csharp
        history.AddSystemMessage(exception?.Message ?? "disconnected");
        await base.OnDisconnectedAsync(exception);
    }
}

public class DraftModel : PageModel
{
    private readonly IChatCompletionService _chat;

    public DraftModel(IChatCompletionService chat) => _chat = chat;

    [BindProperty]
    public string Audience { get; set; } = "";

    [BindProperty(SupportsGet = true)]
    public int Bullets { get; set; }

    public string Title { get; set; } = "Release notes";

    public async Task OnPostAsync(string notes)
    {
        var history = new ChatHistory();
        // ruleid: user-input-in-system-prompt-csharp
        history.AddSystemMessage("Audience: " + Audience);
        // ok: user-input-in-system-prompt-csharp
        history.AddSystemMessage($"Use {Bullets} bullets under the title {Title}.");
        // ruleid: user-input-in-system-prompt-csharp
        history.AddDeveloperMessage(notes);
        await _chat.GetChatMessageContentAsync(history);
    }
}

public class DraftService : Drafts.DraftsBase
{
    private readonly IChatCompletionService _chat;

    public DraftService(IChatCompletionService chat) => _chat = chat;

    public override async Task<DraftReply> Draft(DraftRpc request, ServerCallContext context)
    {
        // ruleid: user-input-in-system-prompt-csharp
        var history = new ChatHistory($"Audience: {request.Audience}");
        // ok: user-input-in-system-prompt-csharp
        var copy = new ChatHistory(history);
        var reply = await _chat.GetChatMessageContentAsync(history);
        return new DraftReply { Text = reply.Content };
    }
}
