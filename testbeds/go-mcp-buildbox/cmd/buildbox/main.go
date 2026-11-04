// Command buildbox serves the repository and build-history tools over stdio.
package main

import (
	"context"
	"log"
	"os"

	"github.com/mark3labs/mcp-go/server"

	"example.com/buildbox-mcp/internal/gitops"
	"example.com/buildbox-mcp/internal/history"
)

func getenv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func main() {
	ctx := context.Background()

	s := server.NewMCPServer(
		"buildbox",
		"0.4.0",
		server.WithToolCapabilities(false),
		server.WithRecovery(),
	)

	repo := &gitops.Repo{Dir: getenv("BUILDBOX_REPO", "/srv/buildbox/repo")}
	repo.Register(s)

	h, err := history.Open(ctx, getenv("BUILDBOX_DATABASE_URL", "postgres://buildbox@db.example.invalid/history"))
	if err != nil {
		log.Fatalf("history: %v", err)
	}
	defer h.Close()
	h.Register(s)

	if err := server.ServeStdio(s); err != nil {
		log.Fatal(err)
	}
}
