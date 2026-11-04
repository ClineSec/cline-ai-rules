# Developer shortcuts for devtools-mcp.

.PHONY: test serve serve-http serve-notes-team image

test:
	uv run --extra dev pytest -q

serve:
	uv run devtools-mcp

serve-http:
	uv run devtools-mcp --transport streamable-http

# Shares the notes server with the team for a planning session.
serve-notes-team:
	FASTMCP_TRANSPORT=http FASTMCP_HOST=0.0.0.0 FASTMCP_PORT=8812 uv run --extra contrib python contrib/notes_server.py

image:
	docker build -f deploy/contrib.Dockerfile -t devtools-contrib:dev .
