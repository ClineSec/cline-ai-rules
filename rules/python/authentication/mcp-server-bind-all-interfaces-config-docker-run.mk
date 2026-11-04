IMAGE ?= example-org/repo-tools-mcp:1.4.0

run-lan:
	# ruleid: mcp-server-bind-all-interfaces-config-docker-run
	docker run --rm -p 8000:8000 -e FASTMCP_HOST=0.0.0.0 $(IMAGE)

run:
	# ok: mcp-server-bind-all-interfaces-config-docker-run
	docker run --rm -p 127.0.0.1:8000:8000 -e FASTMCP_HOST=0.0.0.0 $(IMAGE)
