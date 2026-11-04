package history

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/mark3labs/mcp-go/mcp"
	"github.com/mark3labs/mcp-go/server"
)

// sortColumns maps the sort names the tools accept to columns.
var sortColumns = map[string]string{
	"started":  "started_at",
	"duration": "duration_ms",
	"status":   "status",
}

type FlakyTest struct {
	Suite    string  `db:"suite" json:"suite"`
	Name     string  `db:"name" json:"name"`
	FailRate float64 `db:"fail_rate" json:"fail_rate"`
}

// Register adds the build-history tools to s.
func (h *History) Register(s *server.MCPServer) {
	s.AddTool(mcp.NewTool("build_search",
		mcp.WithDescription("Find builds by branch, status, and commit message text."),
		mcp.WithString("branch"),
		mcp.WithString("status", mcp.Enum("passed", "failed", "cancelled")),
		mcp.WithString("text"),
	), h.buildSearch)
	s.AddTool(mcp.NewTool("build_stats",
		mcp.WithDescription("Build durations for a pipeline, sorted."),
		mcp.WithString("pipeline", mcp.Required()),
		mcp.WithString("sort", mcp.Enum("started", "duration", "status")),
		mcp.WithNumber("limit"),
	), h.buildStats)
	s.AddTool(mcp.NewTool("flaky_tests",
		mcp.WithDescription("Tests that failed and then passed on retry."),
		mcp.WithString("suite", mcp.Required()),
		mcp.WithString("name"),
	), h.flakyTests)
	s.AddTool(mcp.NewTool("job_report",
		mcp.WithDescription("Per-job summary for a build job."),
		mcp.WithString("job", mcp.Required()),
	), h.jobReport)
}

func (h *History) buildSearch(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	var sb strings.Builder
	sb.WriteString("SELECT id, branch, status, started_at FROM builds WHERE true")
	if branch := req.GetString("branch", ""); branch != "" {
		fmt.Fprintf(&sb, " AND branch = '%s'", branch)
	}
	if status := req.GetString("status", ""); status != "" {
		fmt.Fprintf(&sb, " AND status = '%s'", status)
	}
	sb.WriteString(" ORDER BY started_at DESC LIMIT 50")

	rows, err := h.pool.Query(ctx, sb.String())
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	builds, err := pgx.CollectRows(rows, pgx.RowToMap)
	if err != nil {
		return nil, err
	}
	return jsonResult(builds)
}

func (h *History) buildStats(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	pipeline, err := req.RequireString("pipeline")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	column, ok := sortColumns[req.GetString("sort", "started")]
	if !ok {
		return mcp.NewToolResultError("unknown sort"), nil
	}
	limit := req.GetInt("limit", 25)
	query := fmt.Sprintf("SELECT id, duration_ms, status FROM builds WHERE pipeline = $1 ORDER BY %s DESC LIMIT %d", column, limit)
	rows, err := h.pool.Query(ctx, query, pipeline)
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	stats, err := pgx.CollectRows(rows, pgx.RowToMap)
	if err != nil {
		return nil, err
	}
	return jsonResult(stats)
}

func (h *History) flakyTests(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	suite, err := req.RequireString("suite")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	name := req.GetString("name", "")
	var tests []FlakyTest
	query := h.db.Rebind("SELECT suite, name, fail_rate FROM flaky_tests WHERE suite = ? AND name ILIKE ? ORDER BY fail_rate DESC")
	if err := h.db.SelectContext(ctx, &tests, query, suite, "%"+name+"%"); err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	return jsonResult(tests)
}

func (h *History) jobReport(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	job, err := req.RequireString("job")
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	return h.report(ctx, fmt.Sprintf("SELECT job, count(*) AS runs, avg(duration_ms) AS avg_ms FROM job_runs WHERE job = '%s' GROUP BY job", job))
}

// report runs a summary query and returns its rows as JSON.
func (h *History) report(ctx context.Context, query string) (*mcp.CallToolResult, error) {
	rows, err := h.pool.Query(ctx, query)
	if err != nil {
		return mcp.NewToolResultError(err.Error()), nil
	}
	out, err := pgx.CollectRows(rows, pgx.RowToMap)
	if err != nil {
		return nil, err
	}
	return jsonResult(out)
}

func jsonResult(v any) (*mcp.CallToolResult, error) {
	b, err := json.MarshalIndent(v, "", "  ")
	if err != nil {
		return nil, err
	}
	return mcp.NewToolResultText(string(b)), nil
}
