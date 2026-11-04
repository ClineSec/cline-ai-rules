// Package history answers questions about past builds from the build-history database.
package history

import (
	"context"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/jackc/pgx/v5/stdlib"
	"github.com/jmoiron/sqlx"
)

// History holds the database handles the tools use: pgx for most queries, and sqlx for
// the struct-scanning ones.
type History struct {
	pool *pgxpool.Pool
	db   *sqlx.DB
}

// Open connects to the build-history database.
func Open(ctx context.Context, url string) (*History, error) {
	pool, err := pgxpool.New(ctx, url)
	if err != nil {
		return nil, err
	}
	db := sqlx.NewDb(stdlib.OpenDBFromPool(pool), "pgx")
	return &History{pool: pool, db: db}, nil
}

// Close releases the connections.
func (h *History) Close() {
	h.db.Close()
	h.pool.Close()
}
