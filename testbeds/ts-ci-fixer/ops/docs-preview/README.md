# Docs preview

Checks the docs preview a pull request deploys and fixes broken links in `docs/`. Open this
folder in VS Code (Copilot agent mode) or run `cursor-agent` from it; both may read the preview
site and the upstream API reference without asking.

Preview deploys land on a per-branch Vercel URL, so the fetch rules allow those hosts too.
