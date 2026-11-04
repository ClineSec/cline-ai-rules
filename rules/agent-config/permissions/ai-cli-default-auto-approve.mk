# Fixture for ai-cli-default-auto-approve: Makefile recipes.
CLINE ?= npx -y cline@3.0.73
PROMPT ?= summarize the failing tests in pytest.log

agent-triage:
	# ruleid: ai-cli-default-auto-approve
	$(CLINE) --json "$(PROMPT)"

agent-ask:
	# ruleid: ai-cli-default-auto-approve
	@amp --execute "$(PROMPT)"

agent-plan:
	# ok: ai-cli-default-auto-approve
	$(CLINE) --plan "$(PROMPT)"

agent-safe:
	# ok: ai-cli-default-auto-approve
	-$(CLINE) --auto-approve false "$(PROMPT)"
