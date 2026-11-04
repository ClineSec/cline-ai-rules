package artifacts

import (
	"context"
	"os/exec"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// checkout is the working copy the release prompts compare.
const checkout = "/srv/buildbox/checkout"

// RegisterPrompts adds the release-comparison prompts to srv.
func RegisterPrompts(srv *mcp.Server) {
	srv.AddPrompt(&mcp.Prompt{
		Name:        "compare_releases",
		Description: "Explain what changed since a release tag.",
		Arguments:   []*mcp.PromptArgument{{Name: "from", Required: true}},
	}, compareReleases)
	srv.AddPrompt(&mcp.Prompt{
		Name:        "release_notes",
		Description: "Draft release notes since a tag.",
		Arguments:   []*mcp.PromptArgument{{Name: "since", Required: true}},
	}, releaseNotes)
}

func compareReleases(ctx context.Context, req *mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
	from := req.Params.Arguments["from"]
	cmd := exec.CommandContext(ctx, "git", "diff", "--stat", from)
	cmd.Dir = checkout
	out, err := cmd.Output()
	if err != nil {
		return nil, err
	}
	return &mcp.GetPromptResult{Messages: []*mcp.PromptMessage{
		{Role: "user", Content: &mcp.TextContent{Text: "Explain these changes for the release notes:\n" + string(out)}},
	}}, nil
}

func releaseNotes(ctx context.Context, req *mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
	since := req.Params.Arguments["since"]
	cmd := exec.CommandContext(ctx, "git", "log", "--oneline", "--end-of-options", since+"..HEAD")
	cmd.Dir = checkout
	out, err := cmd.Output()
	if err != nil {
		return nil, err
	}
	return &mcp.GetPromptResult{Messages: []*mcp.PromptMessage{
		{Role: "user", Content: &mcp.TextContent{Text: "Draft release notes from:\n" + string(out)}},
	}}, nil
}
