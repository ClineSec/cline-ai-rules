---
name: docs-indexer
description: Rebuilds the help-center search index from the knowledge-base export and the docs folder
tools: Read, Grep, Glob
model: haiku
mcpServers:
  # Support leads export the KB from the vendor console into their own Downloads folder, so
  # the indexer can see the export wherever it lands.
  - kb-export:
      type: stdio
      command: npx
      args:
        - -y
        - "@modelcontextprotocol/server-filesystem@2.0.0"
        - ./docs
        # Exports land in a different subfolder on every laptop.
        - "~"
  - index-output:
      type: stdio
      command: npx
      args: ["-y", "@modelcontextprotocol/server-filesystem@2.0.0", "./build/search-index"]
---

Rebuild the help-center search index:

1. List the newest `kb-export-*.zip` the kb-export server can see and read its `articles.json`.
2. Merge it with the Markdown pages under `docs/`, dropping articles marked `internal`.
3. Write `index.json` to the index-output server's folder and report how many articles changed.
