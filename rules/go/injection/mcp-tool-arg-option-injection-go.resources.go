package tools

import (
	"context"
	"os/exec"
	"strings"

	sdk "github.com/modelcontextprotocol/go-sdk/mcp"
)

func readDiff(ctx context.Context, req *sdk.ReadResourceRequest) (*sdk.ReadResourceResult, error) {
	ref := strings.TrimPrefix(req.Params.URI, "git://diff/")
	// ruleid: mcp-tool-arg-option-injection-go
	out, err := exec.CommandContext(ctx, "git", "diff", ref).Output()
	return &sdk.ReadResourceResult{Contents: []*sdk.ResourceContents{{URI: req.Params.URI, Text: string(out)}}}, err
}

func readDiffSafe(ctx context.Context, req *sdk.ReadResourceRequest) (*sdk.ReadResourceResult, error) {
	ref := strings.TrimPrefix(req.Params.URI, "git://diff/")
	// ok: mcp-tool-arg-option-injection-go
	out, err := exec.CommandContext(ctx, "git", "diff", "--end-of-options", ref).Output()
	return &sdk.ReadResourceResult{Contents: []*sdk.ResourceContents{{URI: req.Params.URI, Text: string(out)}}}, err
}
