<#
One-command OverMind installer for Windows.
  irm https://raw.githubusercontent.com/KaiwalPanchal/OverMind/main/install.ps1 | iex
or, with options:
  & ([scriptblock]::Create((irm https://raw.githubusercontent.com/KaiwalPanchal/OverMind/main/install.ps1))) -Vault C:\vault -Owner Ada
#>
param(
  [string]$Vault = (Get-Location).Path,
  [string]$Owner,
  [string]$Agents,
  [switch]$WithWiki,
  [string]$Package = $(if ($env:OVERMIND_PACKAGE) { $env:OVERMIND_PACKAGE } else { 'overmind-engine' })
)
$ErrorActionPreference = 'Stop'

if (Get-Command uvx -ErrorAction SilentlyContinue) { $run = @('uvx', '--from', $Package, 'overmind') }
elseif (Get-Command pipx -ErrorAction SilentlyContinue) { $run = @('pipx', 'run', '--spec', $Package, 'overmind') }
else {
  Write-Error "OverMind needs uv (https://docs.astral.sh/uv/) or pipx. Install uv with: powershell -c `"irm https://astral.sh/uv/install.ps1 | iex`""
  exit 1
}

$install = @('install', '--vault', $Vault)
if ($Owner)    { $install += @('--owner', $Owner) }
if ($Agents)   { $install += @('--agents', $Agents) }
if ($WithWiki) { $install += '--with-wiki' }

& $run[0] @($run[1..($run.Length - 1)] + $install)
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "`nDone. Wire it into your AI client (Claude Desktop, Claude Code, Cursor, Windsurf):"
Write-Host "  $($run -join ' ') mcp-config --vault `"$Vault`""
