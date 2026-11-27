param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
)

$ErrorActionPreference = 'Stop'

$repo = (Resolve-Path $RepoRoot).Path
Set-Location $repo

git config core.hooksPath ".githooks"
git config commit.template ".gitmessage.txt"
git config pull.rebase true
git config rebase.autoStash true
git config fetch.prune true
git config branch.autosetuprebase always

Write-Host "Configured Git hooks and commit template for $repo"
