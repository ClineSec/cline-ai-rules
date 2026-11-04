package store

import (
	"context"

	"github.com/mark3labs/mcp-go/mcp"
	"gorm.io/gorm"
	"gorm.io/gorm/clause"
)

type Ticket struct {
	ID    uint
	Queue string
	Title string
}

type GormTickets struct{ db *gorm.DB }

type FilterArgs struct {
	Queue string `json:"queue"`
	Sort  string `json:"sort"`
	ID    string `json:"id"`
}

func (g *GormTickets) filter(ctx context.Context, req mcp.CallToolRequest, args FilterArgs) (*mcp.CallToolResult, error) {
	var out []Ticket
	// ruleid: mcp-tool-arg-to-sql-go
	g.db.WithContext(ctx).Where("queue = '" + args.Queue + "'").Find(&out)
	// ok: mcp-tool-arg-to-sql-go
	g.db.WithContext(ctx).Where("queue = ?", args.Queue).Find(&out)
	// ok: mcp-tool-arg-to-sql-go
	g.db.WithContext(ctx).Where(&Ticket{Queue: args.Queue}).Find(&out)
	// ruleid: mcp-tool-arg-to-sql-go
	g.db.Order(args.Sort).Find(&out)
	// ok: mcp-tool-arg-to-sql-go
	g.db.Order(clause.OrderByColumn{Column: clause.Column{Name: args.Sort}}).Find(&out)
	var one Ticket
	// ruleid: mcp-tool-arg-to-sql-go
	g.db.First(&one, args.ID)
	// ok: mcp-tool-arg-to-sql-go
	g.db.First(&one, "id = ?", args.ID)
	// ruleid: mcp-tool-arg-to-sql-go
	g.db.Raw("SELECT * FROM tickets WHERE title LIKE '%" + args.Queue + "%'").Scan(&out)
	return nil, nil
}
