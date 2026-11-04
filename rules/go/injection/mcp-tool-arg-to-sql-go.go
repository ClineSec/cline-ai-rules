package store

import (
	"context"
	"database/sql"
	"fmt"
	"slices"
	"strings"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jmoiron/sqlx"
	"github.com/lib/pq"
	"github.com/mark3labs/mcp-go/mcp"
	sdk "github.com/modelcontextprotocol/go-sdk/mcp"
)

var sortColumns = map[string]string{"created": "created_at", "priority": "priority"}

var tables = []string{"tickets", "comments"}

type Tickets struct {
	db   *sql.DB
	pool *pgxpool.Pool
	x    *sqlx.DB
}

type SearchIn struct {
	Queue string `json:"queue"`
	Limit int    `json:"limit"`
	Sort  string `json:"sort"`
}

func (t *Tickets) search(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	queue := req.GetString("queue", "")
	// ruleid: mcp-tool-arg-to-sql-go
	rows, err := t.db.QueryContext(ctx, "SELECT id, title FROM tickets WHERE queue = '"+queue+"'")
	if err != nil {
		return nil, err
	}
	rows.Close()
	// ok: mcp-tool-arg-to-sql-go
	rows, err = t.db.QueryContext(ctx, "SELECT id, title FROM tickets WHERE queue = $1", queue)
	if err != nil {
		return nil, err
	}
	rows.Close()
	// ok: mcp-tool-arg-to-sql-go
	t.db.Query("SELECT id FROM tickets WHERE queue = ?", queue)
	limit := req.GetInt("limit", 20)
	// ok: mcp-tool-arg-to-sql-go
	t.db.Query(fmt.Sprintf("SELECT id FROM tickets LIMIT %d", limit))
	return nil, nil
}

func (t *Tickets) report(ctx context.Context, req *sdk.CallToolRequest, in SearchIn) (*sdk.CallToolResult, any, error) {
	q := fmt.Sprintf("SELECT id, title FROM tickets WHERE queue = '%s' ORDER BY %s LIMIT %d", in.Queue, in.Sort, in.Limit)
	// ruleid: mcp-tool-arg-to-sql-go
	rows, err := t.pool.Query(ctx, q)
	if err != nil {
		return nil, nil, err
	}
	rows.Close()
	col := sortColumns[in.Sort]
	// ok: mcp-tool-arg-to-sql-go
	t.pool.Query(ctx, "SELECT id FROM tickets WHERE queue = $1 ORDER BY "+col+" LIMIT $2", in.Queue, in.Limit)
	// ok: mcp-tool-arg-to-sql-go
	t.pool.Query(ctx, "SELECT id FROM "+pgx.Identifier{in.Sort}.Sanitize())
	// ok: mcp-tool-arg-to-sql-go
	t.pool.Exec(ctx, "NOTIFY ticket_events, "+pq.QuoteLiteral(in.Queue))
	var b strings.Builder
	b.WriteString("SELECT count(*) FROM tickets WHERE status = '")
	b.WriteString(in.Queue)
	b.WriteString("'")
	var n int
	// ruleid: mcp-tool-arg-to-sql-go
	err = t.x.Get(&n, b.String())
	return nil, n, err
}

func (t *Tickets) purge(ctx context.Context, req mcp.CallToolRequest) (*mcp.CallToolResult, error) {
	table := req.GetString("table", "")
	if !slices.Contains(tables, table) {
		return mcp.NewToolResultError("unknown table"), nil
	}
	// ok: mcp-tool-arg-to-sql-go
	t.db.ExecContext(ctx, "DELETE FROM "+table+" WHERE closed_at < now() - interval '90 days'")
	before := req.GetString("before", "")
	// ruleid: mcp-tool-arg-to-sql-go
	t.exec(ctx, fmt.Sprintf("DELETE FROM comments WHERE created_at < '%s'", before))
	// ok: mcp-tool-arg-to-sql-go
	t.logf("DELETE FROM comments WHERE created_at < '%s'", before)
	return nil, nil
}

func (t *Tickets) byStatus(ctx context.Context, req mcp.CallToolRequest, fallback string) (*mcp.CallToolResult, error) {
	status := req.GetString("status", "open")
	switch status {
	case "open", "closed":
		// ok: mcp-tool-arg-to-sql-go
		t.db.QueryContext(ctx, "SELECT id FROM tickets WHERE status = '"+status+"'")
	case fallback:
		// ruleid: mcp-tool-arg-to-sql-go
		t.db.QueryContext(ctx, "SELECT id FROM tickets WHERE status = '"+status+"'")
	}
	return nil, nil
}

func (t *Tickets) exec(ctx context.Context, stmt string) error {
	_, err := t.db.ExecContext(ctx, stmt)
	return err
}

func (t *Tickets) logf(format string, args ...any) {}
