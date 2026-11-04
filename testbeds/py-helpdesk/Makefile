# Developer shortcuts. `make help` lists them.
PYTHON ?= python3
CLAUDE ?= npx -y @anthropic-ai/claude-code@2.1.308
CODEX ?= codex
PROMPT ?= summarize the failing tests in pytest.log
# Used by the unattended targets below so they never stop for a prompt.
AGENT_ARGS ?= --output-format stream-json --dangerously-skip-permissions

.PHONY: help test lint agent-triage agent-fix agent-explain

help:
	@echo "make test           run the test suite"
	@echo "make agent-triage   let Claude triage pytest.log (runs claude --dangerously-skip-permissions)"
	@echo "make agent-explain  explain failures, read-only"

test:
	$(PYTHON) -m pytest -q | tee pytest.log

lint:
	$(PYTHON) -m ruff check helpdesk tests

agent-triage: test
	$(CLAUDE) -p "$(PROMPT)" $(AGENT_ARGS)

agent-fix:
	-$(CODEX) exec --sandbox danger-full-access "$(PROMPT), then fix them"

agent-explain:
	$(CLAUDE) -p "$(PROMPT)" --permission-mode dontAsk --allowedTools "Read" "Bash(cat pytest.log)"
