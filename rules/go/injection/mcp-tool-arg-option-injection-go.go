package gittools

import (
	"context"
	"fmt"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	sdk "github.com/modelcontextprotocol/go-sdk/mcp"
)

const gitBin = "git"

var shaPattern = regexp.MustCompile(`^[0-9a-f]{7,40}$`)

var remotes = map[string]string{"origin": "https://example.com/org/repo.git"}

type Repo struct{ dir string }

type DiffIn struct {
	Target  string `json:"target"`
	Context int    `json:"context"`
}

func (r *Repo) Register(s *server.MCPServer) {
	s.AddTool(mcp.NewTool("git_diff"), r.diff)
	s.AddTool(mcp.NewTool("git_show"), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		rev := req.GetString("rev", "HEAD")
		// ruleid: mcp-tool-arg-option-injection-go
		out, err := exec.CommandContext(ctx, gitBin, "-C", r.dir, "show", rev).Output()
		if err != nil {
			return mcp.NewToolResultError(err.Error()), nil
		}
		return mcp.NewToolResultText(string(out)), nil
	})
}

func (r *Repo) diff(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	target, err := req.RequireString("target")
	if err != nil {
		return nil, err
	}
	// ruleid: mcp-tool-arg-option-injection-go
	exec.Command("git", "diff", target).Run()
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("git", "diff", "--", target).Run()
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("git", "diff", "--end-of-options", target).Run()
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("git", "log", "--author", target).Run()
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("git", "log", "--format="+target).Run()
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("git", "checkout", "origin/"+target).Run()
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("git", "branch", fmt.Sprintf("feature/%s", target)).Run()
	return nil, nil
}

func logTool(ctx context.Context, req *sdk.CallToolRequest, in DiffIn) (*sdk.CallToolResult, any, error) {
	args := []string{"log", "--oneline"}
	if in.Target != "" {
		// ruleid: mcp-tool-arg-option-injection-go
		args = append(args, in.Target)
	}
	out, err := exec.CommandContext(ctx, "git", args...).Output()
	return nil, string(out), err
}

func blameTool(ctx context.Context, req *sdk.CallToolRequest, in DiffIn) (*sdk.CallToolResult, any, error) {
	args := []string{"blame", fmt.Sprintf("-L%d,+20", in.Context)}
	args = append(args, "--")
	// ok: mcp-tool-arg-option-injection-go
	args = append(args, in.Target)
	out, err := exec.CommandContext(ctx, "git", args...).Output()
	return nil, string(out), err
}

func fetchTool(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	remote := req.GetString("remote", "origin")
	branch := req.GetString("branch", "main")
	// ruleid: mcp-tool-arg-option-injection-go
	argv := []string{"fetch", remote, branch}
	exec.Command("git", argv...).Run()
	url := remotes[remote]
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("git", "ls-remote", url).Run()
	if strings.HasPrefix(branch, "-") {
		return mcp.NewToolResultError("invalid branch"), nil
	}
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("git", "fetch", "origin", branch).Run()
	return nil, nil
}

func revTool(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	sha := req.GetString("sha", "")
	if !shaPattern.MatchString(sha) {
		return mcp.NewToolResultError("not a commit id"), nil
	}
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("git", "show", sha).Run()
	pattern := req.GetString("pattern", "")
	// ruleid: mcp-tool-arg-option-injection-go
	exec.Command("rg", "--json", strings.TrimPrefix(pattern, "-")).Run()
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("rg", "--json", strings.TrimLeft(pattern, "-")).Run()
	file := req.GetString("file", "")
	abs, _ := filepath.Abs(file)
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("git", "add", abs).Run()
	// ok: mcp-tool-arg-option-injection-go
	exec.Command("ls", "-la", file).Run()
	host := req.GetString("host", "")
	// ruleid: mcp-tool-arg-option-injection-go
	exec.Command("ssh", host, "uptime").Run()
	return nil, nil
}

func switchTool(ctx context.Context, req mcp.CallToolRequest, current string) (*mcp.CallToolResult, error) {
	branch := req.GetString("branch", "main")
	switch branch {
	case "main", "develop":
		// ok: mcp-tool-arg-option-injection-go
		exec.Command("git", "checkout", branch).Run()
	default:
		// ruleid: mcp-tool-arg-option-injection-go
		exec.Command("git", "checkout", branch).Run()
	}
	switch branch {
	case current:
		// ruleid: mcp-tool-arg-option-injection-go
		exec.Command("git", "checkout", branch).Run()
	}
	switch {
	case branch != "":
		// ruleid: mcp-tool-arg-option-injection-go
		exec.Command("git", "branch", branch).Run()
	}
	switch mode := req.GetString("mode", ""); mode {
	case "aggressive":
		// ok: mcp-tool-arg-option-injection-go
		exec.Command("git", "gc", "--"+mode, mode).Run()
	}
	return nil, nil
}
