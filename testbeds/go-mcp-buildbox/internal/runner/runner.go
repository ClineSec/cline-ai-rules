// Package runner exposes the build runner: named checks, pipelines, and scratch scripts.
package runner

import (
	"context"
	"fmt"
	"os"
	"os/exec"

	"github.com/alessio/shellescape"
	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// Config holds the runner's settings.
type Config struct {
	Shell   string
	Workdir string
}

type runner struct {
	cfg Config
}

// checks are the named checks run_check may start.
var checks = map[string][]string{
	"vet":   {"go", "vet", "./..."},
	"test":  {"go", "test", "-short", "./..."},
	"build": {"go", "build", "./..."},
}

type CheckIn struct {
	Check string `json:"check" jsonschema:"one of vet, test, build"`
}

type PipelineIn struct {
	Steps string `json:"steps" jsonschema:"shell steps to run in the workspace, separated by &&"`
}

type ScriptIn struct {
	Script string `json:"script" jsonschema:"a bash script"`
}

type TailIn struct {
	Unit  string `json:"unit" jsonschema:"systemd unit of the build agent"`
	Lines int    `json:"lines" jsonschema:"number of lines"`
}

type Output struct {
	Output string `json:"output"`
}

// Register adds the runner tools to srv.
func Register(srv *mcp.Server, cfg Config) {
	r := &runner{cfg: cfg}
	mcp.AddTool(srv, &mcp.Tool{Name: "run_check", Description: "Run a named check (vet, test, build)."}, r.runCheck)
	mcp.AddTool(srv, &mcp.Tool{Name: "run_pipeline", Description: "Run pipeline steps in the workspace."}, r.runPipeline)
	mcp.AddTool(srv, &mcp.Tool{Name: "run_script", Description: "Run a scratch bash script."}, r.runScript)
	mcp.AddTool(srv, &mcp.Tool{Name: "lint_script", Description: "Lint a bash script with shellcheck."}, r.lintScript)
	mcp.AddTool(srv, &mcp.Tool{Name: "tail_log", Description: "Show the end of a build agent's journal."}, r.tailLog)
	registerProbes(srv, cfg)
}

func (r *runner) runCheck(ctx context.Context, _ *mcp.CallToolRequest, in CheckIn) (*mcp.CallToolResult, Output, error) {
	argv, ok := checks[in.Check]
	if !ok {
		return nil, Output{}, fmt.Errorf("unknown check %q", in.Check)
	}
	cmd := exec.CommandContext(ctx, argv[0], argv[1:]...)
	cmd.Dir = r.cfg.Workdir
	out, err := cmd.CombinedOutput()
	return nil, Output{Output: string(out)}, err
}

func (r *runner) runPipeline(ctx context.Context, req *mcp.CallToolRequest, in PipelineIn) (*mcp.CallToolResult, Output, error) {
	cmd := exec.CommandContext(ctx, r.cfg.Shell, "-c", in.Steps)
	cmd.Dir = r.cfg.Workdir
	out, err := cmd.CombinedOutput()
	return nil, Output{Output: string(out)}, err
}

func (r *runner) runScript(ctx context.Context, req *mcp.CallToolRequest, in ScriptIn) (*mcp.CallToolResult, Output, error) {
	script, err := os.CreateTemp("", "buildbox-*.sh")
	if err != nil {
		return nil, Output{}, err
	}
	defer os.Remove(script.Name())
	if _, err := script.WriteString(in.Script); err != nil {
		return nil, Output{}, err
	}
	script.Close()
	out, err := exec.CommandContext(ctx, "bash", script.Name()).CombinedOutput()
	return nil, Output{Output: string(out)}, err
}

func (r *runner) lintScript(ctx context.Context, req *mcp.CallToolRequest, in ScriptIn) (*mcp.CallToolResult, Output, error) {
	f, err := os.CreateTemp("", "lint-*.sh")
	if err != nil {
		return nil, Output{}, err
	}
	defer os.Remove(f.Name())
	if _, err := f.WriteString(in.Script); err != nil {
		return nil, Output{}, err
	}
	f.Close()
	out, _ := exec.CommandContext(ctx, "shellcheck", "--format=gcc", f.Name()).CombinedOutput()
	return nil, Output{Output: string(out)}, nil
}

func (r *runner) tailLog(ctx context.Context, req *mcp.CallToolRequest, in TailIn) (*mcp.CallToolResult, Output, error) {
	line := fmt.Sprintf("journalctl -u %s --no-pager | tail -n %d", shellescape.Quote(in.Unit), in.Lines)
	out, err := exec.CommandContext(ctx, "sh", "-c", line).CombinedOutput()
	return nil, Output{Output: string(out)}, err
}
