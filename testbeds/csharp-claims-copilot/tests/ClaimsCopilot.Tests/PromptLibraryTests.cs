using ClaimsCopilot.Prompts;
using Xunit;

namespace ClaimsCopilot.Tests;

public class PromptLibraryTests
{
    [Theory]
    [InlineData("desk-adjuster")]
    [InlineData("field-adjuster")]
    [InlineData("supervisor")]
    public void Every_persona_has_guidance(string persona)
    {
        Assert.False(string.IsNullOrWhiteSpace(PromptLibrary.Personas[persona]));
    }

    [Fact]
    public void Preamble_carries_the_guardrails()
    {
        var preamble = PromptLibrary.AdjusterPreamble("midwest");

        Assert.Contains("midwest", preamble);
        Assert.Contains(PromptLibrary.SummaryGuardrails, preamble);
    }

    [Fact]
    public void Supported_regions_are_lower_case()
    {
        Assert.All(PromptLibrary.SupportedRegions, region => Assert.Equal(region.ToLowerInvariant(), region));
    }
}
