using ClaimsCopilot.Models;
using Microsoft.Extensions.AI;

namespace ClaimsCopilot.Endpoints;

public static class TriageEndpoints
{
    private static readonly Dictionary<LineOfBusiness, string> Playbooks = new()
    {
        [LineOfBusiness.Auto] = "Ask for the police report number and photos of both vehicles.",
        [LineOfBusiness.Homeowners] = "Ask for photos of the damage and the date the loss was noticed.",
        [LineOfBusiness.CommercialProperty] = "Ask for the business interruption start date.",
    };

    public static IEndpointRouteBuilder MapTriageEndpoints(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/api/triage");
        group.MapPost("/", Triage);
        group.MapPost("/first-notice", FirstNotice);
        group.MapGet("/channels/{channel}/greeting", async (string channel, IChatClient client) =>
        {
            var options = new ChatOptions
            {
                Instructions = "Greet the policyholder and ask how we can help. Contact channel: " + channel,
                MaxOutputTokens = 120,
            };
            var response = await client.GetResponseAsync("Start the conversation.", options);
            return Results.Ok(new { greeting = response.Text });
        });
        return app;
    }

    private static async Task<IResult> Triage(TriageRequest request, IChatClient client, CancellationToken ct)
    {
        var line = Enum.Parse<LineOfBusiness>(request.LineOfBusiness, ignoreCase: true);
        List<ChatMessage> messages =
        [
            new(ChatRole.System, Playbooks[line]),
            new(ChatRole.System, $"Triage {line} claims. Ask one question at a time."),
            new(ChatRole.User, request.LossDescription),
        ];
        var response = await client.GetResponseAsync(messages, cancellationToken: ct);
        return Results.Ok(new { request.ClaimId, nextQuestion = response.Text });
    }

    private static async Task<IResult> FirstNotice(TriageRequest request, IChatClient client, CancellationToken ct)
    {
        List<ChatMessage> messages =
        [
            new(ChatRole.System, $"""
                You take first notice of loss for claim {request.ClaimId}.
                The caller reached us through {request.Channel}; match that channel's style.
                """),
            new(ChatRole.User, request.LossDescription),
        ];
        var response = await client.GetResponseAsync(messages, cancellationToken: ct);
        return Results.Ok(new { request.ClaimId, reply = response.Text });
    }
}
