// Package artifacts lists build artifacts recorded in the build-history database.
package artifacts

import (
	"context"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

type Artifact struct {
	ID        uint      `json:"id"`
	BuildID   uint      `json:"build_id"`
	Name      string    `json:"name"`
	Kind      string    `json:"kind"`
	SizeBytes int64     `json:"size_bytes"`
	CreatedAt time.Time `json:"created_at"`
}

type Store struct {
	db *gorm.DB
}

type ListIn struct {
	Build  uint   `json:"build" jsonschema:"build id"`
	Kind   string `json:"kind" jsonschema:"artifact kind, such as binary or coverage"`
	Fields string `json:"fields,omitempty" jsonschema:"comma-separated columns to return"`
}

type ListOut struct {
	Artifacts []Artifact `json:"artifacts"`
}

// Open connects to the database.
func Open(dsn string) (*Store, error) {
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		return nil, err
	}
	return &Store{db: db}, nil
}

// Register adds the artifact tools to srv.
func (s *Store) Register(srv *mcp.Server) {
	mcp.AddTool(srv, &mcp.Tool{Name: "artifact_list", Description: "List the artifacts of a build."}, s.list)
}

func (s *Store) list(ctx context.Context, _ *mcp.CallToolRequest, in ListIn) (*mcp.CallToolResult, ListOut, error) {
	q := s.db.WithContext(ctx).Model(&Artifact{}).Where("build_id = ? AND kind = ?", in.Build, in.Kind)
	if in.Fields != "" {
		q = q.Select(in.Fields)
	}
	var out []Artifact
	if err := q.Order("created_at DESC").Find(&out).Error; err != nil {
		return nil, ListOut{}, err
	}
	return nil, ListOut{Artifacts: out}, nil
}
