---
name: close-stale
description: Close tickets that have waited on the customer for more than 14 days, with a polite closing note.
allowed-tools:
  - Read
  - mcp__tickets__search_tickets
  - mcp__tickets__get_ticket
  - mcp__tickets__close_ticket
---

Find tickets in the `waiting-on-customer` state whose last customer reply is more than 14 days
old. For each one, read the thread, then close it with the note from
`docs/macros/stale-close.md`. Skip anything tagged `vip` or `legal-hold`.
