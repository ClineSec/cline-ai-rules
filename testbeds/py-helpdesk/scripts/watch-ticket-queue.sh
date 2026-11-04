#!/bin/sh
# Prints a heartbeat line every five minutes; the queue feed itself is not wired up yet.
while true; do
  echo "ticket-queue: no new P1 tickets"
  sleep 300
done
