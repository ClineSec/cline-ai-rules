// Package gitops exposes read-mostly git tools for the checked-out repository.
package gitops

import (
	"context"
	"fmt"
	"os/exec"
	"strings"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

// Repo is the working copy the tools operate on.
type Repo struct {
	Dir string
}

// BlameArgs are the arguments of git_blame.
type BlameArgs struct {
	Path  string `json:"path"`
	Line  int    `json:"line"`
	Lines int    `json:"lines"`
}

// Register adds the git tools to s.
func (r *Repo) Register(s *server.MCPServer) {
	s.AddTools(
		server.ServerTool{
			Tool: mcp.NewTool("git_log",
				mcp.WithDescription("Show recent commits, optionally from a revision or by an author."),
				mcp.WithString("rev", mcp.Description("Revision to start from")),
				mcp.WithString("author", mcp.Description("Only commits by this author")),
				mcp.WithNumber("limit", mcp.Description("Number of commits")),
			),
			Handler: r.handleLog,
		},
		server.ServerTool{
			Tool: mcp.NewTool("git_diff",
				mcp.WithDescription("Summarize changes against a base revision."),
				mcp.WithString("base", mcp.Required()),
			),
			Handler: r.handleDiff,
		},
	)
	s.AddTool(mcp.NewTool("git_checkout",
		mcp.WithDescription("Check out a branch."),
		mcp.WithString("branch", mcp.Required()),
	), r.handleCheckout)
	s.AddTool(mcp.NewTool("git_fetch",
		mcp.WithDescription("Fetch a remote."),
		mcp.WithString("remote", mcp.DefaultString("origin")),
	), r.handleFetch)
	s.AddTool(mcp.NewTool("git_push",
		mcp.WithDescription("Push the current branch to one of the known remotes."),
		mcp.WithString("remote", mcp.Enum("origin", "upstream")),
	), r.handlePush)
	s.AddTool(mcp.NewTool("git_blame",
		mcp.WithDescription("Blame a range of lines in a file."),
		mcp.WithInputSchema[BlameArgs](),
	), mcp.NewTypedToolHandler(r.blame))
}

func (r *Repo) handleLog(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	limit := req.GetInt("limit", 20)
	args := []string{"-C", r.Dir, "log", "--oneline", fmt.Sprintf("--max-count=%d", limit)}
	if author := req.GetString("author", ""); author != "" {
		args = append(args, "--author", author)
	}
	if rev := req.GetString("rev", ""); rev != "" {
		args = append(args, rev)
	}
	out, err := exec.CommandContext(ctx, "git", args...).CombinedOutput()
	if err != nil {
		return mcp.NewToolResultError(strings.TrimSpace(string(out))), nil
	}
	return mcp.NewToolResultText(string(out)), nil
}

func (r *Repo) handleDiff(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	base, err := req.RequireString("base")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	out, err := exec.CommandContext(ctx, "git", "-C", r.Dir, "diff", "--stat", "--end-of-options", base).Output()
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	return mcp.NewToolResultText(string(out)), nil
}

func (r *Repo) handleCheckout(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	branch, err := req.RequireString("branch")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	if strings.HasPrefix(branch, "-") {
		return mcp.NewToolResultError("branch names can't start with '-'"), nil
	}
	out, err := exec.CommandContext(ctx, "git", "-C", r.Dir, "checkout", branch).CombinedOutput()
	if err != nil {
		return mcp.NewToolResultError(string(out)), nil
	}
	return mcp.NewToolResultText("checked out " + branch), nil
}

func (r *Repo) handleFetch(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	remote := req.GetString("remote", "origin")
	argv := []string{"git", "-C", r.Dir, "fetch", "--prune", remote}
	out, err := r.run(ctx, argv)
	if err != nil {
		return mcp.NewToolResultError(out), nil
	}
	return mcp.NewToolResultText(out), nil
}

func (r *Repo) blame(ctx context.Context, req mcp.CallToolRequest, args BlameArgs) (*mcp.CallToolResult, error) {
	span := fmt.Sprintf("%d,+%d", args.Line, args.Lines)
	out, err := exec.CommandContext(ctx, "git", "-C", r.Dir, "blame", "-L", span, "--", args.Path).Output()
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	return mcp.NewToolResultText(string(out)), nil
}

func (r *Repo) handlePush(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	remote := req.GetString("remote", "origin")
	switch remote {
	case "origin", "upstream":
		out, err := exec.CommandContext(ctx, "git", "-C", r.Dir, "push", remote, "HEAD").CombinedOutput()
		if err != nil {
			return mcp.NewToolResultError(strings.TrimSpace(string(out))), nil
		}
		return mcp.NewToolResultText(string(out)), nil
	default:
		return mcp.NewToolResultError("unknown remote " + remote), nil
	}
}
