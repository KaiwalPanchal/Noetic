<#
One-command Noetic installer for Windows.
  irm https://raw.githubusercontent.com/KaiwalPanchal/Noetic/main/install.ps1 | iex
or, with options:
  & ([scriptblock]::Create((irm https://raw.githubusercontent.com/KaiwalPanchal/Noetic/main/install.ps1))) -Vault C:\vault -Owner Ada
#>
param(
  [string]$Vault = (Get-Location).Path,
  [string]$Owner,
  [string]$Agents,
  [switch]$WithWiki,
  [string]$Package = $(if ($env:NOETIC_PACKAGE) { $env:NOETIC_PACKAGE } else { 'noetic-engine' })
)
$ErrorActionPreference = 'Stop'

if (Get-Command uvx -ErrorAction SilentlyContinue) { $run = @('uvx', '--from', $Package, 'noetic') }
elseif (Get-Command pipx -ErrorAction SilentlyContinue) { $run = @('pipx', 'run', '--spec', $Package, 'noetic') }
else {
  Write-Error "Noetic needs uv (https://docs.astral.sh/uv/) or pipx. Install uv with: powershell -c `"irm https://astral.sh/uv/install.ps1 | iex`""
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
