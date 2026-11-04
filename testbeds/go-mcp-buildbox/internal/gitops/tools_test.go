package gitops

import (
	"context"
	"testing"

	"github.com/mark3labs/mcp-go/mcp"
)

func TestCheckoutRejectsOptions(t *testing.T) {
	r := &Repo{Dir: t.TempDir()}
	req := mcp.CallToolRequest{}
	req.Params.Name = "git_checkout"
	req.Params.Arguments = map[string]any{"branch": "--orphan=scratch"}

	res, err := r.handleCheckout(context.Background(), req)
	if err != nil {
		t.Fatal(err)
	}
	if !res.IsError {
		t.Fatalf("expected an error result for an option-looking branch, got %+v", res)
	}
}
