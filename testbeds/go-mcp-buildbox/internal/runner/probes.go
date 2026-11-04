package runner

import (
	"context"
	"encoding/json"
	"fmt"
	"os/exec"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

type probeArgs struct {
	Var  string `json:"var"`
	Path string `json:"path"`
}

var probeSchema = json.RawMessage(`{
  "type": "object",
  "properties": {
    "var": {"type": "string", "description": "environment variable to print"},
    "path": {"type": "string", "description": "workspace path to measure"}
  }
}`)

// registerProbes adds the low-level probe tools, which decode their own arguments.
func registerProbes(srv *mcp.Server, cfg Config) {
	srv.AddTool(&mcp.Tool{Name: "env_probe", Description: "Print a build environment variable.", InputSchema: probeSchema}, envProbe)
	srv.AddTool(&mcp.Tool{Name: "disk_usage", Description: "Measure a workspace path.", InputSchema: probeSchema},
		func(ctx context.Context, req *mcp.CallToolRequest) (*mcp.CallToolResult, error) {
			var a probeArgs
			if err := json.Unmarshal(req.Params.Arguments, &a); err != nil {
				return nil, err
			}
			target := cfg.Workdir + "/" + a.Path
			out, err := shellOut(ctx, "du -sh "+target)
			if err != nil {
				return nil, err
			}
			return &mcp.CallToolResult{Content: []mcp.Content{&mcp.TextContent{Text: out}}}, nil
		})
}

func envProbe(ctx context.Context, req *mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var a probeArgs
	if err := json.Unmarshal(req.Params.Arguments, &a); err != nil {
		return nil, err
	}
	out, err := exec.CommandContext(ctx, "/bin/sh", "-c", "printenv '"+a.Var+"'").Output()
	if err != nil {
		return nil, fmt.Errorf("printenv: %w", err)
	}
	return &mcp.CallToolResult{Content: []mcp.Content{&mcp.TextContent{Text: string(out)}}}, nil
}

// shellOut runs line with /bin/sh and returns its output.
func shellOut(ctx context.Context, line string) (string, error) {
	out, err := exec.CommandContext(ctx, "/bin/sh", "-c", line).CombinedOutput()
	return string(out), err
}
