using System.Text.RegularExpressions;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;
using OpenAI.Responses;

namespace Fixtures.Support;

public enum Tone { Friendly, Formal }

public record AskRequest(string Persona, string Question, string Locale);

[ApiController]
[Route("api/support")]
public class SupportController : ControllerBase
{
    private static readonly Dictionary<string, string> Personas = new()
    {
        ["billing"] = "You answer billing questions for Contoso Cloud.",
        ["outage"] = "You explain service incidents for Contoso Cloud.",
    };
    private static readonly HashSet<string> SupportedLocales = new() { "en-US", "de-DE", "fr-FR" };

    private readonly IChatCompletionService _chat;
    private readonly Kernel _kernel;

    public SupportController(IChatCompletionService chat, Kernel kernel)
    {
        _chat = chat;
        _kernel = kernel;
    }

    [HttpGet("ask")]
    public async Task<string> Ask([FromQuery] string persona, [FromQuery(Name = "q")] string question)
    {
        var history = new ChatHistory();
        // ruleid: user-input-in-system-prompt-csharp
        history.AddSystemMessage($"You are {persona}. Answer briefly.");
        // ok: user-input-in-system-prompt-csharp
        history.AddUserMessage(question);
        var reply = await _chat.GetChatMessageContentAsync(history);
        return reply.Content ?? "";
    }

    [HttpPost("ask")]
    public async Task<IActionResult> AskBody(AskRequest body)
    {
        // ruleid: user-input-in-system-prompt-csharp
        var history = new ChatHistory(body.Persona);
        history.AddUserMessage(body.Question);
        // ok: user-input-in-system-prompt-csharp
        history.AddSystemMessage(Personas[body.Persona]);
        // ok: user-input-in-system-prompt-csharp
        history.AddSystemMessage(Personas.GetValueOrDefault(body.Persona, "You are a helpful agent."));
        if (!SupportedLocales.Contains(body.Locale))
        {
            return BadRequest();
        }
        // ok: user-input-in-system-prompt-csharp
        history.AddSystemMessage($"Reply in {body.Locale}.");
        var reply = await _chat.GetChatMessageContentAsync(history);
        return Ok(reply.Content);
    }

    [HttpPost("escalate")]
    public async Task<IActionResult> Escalate([FromHeader(Name = "X-Team")] string team, [FromBody] AskRequest body)
    {
        var history = new ChatHistory();
        // ruleid: user-input-in-system-prompt-csharp
        history.Add(new ChatMessageContent(AuthorRole.System, "Route to the " + team + " queue."));
        // ruleid: user-input-in-system-prompt-csharp
        history.Add(new(AuthorRole.Developer, body.Persona));
        // ruleid: user-input-in-system-prompt-csharp
        history.AddMessage(AuthorRole.System, body.Question);
        // ok: user-input-in-system-prompt-csharp
        history.AddMessage(AuthorRole.User, body.Question);
        // ruleid: user-input-in-system-prompt-csharp
        history.AddDeveloperMessage(Request.Headers["X-Escalation-Note"].ToString());
        var reply = await _chat.GetChatMessageContentAsync(history);
        return Ok(reply.Content);
    }

    [HttpGet("tone")]
    public async Task<string> WithTone([FromQuery] Tone tone, [FromQuery] int maxWords, [FromQuery] string slug)
    {
        var history = new ChatHistory();
        // ok: user-input-in-system-prompt-csharp
        history.AddSystemMessage($"Use a {tone} tone in at most {maxWords} words.");
        if (!Regex.IsMatch(slug, "^[a-z0-9-]{1,40}$"))
        {
            return "";
        }
        // ok: user-input-in-system-prompt-csharp
        history.AddSystemMessage($"The customer is asking about article {slug}.");
        var parsed = Enum.Parse<Tone>(Request.Query["fallbackTone"].ToString());
        // ok: user-input-in-system-prompt-csharp
        history.AddSystemMessage($"Fallback tone: {parsed}.");
        // ruleid: user-input-in-system-prompt-csharp
        history.AddSystemMessage("Customer note: " + Request.Query["note"]);
        var reply = await _chat.GetChatMessageContentAsync(history);
        return reply.Content ?? "";
    }

    [HttpPost("agent")]
    public async Task<IActionResult> AgentReply([FromBody] AskRequest body)
    {
        var agent = new ChatCompletionAgent
        {
            Name = "SupportAgent",
            // ruleid: user-input-in-system-prompt-csharp
            Instructions = $"You are {body.Persona}.",
            Kernel = _kernel,
        };
        var options = new AgentInvokeOptions
        {
            // ruleid: user-input-in-system-prompt-csharp
            AdditionalInstructions = body.Locale,
        };
        var settings = new OpenAIPromptExecutionSettings
        {
            // ruleid: user-input-in-system-prompt-csharp
            ChatSystemPrompt = body.Persona,
            // ok: user-input-in-system-prompt-csharp
            User = body.Question,
        };
        await foreach (var item in agent.InvokeAsync(body.Question, options: options))
        {
            return Ok(item.Message.Content);
        }
        return Ok();
    }

    [HttpPost("template")]
    public async Task<string> Template([FromBody] AskRequest body)
    {
        var result = await _kernel.InvokePromptAsync($"""
            <message role="system">You are the support lead for
            // ruleid: user-input-in-system-prompt-csharp
            the {body.Persona} queue.</message>
            // ok: user-input-in-system-prompt-csharp
            <message role="user">{body.Question}</message>
            """);
        // ruleid: user-input-in-system-prompt-csharp
        var inline = $"<message role=\"system\">Answer as {body.Persona}.</message><message role=\"user\">{body.Question}</message>";
        // ok: user-input-in-system-prompt-csharp
        var templated = "<message role=\"system\">Answer as {{$persona}}.</message>";
        return result.ToString() + inline + templated;
    }
}

public class ChatOptionsFactory
{
    private readonly IChatClient _client;
    private readonly ChatClient _openAi;

    public ChatOptionsFactory(IChatClient client, ChatClient openAi)
    {
        _client = client;
        _openAi = openAi;
    }

    public async Task<string> Answer([FromBody] AskRequest body)
    {
        var messages = new List<Microsoft.Extensions.AI.ChatMessage>
        {
            // ruleid: user-input-in-system-prompt-csharp
            new Microsoft.Extensions.AI.ChatMessage(ChatRole.System, body.Persona),
            // ok: user-input-in-system-prompt-csharp
            new Microsoft.Extensions.AI.ChatMessage(ChatRole.User, body.Question),
        };
        // ruleid: user-input-in-system-prompt-csharp
        var options = new ChatOptions { Instructions = body.Locale, Temperature = 0.2f };
        var response = await _client.GetResponseAsync(messages, options);
        return response.Text;
    }

    public async Task<string> AnswerOpenAi([FromBody] AskRequest body)
    {
        var completion = await _openAi.CompleteChatAsync(
            // ruleid: user-input-in-system-prompt-csharp
            new SystemChatMessage(body.Persona),
            // ok: user-input-in-system-prompt-csharp
            new UserChatMessage(body.Question));
        // ruleid: user-input-in-system-prompt-csharp
        var item = ResponseItem.CreateDeveloperMessageItem(body.Locale);
        CreateResponseOptions responseOptions = new()
        {
            // ruleid: user-input-in-system-prompt-csharp
            Instructions = body.Persona,
        };
        // ruleid: user-input-in-system-prompt-csharp
        var legacy = OpenAI.Chat.ChatMessage.CreateSystemMessage(body.Locale);
        return completion.Value.Content[0].Text;
    }
}
