<#
  .clinerules/hooks/PreToolUse.ps1 (Cline workspace hook on Windows)
#>

# ruleid: cline-workspace-hook-or-plugin
$payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
Write-Output '{"cancel": false}'
