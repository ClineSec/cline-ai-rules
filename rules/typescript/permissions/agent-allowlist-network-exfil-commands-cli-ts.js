const { spawnSync, exec } = require("child_process");

function checkHosts(prompt) {
  // ruleid: agent-allowlist-network-exfil-commands-cli-ts
  return spawnSync("claude", ["-p", prompt, "--allowedTools", "Read", "Bash(nslookup:*)"]);
}

function runTests(prompt) {
  // ok: agent-allowlist-network-exfil-commands-cli-ts
  return spawnSync("claude", ["-p", prompt, "--allowedTools", "Read", "Bash(npm test:*)"]);
}

function pingHosts() {
  // ruleid: agent-allowlist-network-exfil-commands-cli-ts
  exec('gemini -p "ping the hosts" --allowed-tools "run_shell_command(ping)"');
}

module.exports = { checkHosts, runTests, pingHosts };
