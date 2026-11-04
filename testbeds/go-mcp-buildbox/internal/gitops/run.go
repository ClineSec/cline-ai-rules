package gitops

import (
	"context"
	"os/exec"
	"strings"
	"time"
)

const gitTimeout = 30 * time.Second

// run executes argv in the repository with a timeout and returns trimmed combined output.
func (r *Repo) run(ctx context.Context, argv []string) (string, error) {
	ctx, cancel := context.WithTimeout(ctx, gitTimeout)
	defer cancel()
	cmd := exec.CommandContext(ctx, argv[0], argv[1:]...)
	cmd.Dir = r.Dir
	cmd.Env = append(cmd.Environ(), "GIT_TERMINAL_PROMPT=0")
	out, err := cmd.CombinedOutput()
	return strings.TrimSpace(string(out)), err
}
