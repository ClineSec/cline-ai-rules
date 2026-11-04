using Ganss.Xss;
using Markdig;
using Microsoft.AspNetCore.Components;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ClaimsCopilot.Components;

public partial class ClaimTimeline : ComponentBase
{
    private static readonly HtmlSanitizer Sanitizer = new();

    [Inject] public IChatCompletionService Chat { get; set; } = default!;

    [Parameter] public string ClaimId { get; set; } = "";

    protected MarkupString Timeline { get; private set; }

    protected MarkupString AdjusterTip { get; private set; }

    protected string PlainSummary { get; private set; } = "";

    protected override async Task OnParametersSetAsync()
    {
        var history = new ChatHistory("Turn the claim's activity log into a short markdown timeline.");
        history.AddUserMessage($"Claim {ClaimId}");
        var timeline = await Chat.GetChatMessageContentAsync(history);
        Timeline = new MarkupString(Markdown.ToHtml(timeline.Content ?? ""));

        var tip = await Chat.GetChatMessageContentAsync($"One markdown tip for the adjuster on claim {ClaimId}.");
        AdjusterTip = new MarkupString(Sanitizer.Sanitize(Markdown.ToHtml(tip.Content ?? "")));
        PlainSummary = tip.Content ?? "";
    }
}
