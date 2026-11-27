[CmdletBinding()]
param(
    [switch]$PushBack,
    [switch]$AllAgents
)

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
$SkillNames = @("korean-humanizer", "narrative-forge", "literature-machine")
$HomeAgentsSkills = Join-Path $HOME ".agents\skills"

function Copy-CleanDir {
    param(
        [string]$Source,
        [string]$Destination
    )
    if (Test-Path $Destination) {
        Remove-Item -Path $Destination -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Get-ChildItem -Path $Source -Force | ForEach-Object {
        if ($_.Name -eq "__pycache__") { return }
        if ($_.Extension -in @(".pyc", ".pyo")) { return }
        $target = Join-Path $Destination $_.Name
        if ($_.PSIsContainer) {
            Copy-CleanDir -Source $_.FullName -Destination $target
        } else {
            Copy-Item -Path $_.FullName -Destination $target -Force
        }
    }
}

if ($PushBack) {
    Write-Host "[Sync] $HomeAgentsSkills -> $RepoRoot\skills"
    foreach ($name in $SkillNames) {
        $src = Join-Path $HomeAgentsSkills $name
        $dst = Join-Path $RepoRoot "skills\$name"
        if (-not (Test-Path $src)) {
            throw "Missing local skill directory: $src"
        }
        Copy-CleanDir -Source $src -Destination $dst
        Write-Host "  Synced <- $name"
    }
    Write-Host "[Done] Repository skills updated from local installation."
    exit 0
}

Write-Host "[Install] $RepoRoot\skills -> $HomeAgentsSkills"
New-Item -ItemType Directory -Force -Path $HomeAgentsSkills | Out-Null
foreach ($name in $SkillNames) {
    $src = Join-Path $RepoRoot "skills\$name"
    $dst = Join-Path $HomeAgentsSkills $name
    Copy-CleanDir -Source $src -Destination $dst
    Write-Host "  Installed -> $dst"
}

if ($AllAgents) {
    foreach ($agentRoot in @(".claude", ".codex")) {
        $agentDir = Join-Path $HOME $agentRoot
        if (Test-Path $agentDir) {
            $skillsDir = Join-Path $agentDir "skills"
            New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
            foreach ($name in $SkillNames) {
                Copy-CleanDir -Source (Join-Path $RepoRoot "skills\$name") -Destination (Join-Path $skillsDir $name)
            }
            Write-Host "  Also synced -> $skillsDir"
        }
    }
}

$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Warning "Python 3.10+ not found on PATH. Install Python to run audit_korean.py and novel_checker.py."
    exit 0
}

Write-Host "[Smoke Test] Verifying Python CLI checkers..."
& python (Join-Path $HomeAgentsSkills "korean-humanizer\scripts\audit_korean.py") --help | Out-Null
& python (Join-Path $HomeAgentsSkills "literature-machine\scripts\novel_checker.py") --help | Out-Null
Write-Host "[OK] Literature Machine is ready on this PC!"
