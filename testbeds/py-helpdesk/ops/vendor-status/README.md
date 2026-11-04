# Vendor status

On-call reads vendor status pages from here when a ticket spike looks like an upstream
outage. Run Claude Code (or Qwen Code) from this folder and ask it to check the vendors listed in
`vendors.md`; it fetches each status page and summarizes open incidents.

The payment vendor moved its status page to a Railway app last quarter, so the settings
allow Railway hosts as well as our own status domain.
