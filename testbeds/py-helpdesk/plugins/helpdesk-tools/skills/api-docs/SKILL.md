---
name: api-docs
description: Quote the helpdesk API reference for an endpoint a ticket mentions.
allowed-tools:
  - Read
  - WebFetch(domain:docs.example.com)
  - WebFetch(domain:*.docs.example.com)
---

# API docs

1. Find the endpoint in the ticket.
2. Fetch its page from the API reference and quote the request and response shapes.
