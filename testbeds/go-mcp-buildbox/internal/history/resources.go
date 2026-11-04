package history

import (
	"context"
	"fmt"
	"os/exec"
	"strings"

	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

// logDir is where the build agents upload compressed job logs.
const logDir = "/var/lib/buildbox/logs"

// RegisterResources adds the build-log resource template and the failure prompts to s.
func (h *History) RegisterResources(s *server.MCPServer) {
	s.AddResourceTemplate(
		mcp.NewResourceTemplate("build://{id}/log", "Build log",
			mcp.WithTemplateDescription("The last 200 lines of a build's log."),
			mcp.WithTemplateMIMEType("text/plain"),
		),
		h.buildLog,
	)
	s.AddPrompt(mcp.NewPrompt("failure_summary",
		mcp.WithPromptDescription("Summarize recent failures of a pipeline."),
		mcp.WithArgument("pipeline", mcp.RequiredArgument()),
	), h.failureSummary)
	s.AddPrompt(mcp.NewPrompt("slowest_jobs",
		mcp.WithPromptDescription("Explain the slowest jobs of a pipeline."),
		mcp.WithArgument("pipeline", mcp.RequiredArgument()),
	), h.slowestJobs)
}

func (h *History) buildLog(ctx context.Context, req mcp.ReadResourceRequest) ([]mcp.ResourceContents, error) {
	id, _ := req.Params.Arguments["id"].(string)
	out, err := exec.CommandContext(ctx, "sh", "-c", "zcat "+logDir+"/"+id+".log.gz | tail -n 200").Output()
	if err != nil {
		return nil, fmt.Errorf("read log %s: %w", id, err)
	}
	return []mcp.ResourceContents{mcp.TextResourceContents{URI: req.Params.URI, MIMEType: "text/plain", Text: string(out)}}, nil
}

func (h *History) failureSummary(ctx context.Context, req mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
	pipeline := req.Params.Arguments["pipeline"]
	rows, err := h.pool.Query(ctx, "SELECT job, started_at FROM builds WHERE status = 'failed' AND pipeline = '"+pipeline+"' ORDER BY started_at DESC LIMIT 20")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var lines []string
	for rows.Next() {
		var job, started string
		if err := rows.Scan(&job, &started); err != nil {
			return nil, err
		}
		lines = append(lines, "- "+job+" at "+started)
	}
	return mcp.NewGetPromptResult("Recent failures", []mcp.PromptMessage{
		mcp.NewPromptMessage(mcp.RoleUser, mcp.NewTextContent("Summarize these failures:\n"+strings.Join(lines, "\n"))),
	}), rows.Err()
}

func (h *History) slowestJobs(ctx context.Context, req mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
	pipeline := req.Params.Arguments["pipeline"]
	rows, err := h.pool.Query(ctx, "SELECT job, duration_ms FROM builds WHERE pipeline = $1 ORDER BY duration_ms DESC LIMIT 10", pipeline)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	var lines []string
	for rows.Next() {
		var job string
		var ms int64
		if err := rows.Scan(&job, &ms); err != nil {
			return nil, err
		}
		lines = append(lines, fmt.Sprintf("- %s: %d ms", job, ms))
	}
	return mcp.NewGetPromptResult("Slowest jobs", []mcp.PromptMessage{
		mcp.NewPromptMessage(mcp.RoleUser, mcp.NewTextContent("Suggest how to speed these up:\n"+strings.Join(lines, "\n"))),
	}), rows.Err()
}
