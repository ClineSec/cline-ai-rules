package tools

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"slices"
	"strconv"
	"strings"
	"syscall"

	"github.com/alessio/shellescape"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
	sdk "github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/traefik/yaegi/interp"
	"github.com/traefik/yaegi/stdlib"
)

const loginShell = "/bin/bash"

var branchName = regexp.MustCompile(`^[A-Za-z0-9._/-]+$`)

var looseName = regexp.MustCompile(`[A-Za-z0-9]+`)

var makeTargets = []string{"build", "test", "lint"}

var formatFlags = map[string]string{"json": "--json", "table": "--table"}

type GrepArgs struct {
	Pattern string `json:"pattern"`
	Context int    `json:"context"`
}

type Workspace struct{ root string }

func register(s *server.MCPServer, ws *Workspace) {
	s.AddTool(mcp.NewTool("run"), func(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
		command := req.GetString("command", "")
		// ruleid: mcp-tool-arg-to-shell-go
		out, err := exec.CommandContext(ctx, "sh", "-c", command).CombinedOutput()
		if err != nil {
			return mcp.NewToolResultError(err.Error()), nil
		}
		return mcp.NewToolResultText(string(out)), nil
	})
	s.AddTool(mcp.NewTool("disk_usage"), ws.diskUsage)
	s.AddTool(mcp.NewTool("grep"), mcp.NewTypedToolHandler(ws.grep))
}

func (w *Workspace) diskUsage(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	dir, err := req.RequireString("dir")
	if err != nil {
		return nil, err
	}
	// ruleid: mcp-tool-arg-to-shell-go
	out, _ := exec.Command(loginShell, "-lc", fmt.Sprintf("du -sh %s/%q", w.root, dir)).Output()
	// ok: mcp-tool-arg-to-shell-go
	out, _ = exec.Command("du", "-sh", "--", filepath.Join(w.root, dir)).Output()
	return mcp.NewToolResultText(string(out)), nil
}

func (w *Workspace) grep(ctx context.Context, req mcp.CallToolRequest, args GrepArgs) (*mcp.CallToolResult, error) {
	// ruleid: mcp-tool-arg-to-shell-go
	script := exec.Command("bash", "-e", "-c", "grep -rn '"+args.Pattern+"' .")
	// ok: mcp-tool-arg-to-shell-go
	ctxLines := exec.Command("sh", "-c", fmt.Sprintf("grep -C %d TODO .", args.Context))
	_, _ = script, ctxLines
	return nil, nil
}

func checkout(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	branch := req.GetString("branch", "main")
	if !branchName.MatchString(branch) {
		return mcp.NewToolResultError("invalid branch"), nil
	}
	// ok: mcp-tool-arg-to-shell-go
	exec.Command("sh", "-c", "git checkout "+branch).Run()
	tag := req.GetString("tag", "")
	if !looseName.MatchString(tag) {
		return mcp.NewToolResultError("invalid tag"), nil
	}
	// ruleid: mcp-tool-arg-to-shell-go
	exec.Command("sh", "-c", "git tag "+tag).Run()
	target := req.GetString("target", "build")
	if !slices.Contains(makeTargets, target) {
		return mcp.NewToolResultError("unknown target"), nil
	}
	// ok: mcp-tool-arg-to-shell-go
	exec.Command("sh", "-c", "make "+target).Run()
	format := req.GetString("format", "json")
	// ok: mcp-tool-arg-to-shell-go
	exec.Command("sh", "-c", "kubectl get pods "+formatFlags[format]).Run()
	name := req.GetString("name", "")
	// ok: mcp-tool-arg-to-shell-go
	exec.Command("sh", "-c", "touch "+shellescape.Quote(name)).Run()
	lines := req.GetInt("lines", 20)
	// ok: mcp-tool-arg-to-shell-go
	exec.Command("sh", "-c", "tail -n "+strconv.Itoa(lines)+" app.log").Run()
	// ruleid: mcp-tool-arg-to-shell-go
	exec.Command("sh", "-c", "echo "+strconv.Quote(name)).Run()
	return nil, nil
}

