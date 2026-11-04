using System.Net;
using System.Net.Mime;
using System.Text.Encodings.Web;
using Ganss.Xss;
using Markdig;
using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Html;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Razor.TagHelpers;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Fixtures.Answers;

[ApiController]
[Route("answers")]
public class AnswerController : ControllerBase
{
    private static readonly HtmlSanitizer Sanitizer = new();

    private readonly IChatCompletionService _chat;
    private readonly Kernel _kernel;

    public AnswerController(IChatCompletionService chat, Kernel kernel)
    {
        _chat = chat;
        _kernel = kernel;
    }

    [HttpGet("{id}/preview")]
    public async Task<IActionResult> Preview(string id)
    {
        var reply = await _chat.GetChatMessageContentAsync($"Summarize article {id} as markdown.");
        var html = Markdown.ToHtml(reply.Content ?? "");
        // ruleid: llm-output-to-html-csharp
        return Content(html, "text/html");
    }

    [HttpGet("{id}/safe")]
    public async Task<IActionResult> SafePreview(string id)
    {
        var reply = await _chat.GetChatMessageContentAsync($"Summarize article {id} as markdown.");
        var html = Sanitizer.Sanitize(Markdown.ToHtml(reply.Content ?? ""));
        // ok: llm-output-to-html-csharp
        return Content(html, "text/html; charset=utf-8");
    }

    [HttpGet("{id}/text")]
    public async Task<IActionResult> Text(string id)
    {
        var reply = await _chat.GetChatMessageContentAsync($"Summarize article {id}.");
        // ok: llm-output-to-html-csharp
        return Content(reply.Content ?? "", "text/plain");
    }

    [HttpGet("{id}")]
    public async Task<string> Plain(string id)
    {
        var result = await _kernel.InvokePromptAsync($"Summarize article {id}.");
        // ok: llm-output-to-html-csharp
        return result.ToString();
    }

    [HttpGet("{id}/card")]
    public async Task<ContentResult> Card(string id)
    {
        var result = await _kernel.InvokePromptAsync($"Write an HTML card for article {id}.");
        return new ContentResult
        {
            ContentType = MediaTypeNames.Text.Html,
            // ruleid: llm-output-to-html-csharp
            Content = result.GetValue<string>(),
            StatusCode = 200,
        };
    }

    [HttpGet("{id}/encoded")]
    public async Task<ContentResult> Encoded(string id)
    {
        var result = await _kernel.InvokePromptAsync($"Summarize article {id}.");
        return new ContentResult
        {
            ContentType = "text/html",
            // ok: llm-output-to-html-csharp
            Content = "<p>" + HtmlEncoder.Default.Encode(result.ToString()) + "</p>",
        };
    }

    [HttpGet("{id}/stream")]
    public async Task Stream(string id)
    {
        Response.ContentType = "text/html";
        await foreach (var chunk in _chat.GetStreamingChatMessageContentsAsync($"Summarize article {id}."))
        {
            // ruleid: llm-output-to-html-csharp
            await Response.WriteAsync(chunk.Content ?? "");
        }
        // ok: llm-output-to-html-csharp
        await Response.WriteAsync(WebUtility.HtmlEncode(id));
    }
}

public static class AnswerEndpoints
{
    public static void MapAnswerEndpoints(this IEndpointRouteBuilder app)
    {
        app.MapGet("/widget/{id}", async (string id, IChatClient client) =>
        {
            var response = await client.GetResponseAsync($"Answer FAQ {id} in HTML.");
            // ruleid: llm-output-to-html-csharp
            return Results.Content(response.Text, contentType: "text/html");
        });
        app.MapGet("/widget/{id}/plain", async (string id, IChatClient client) =>
        {
            var response = await client.GetResponseAsync($"Answer FAQ {id}.");
            // ok: llm-output-to-html-csharp
            return Results.Text(response.Text);
        });
    }
}

public class AnswerCard : ComponentBase
{
    [Inject] public IChatClient Client { get; set; } = default!;

    protected MarkupString Body { get; private set; }
    protected string Raw { get; private set; } = "";

    protected override async Task OnInitializedAsync()
    {
        var response = await Client.GetResponseAsync("Write today's status note in markdown.");
        // ruleid: llm-output-to-html-csharp
        Body = (MarkupString)Markdown.ToHtml(response.Text);
        // ok: llm-output-to-html-csharp
        Raw = response.Text;
        // ok: llm-output-to-html-csharp
        var cleaned = new MarkupString(new HtmlSanitizer().Sanitize(Markdown.ToHtml(response.Text)));
    }
}

[HtmlTargetElement("ai-answer")]
public class AiAnswerTagHelper : TagHelper
{
    private readonly IChatCompletionService _chat;

    public AiAnswerTagHelper(IChatCompletionService chat) => _chat = chat;

    public string Topic { get; set; } = "";

    public override async Task ProcessAsync(TagHelperContext context, TagHelperOutput output)
    {
        var reply = await _chat.GetChatMessageContentAsync($"Explain {Topic} in one paragraph of HTML.");
        // ruleid: llm-output-to-html-csharp
        output.Content.SetHtmlContent(reply.Content);
        // ok: llm-output-to-html-csharp
        output.Content.SetContent(reply.Content);
        // ruleid: llm-output-to-html-csharp
        output.PostContent.AppendHtml(new HtmlString(reply.Content));
    }
}
