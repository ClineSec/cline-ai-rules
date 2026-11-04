#!/usr/bin/env bash
# Before the first Bash call of a status-digest run: make sure the hd CLI can reach the queue.
hd queue ping --quiet >/dev/null 2>&1 || echo "hd queue unreachable; the digest will use cached counts" >&2
exit 0
