# Ticket backfill

One-off job that re-summarizes closed tickets from 2024 with Gemini so the new search index has
consistent summaries. Run `gemini` from this folder; it picks up `.gemini/.env` and
`.gemini/settings.json` here.

The summaries go through the analytics team's caching proxy (it deduplicates the many
near-identical tickets), and the run is traced to their collector so we can see cost per batch.
The job itself reads `../../helpdesk/` and writes nothing outside `out/`.
