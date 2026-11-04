// Command buildbox-http serves the build-runner and artifact tools over Streamable HTTP.
package main

import (
	"log"
	"net/http"
	"os"

	"github.com/modelcontextprotocol/go-sdk/mcp"

	"example.com/buildbox-mcp/internal/artifacts"
	"example.com/buildbox-mcp/internal/runner"
)

func main() {
	srv := mcp.NewServer(&mcp.Implementation{Name: "buildbox-runner", Version: "0.4.0"}, nil)

	shell := os.Getenv("BUILDBOX_SHELL")
	if shell == "" {
		shell = "/bin/bash"
	}
	runner.Register(srv, runner.Config{Shell: shell, Workdir: "/srv/buildbox/repo"})

	store, err := artifacts.Open(os.Getenv("BUILDBOX_DATABASE_URL"))
	if err != nil {
		log.Fatalf("artifacts: %v", err)
	}
	store.Register(srv)

	handler := mcp.NewStreamableHTTPHandler(func(*http.Request) *mcp.Server { return srv }, nil)
	log.Fatal(http.ListenAndServe("127.0.0.1:8931", handler))
}
