// Resource templates and prompts: the client fills a template's URI and a prompt's arguments,
// and clients let the model choose them, so they're sources like tool arguments.
package tools

import (
	"context"
	"os/exec"
	"strings"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	sdk "github.com/modelcontextprotocol/go-sdk/mcp"
)

func registerLogResources(s *server.MCPServer) {
	s.AddResourceTemplate(
		mcp.NewResourceTemplate("logs://{service}/tail", "Unit logs"),
		func(ctx context.Context, req mcp.ReadResourceRequest) ([]mcp.ResourceContents, error) {
			service, _ := req.Params.Arguments["service"].(string)
			// ruleid: mcp-tool-arg-to-shell-go
			out, err := exec.Command("sh", "-c", "journalctl -n 50 -u "+service).Output()
			return []mcp.ResourceContents{mcp.TextResourceContents{URI: req.Params.URI, Text: string(out)}}, err
		},
	)
	s.AddPrompt(mcp.NewPrompt("triage", mcp.WithArgument("unit", mcp.RequiredArgument())), triagePrompt)
}

func triagePrompt(ctx context.Context, req mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
	unit := req.Params.Arguments["unit"]
	// ruleid: mcp-tool-arg-to-shell-go
	out, err := exec.Command("bash", "-c", "systemctl status "+unit).CombinedOutput()
	return mcp.NewGetPromptResult("Triage", []mcp.PromptMessage{
		mcp.NewPromptMessage(mcp.RoleUser, mcp.NewTextContent(string(out))),
	}), err
}

func registerSDKResources(s *sdk.Server) {
	s.AddResourceTemplate(&sdk.ResourceTemplate{URITemplate: "runbook://{name}", Name: "runbook"}, readRunbook)
	s.AddPrompt(&sdk.Prompt{Name: "disk_report"}, func(ctx context.Context, req *sdk.GetPromptRequest) (*sdk.GetPromptResult, error) {
		// ruleid: mcp-tool-arg-to-shell-go
		out, err := exec.CommandContext(ctx, "sh", "-c", "df -h "+req.Params.Arguments["mount"]).Output()
		return &sdk.GetPromptResult{Messages: []*sdk.PromptMessage{{Role: "user", Content: &sdk.TextContent{Text: string(out)}}}}, err
	})
}

func readRunbook(ctx context.Context, req *sdk.ReadResourceRequest) (*sdk.ReadResourceResult, error) {
	name := strings.TrimPrefix(req.Params.URI, "runbook://")
	// ruleid: mcp-tool-arg-to-shell-go
	out, err := exec.Command("sh", "-c", "cat /srv/runbooks/"+name+".md").Output()
	return &sdk.ReadResourceResult{Contents: []*sdk.ResourceContents{{URI: req.Params.URI, Text: string(out)}}}, err
}

// --- Near misses ---

func readRunbookSafe(ctx context.Context, req *sdk.ReadResourceRequest) (*sdk.ReadResourceResult, error) {
	name := strings.TrimPrefix(req.Params.URI, "runbook://")
	// ok: mcp-tool-arg-to-shell-go
	out, err := exec.Command("cat", "/srv/runbooks/"+name+".md").Output()
	return &sdk.ReadResourceResult{Contents: []*sdk.ResourceContents{{URI: req.Params.URI, Text: string(out)}}}, err
}

func listRunbooks(ctx context.Context, req *sdk.ListResourcesRequest) (*sdk.ListResourcesResult, error) {
	// ok: mcp-tool-arg-to-shell-go
	out, err := exec.Command("sh", "-c", "ls /srv/runbooks "+req.Params.Cursor).Output()
	_ = out
	return &sdk.ListResourcesResult{}, err
}