func lowLevel(ctx context.Context, req *sdk.CallToolRequest) (*sdk.CallToolResult, error) {
	var args struct {
		Host string `json:"host"`
	}
	if err := json.Unmarshal(req.Params.Arguments, &args); err != nil {
		return nil, err
	}
	// ruleid: mcp-tool-arg-to-shell-go
	argv := []string{"/bin/sh", "-c", "ping -c 1 " + args.Host}
	syscall.Exec(argv[0], argv, os.Environ())
	return nil, nil
}

type EvalIn struct {
	Code string `json:"code" jsonschema:"Python snippet to run"`
}

func evalPython(ctx context.Context, req *sdk.CallToolRequest, in EvalIn) (*sdk.CallToolResult, any, error) {
	// ruleid: mcp-tool-arg-to-shell-go
	out, err := exec.CommandContext(ctx, "python3", "-I", "-c", in.Code).Output()
	// ok: mcp-tool-arg-to-shell-go
	lint, _ := exec.CommandContext(ctx, "python3", "-m", "pyflakes", "-").Output()
	_ = lint
	return nil, string(out), err
}

func runScript(ctx context.Context, req *sdk.CallToolRequest, in EvalIn) (*sdk.CallToolResult, any, error) {
	path := filepath.Join(os.TempDir(), "snippet.sh")
	// ruleid: mcp-tool-arg-to-shell-go
	if err := os.WriteFile(path, []byte(in.Code), 0o700); err != nil {
		return nil, nil, err
	}
	out, err := exec.Command("bash", path).Output()
	notes := filepath.Join(os.TempDir(), "notes.txt")
	// ok: mcp-tool-arg-to-shell-go
	os.WriteFile(notes, []byte(in.Code), 0o600)
	exec.Command("wc", "-l", notes).Run()
	return nil, string(out), err
}

func runTemp(ctx context.Context, req *sdk.CallToolRequest, in EvalIn) (*sdk.CallToolResult, any, error) {
	f, err := os.CreateTemp("", "step-*.py")
	if err != nil {
		return nil, nil, err
	}
	// ruleid: mcp-tool-arg-to-shell-go
	if _, err := f.WriteString(in.Code); err != nil {
		return nil, nil, err
	}
	out, err := exec.CommandContext(ctx, "python3", f.Name()).Output()
	return nil, string(out), err
}

func evalGo(ctx context.Context, req *sdk.CallToolRequest, in EvalIn) (*sdk.CallToolResult, any, error) {
	i := interp.New(interp.Options{})
	i.Use(stdlib.Symbols)
	// ruleid: mcp-tool-arg-to-shell-go
	res, err := i.Eval(in.Code)
	return nil, res.String(), err
}

func runFromEnv(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var sb strings.Builder
	sb.WriteString("cd /srv && ")
	sb.WriteString(req.GetString("step", ""))
	// ruleid: mcp-tool-arg-to-shell-go
	exec.Command(os.Getenv("SHELL"), "-c", sb.String()).Run()
	// ok: mcp-tool-arg-to-shell-go
	exec.Command("sh", "-c", "uptime", "sh", req.GetString("label", "")).Run()
	// ok: mcp-tool-arg-to-shell-go
	exec.Command("gcc", "-c", req.GetString("file", "")).Run()
	return nil, nil
}

func switchTargets(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	switch req.GetString("target", "") {
	case "build", "test":
		// ok: mcp-tool-arg-to-shell-go
		exec.Command("sh", "-c", "make "+req.GetString("target", "")).Run()
	default:
		// ruleid: mcp-tool-arg-to-shell-go
		exec.Command("sh", "-c", "make "+req.GetString("target", "")).Run()
	}
	return nil, nil
}
