# SyncGit-MHS.ps1
# PowerShell 7 Compatible
# Sync MHS Sports Schedule App + OneDrive Mirror
# ============================================

# -------------------------------------------
# Load WinForms safely for PowerShell 7
# -------------------------------------------
try {
    Add-Type -AssemblyName System.Windows.Forms -ErrorAction Stop
}
catch {
    $winForms = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\System.Windows.Forms.dll"
    if (Test-Path $winForms) {
        Add-Type -Path $winForms
    }
}

# -------------------------------------------
# Configuration
# -------------------------------------------
$RepoPath = "C:\.ScriptLibrary\MHS"
$OneDrivePath = "C:\Users\21968\OneDrive - WilmerHale\.ScriptLibrary\MHS"
$MainBranch = "main"
$RemoteName = "origin"

# -------------------------------------------
# Helper Functions
# -------------------------------------------

function Write-Section {
    param([string]$Text)
    Write-Host ""
    Write-Host $Text
    Write-Host ""
}

function Stop-WithError {
    param(
        [string]$Message,
        [int]$Code = 1
    )
    Write-Host ""
    Write-Host "ERROR: $Message" -ForegroundColor Red
    Write-Host ""
    try {
        [System.Windows.Forms.MessageBox]::Show(
            $Message,
            "Git Sync Error - MHS",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        ) | Out-Null
    }
    catch {}
    exit $Code
}

function Invoke-GitChecked {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Arguments,
        [string]$ActionDescription = "Git command"
    )

    $output = & git @Arguments 2>&1 | Where-Object {
        $_ -notmatch "^Already on " -and
        $_ -notmatch "^Switched to branch " -and
        $_ -notmatch "^From https?://" -and
        $_ -notmatch "^To https?://" -and
        $_ -notmatch "^\s*\* branch\s+" -and
        $_ -notmatch "^\s+[0-9a-f]+\.\.[0-9a-f]+\s+" -and
        $_ -notmatch "^Everything up-to-date"
    }
    $exitCode = $LASTEXITCODE

    if ($exitCode -ne 0) {
        $outputText = ($output | Out-String).Trim()
        if ([string]::IsNullOrWhiteSpace($outputText)) {
            $outputText = "No additional error output returned by git."
        }
        throw "$ActionDescription failed.`nCommand: git $($Arguments -join ' ')`n$outputText"
    }

    return $output
}

# -------------------------------------------
# Validation
# -------------------------------------------

if (-not (Test-Path $RepoPath)) {
    Stop-WithError -Message "Repo path not found: $RepoPath`nRun: git clone https://github.com/SDautovic-GH/MHS.git '$RepoPath'"
}

Set-Location $RepoPath

$gitDir = & git rev-parse --git-dir 2>$null
if ($LASTEXITCODE -ne 0 -or $gitDir -ne ".git") {
    Stop-WithError -Message "Path is not a standalone Git repository: $RepoPath"
}

$configuredRemotes = & git remote 2>$null
if ($configuredRemotes -notcontains $RemoteName) {
    Stop-WithError -Message "Remote '$RemoteName' is not configured."
}

# -------------------------------------------
# Sync MHS repo
# -------------------------------------------

try {
    Write-Section "Syncing MHS repo..."

    $GitIgnorePath = Join-Path $RepoPath ".gitignore"
    $GitIgnorePatterns = @(".DS_Store", "Thumbs.db", "*.log", "*.local")
    if (-not (Test-Path $GitIgnorePath)) {
        New-Item -Path $GitIgnorePath -ItemType File -Force | Out-Null
    }
    $content = Get-Content $GitIgnorePath -ErrorAction SilentlyContinue
    foreach ($pattern in $GitIgnorePatterns) {
        if ($content -notcontains $pattern) {
            Add-Content -Path $GitIgnorePath -Value $pattern
        }
    }

    $mergeHead = Join-Path $RepoPath ".git/MERGE_HEAD"
    if (Test-Path $mergeHead) {
        Write-Host "Unresolved merge detected - aborting before checkout."
        & git merge --abort 2>$null
    }

    $rebaseMergeDir = Join-Path $RepoPath ".git/rebase-merge"
    $rebaseApplyDir = Join-Path $RepoPath ".git/rebase-apply"
    if ((Test-Path $rebaseMergeDir) -or (Test-Path $rebaseApplyDir)) {
        Write-Host "Unresolved rebase detected - aborting before checkout."
        & git rebase --abort 2>$null
    }

    Invoke-GitChecked -Arguments @("checkout", $MainBranch) -ActionDescription "Checkout $MainBranch"

    $isDirty = [bool](& git status --porcelain 2>$null)
    $stashed = $false
    if ($isDirty) {
        Write-Host "Local changes detected - stashing before pull."
        $stashLabel = "auto-sync-prepull-$(Get-Date -Format 'yyyyMMddHHmmss')"
        Invoke-GitChecked -Arguments @("stash", "push", "-u", "-m", $stashLabel) `
            -ActionDescription "Stash local changes before pull"
        $stashed = $true
    }

    $hasRemoteRef = & git ls-remote --heads $RemoteName $MainBranch 2>$null
    if ($hasRemoteRef) {
        Invoke-GitChecked -Arguments @("fetch", $RemoteName, $MainBranch) `
            -ActionDescription "Fetch $MainBranch from $RemoteName"
        try {
            Invoke-GitChecked -Arguments @("merge", "--ff-only", "$RemoteName/$MainBranch") `
                -ActionDescription "Fast-forward $MainBranch to $RemoteName/$MainBranch"
        }
        catch {
            if ($stashed) { & git stash pop 2>$null }
            Stop-WithError -Message ("Cannot fast-forward $MainBranch from $RemoteName/$MainBranch.`n" +
                "Local branch has commits that aren't on the remote, or history has diverged.")
        }
    }

    if ($stashed) {
        $popOutput = & git stash pop 2>&1
        if ($LASTEXITCODE -ne 0) {
            Stop-WithError -Message ("Stash-pop conflict after pull. Your local changes remain in the stash.")
        }
    }

    # Force-add web files (.html, .md, .json)
    $forceFiles = Get-ChildItem -Path $RepoPath -Recurse -File -ErrorAction SilentlyContinue | Where-Object { $_.Extension -match '^\.(md|html|json)$' }
    foreach ($f in $forceFiles) {
        & git add --force -- $f.FullName 2>$null
    }

    Invoke-GitChecked -Arguments @("add", "-A") -ActionDescription "Stage MHS changes"
    $postPullChanges = & git status --porcelain 2>$null
    if ($postPullChanges) {
        $TimeStamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        Invoke-GitChecked -Arguments @("commit", "-m", "Auto sync Windows $TimeStamp") -ActionDescription "Commit MHS changes"
    }

    $unpushed = & git log "$RemoteName/$MainBranch..$MainBranch" --oneline 2>$null
    if ($unpushed -or (-not $hasRemoteRef)) {
        Invoke-GitChecked -Arguments @("push", "-u", $RemoteName, $MainBranch) -ActionDescription "Push MHS to $RemoteName"
        Write-Host "MHS updated on GitHub."
    }
    else {
        Write-Host "MHS sync completed successfully. (Up to date)"
    }
}
catch {
    Stop-WithError -Message $_.Exception.Message
}

# -------------------------------------------
# Mirror to OneDrive
# -------------------------------------------
if (Test-Path $OneDrivePath) {
    Write-Section "Mirroring MHS to OneDrive..."
    robocopy $RepoPath $OneDrivePath /MIR /R:1 /W:1 /XD ".git" | Out-Null
}

Write-Host ""
Write-Host "MHS sync complete."
