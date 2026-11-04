package tools

import (
	"context"
	"database/sql"

	"github.com/mark3labs/mcp-go/mcp"
)

type Catalog struct{ db *sql.DB }

func (c *Catalog) ordersPrompt(ctx context.Context, req mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
	customer := req.Params.Arguments["customer"]
	// ruleid: mcp-tool-arg-to-sql-go
	rows, err := c.db.QueryContext(ctx, "SELECT id, total FROM orders WHERE customer = '"+customer+"'")
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return mcp.NewGetPromptResult("Orders", nil), nil
}

func (c *Catalog) ordersPromptSafe(ctx context.Context, req mcp.GetPromptRequest) (*mcp.GetPromptResult, error) {
	customer := req.Params.Arguments["customer"]
	// ok: mcp-tool-arg-to-sql-go
	rows, err := c.db.QueryContext(ctx, "SELECT id, total FROM orders WHERE customer = $1", customer)
	if err != nil {
		return nil, err
	}
	defer rows.Close()
	return mcp.NewGetPromptResult("Orders", nil), nil
}
