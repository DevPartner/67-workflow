#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Rewrites all commits in the repo to use a new author name and email.

.PARAMETER NewName
    The new author name to use for all commits. Defaults to "DevPartner".

.PARAMETER NewEmail
    The new author email. GitHub noreply format: ID+DevPartner@users.noreply.github.com
    Find your noreply email at: https://github.com/settings/emails

.EXAMPLE
    .\rewrite-git-author.ps1 -NewEmail "12345678+DevPartner@users.noreply.github.com"
#>
param(
    [string]$NewName  = "DevPartner",
    [string]$NewEmail = "info@dev-partner.biz"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Prompt for email if not provided
if (-not $NewEmail) {
    Write-Host ""
    Write-Host "Find your GitHub noreply email at: https://github.com/settings/emails"
    Write-Host "  Format: ID+DevPartner@users.noreply.github.com"
    Write-Host ""
    $NewEmail = Read-Host "Enter new author email"
    if (-not $NewEmail) {
        Write-Error "Email is required."
        exit 1
    }
}

# Show what we are about to do
Write-Host ""
Write-Host "=== Git Author Rewrite ===" -ForegroundColor Cyan
Write-Host "  New name  : $NewName"
Write-Host "  New email : $NewEmail"
Write-Host ""
Write-Host "Commits that will be rewritten:" -ForegroundColor Yellow
git log --oneline --all | Select-Object -First 20
$total = (git rev-list --all --count)
Write-Host "  ... ($total commits total)"
Write-Host ""
Write-Host "WARNING: This rewrites history. Any pushed branches will need --force-push." -ForegroundColor Red
Write-Host ""
$confirm = Read-Host "Type 'yes' to proceed"
if ($confirm -ne "yes") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

# Build the env-filter shell script (runs inside git's bundled sh on Windows)
$filter = @"
GIT_AUTHOR_NAME='$NewName'
GIT_AUTHOR_EMAIL='$NewEmail'
GIT_COMMITTER_NAME='$NewName'
GIT_COMMITTER_EMAIL='$NewEmail'
export GIT_AUTHOR_NAME GIT_AUTHOR_EMAIL GIT_COMMITTER_NAME GIT_COMMITTER_EMAIL
"@

Write-Host ""
Write-Host "Rewriting commits..." -ForegroundColor Cyan

git filter-branch -f --env-filter $filter --tag-name-filter cat -- --branches --tags

if ($LASTEXITCODE -ne 0) {
    Write-Error "git filter-branch failed (exit $LASTEXITCODE)."
    exit $LASTEXITCODE
}

# Remove the backup refs created by filter-branch
git for-each-ref --format="%(refname)" refs/original/ | ForEach-Object {
    git update-ref -d $_
}

Write-Host ""
Write-Host "Done. All commits now authored by: $NewName <$NewEmail>" -ForegroundColor Green
Write-Host ""
Write-Host "To push the rewritten history to GitHub:" -ForegroundColor Cyan
Write-Host "  git push --force-with-lease origin --all"
Write-Host "  git push --force-with-lease origin --tags"
