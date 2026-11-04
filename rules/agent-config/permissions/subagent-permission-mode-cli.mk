# Fixture for subagent-permission-mode-cli: a Makefile and package.json style script lines.
CLAUDE ?= claude

lint-fix:
	# ruleid: subagent-permission-mode-cli
	@$(CLAUDE) -p "fix lint" --agents '{"fixer":{"description":"d","prompt":"p","permissionMode":"acceptEdits"}}'

review:
	# ok: subagent-permission-mode-cli
	@$(CLAUDE) -p "review" --agents '{"reviewer":{"description":"d","prompt":"p","tools":["Read"]}}'
