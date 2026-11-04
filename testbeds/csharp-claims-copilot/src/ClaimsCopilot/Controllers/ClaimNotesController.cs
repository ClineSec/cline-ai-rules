using System.Net.Mime;
using ClaimsCopilot.Models;
using ClaimsCopilot.Prompts;
using Ganss.Xss;
using Markdig;
using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ClaimsCopilot.Controllers;

[ApiController]
[Route("api/claims/{claimId}")]
public sealed class ClaimNotesController(
    IChatCompletionService chat,
    ILogger<ClaimNotesController> logger) : ControllerBase
{
    private static readonly MarkdownPipeline LetterPipeline = new MarkdownPipelineBuilder()
        .UseAdvancedExtensions()
        .Build();

    private static readonly HtmlSanitizer LetterSanitizer = new();

    /// <summary>Summarizes adjuster notes. The gateway adds X-Adjuster-Region for field staff.</summary>
    [HttpPost("notes/summary")]
    public async Task<IActionResult> SummarizeNotes(
        string claimId,
        [FromHeader(Name = "X-Adjuster-Region")] string region,
        [FromBody] NoteSummaryRequest body)
    {
        var history = new ChatHistory();
        history.AddSystemMessage(PromptLibrary.Personas.GetValueOrDefault(body.Persona, PromptLibrary.Personas["desk-adjuster"]));
        history.AddSystemMessage(PromptLibrary.AdjusterPreamble(region));
        history.AddUserMessage($"Claim {claimId} notes:\n{body.Notes}");

        var reply = await chat.GetChatMessageContentAsync(history);
        logger.LogInformation("Summarized notes for {ClaimId} ({Length} chars)", claimId, reply.Content?.Length ?? 0);
        return Ok(new { claimId, summary = reply.Content });
    }

    /// <summary>Same summary for supervisors, limited to the regions the desk covers.</summary>
    [HttpPost("notes/supervisor-summary")]
    public async Task<IActionResult> SupervisorSummary(
        string claimId,
        [FromHeader(Name = "X-Adjuster-Region")] string region,
        [FromBody] NoteSummaryRequest body)
    {
        if (!PromptLibrary.SupportedRegions.Contains(region))
        {
            return BadRequest(new { error = "unknown region" });
        }

        var history = new ChatHistory(PromptLibrary.Personas["supervisor"]);
        history.AddSystemMessage(PromptLibrary.AdjusterPreamble(region));
        history.AddUserMessage(body.Notes);
        var reply = await chat.GetChatMessageContentAsync(history);
        return Ok(new { claimId, summary = reply.Content });
    }

    [HttpGet("letter")]
    public async Task<IActionResult> LetterPreview(string claimId, [FromQuery] ClaimSeverity severity)
    {
        var draft = await chat.GetChatMessageContentAsync(LetterHistory(claimId, severity));
        var html = Markdown.ToHtml(draft.Content ?? "", LetterPipeline);
        return Content(html, MediaTypeNames.Text.Html);
    }

    [HttpGet("letter/reviewed")]
    public async Task<IActionResult> ReviewedLetter(string claimId, [FromQuery] ClaimSeverity severity)
    {
        var draft = await chat.GetChatMessageContentAsync(LetterHistory(claimId, severity));
        var html = LetterSanitizer.Sanitize(Markdown.ToHtml(draft.Content ?? "", LetterPipeline));
        return Content(html, "text/html; charset=utf-8");
    }

    [HttpGet("letter.md")]
    public async Task<IActionResult> LetterMarkdown(string claimId, [FromQuery] ClaimSeverity severity)
    {
        var draft = await chat.GetChatMessageContentAsync(LetterHistory(claimId, severity));
        return Content(draft.Content ?? "", "text/markdown");
    }

    private static ChatHistory LetterHistory(string claimId, ClaimSeverity severity)
    {
        var tone = severity >= ClaimSeverity.Severe ? "compassionate" : "neutral";
        var history = new ChatHistory(PromptLibrary.LetterInstructions(tone));
        history.AddUserMessage($"Write the status letter for claim {claimId}.");
        return history;
    }
}
