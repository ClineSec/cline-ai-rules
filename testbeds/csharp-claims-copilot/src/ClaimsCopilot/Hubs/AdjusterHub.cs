using ClaimsCopilot.Prompts;
using Microsoft.AspNetCore.SignalR;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ClaimsCopilot.Hubs;

/// <summary>Live assistant panel in the adjuster workbench.</summary>
public sealed class AdjusterHub(Kernel kernel, ILogger<AdjusterHub> logger) : Hub
{
    public async Task Ask(string claimId, string specialty, string question)
    {
        var agent = new ChatCompletionAgent
        {
            Name = "ClaimAssistant",
            Instructions = $"You help an adjuster who specializes in {specialty}. Stay on claim {claimId}.",
            Kernel = kernel,
        };

        var thread = new ChatHistoryAgentThread();
        await foreach (var item in agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, question), thread))
        {
            await Clients.Caller.SendAsync("answer", item.Message.Content);
        }
    }

    public async Task AskWithPersona(string persona, string question)
    {
        var agent = new ChatCompletionAgent
        {
            Name = "ClaimAssistant",
            Instructions = PromptLibrary.Personas.GetValueOrDefault(persona, PromptLibrary.Personas["desk-adjuster"]),
            Kernel = kernel,
        };

        await foreach (var item in agent.InvokeAsync(question))
        {
            await Clients.Caller.SendAsync("answer", item.Message.Content);
        }
        logger.LogDebug("Answered with persona {Persona}", persona);
    }
}
