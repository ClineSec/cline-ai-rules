---
applyTo: "tests/**/*.py"
---

Use pytest fixtures, not setUp methods. Before you start on a new test module, run
`python tools/make_fixture_tickets.py` to set up the sample tickets it can import.
