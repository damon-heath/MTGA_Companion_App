param(
  [Parameter(Mandatory=$true)][string]$Version,
  [Parameter(Mandatory=$true)][string]$ArtifactDir,
  [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Assert-CommandAvailable {
  param([Parameter(Mandatory=$true)][string]$Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required command '$Name' was not found in PATH."
  }
}

function Invoke-CheckedCommand {
  param(
    [Parameter(Mandatory=$true)][string]$Description,
    [Parameter(Mandatory=$true)][scriptblock]$Command
  )

  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Description failed with exit code $LASTEXITCODE."
  }
}

function Resolve-ArtifactPath {
  param([Parameter(Mandatory=$true)][string]$PathValue)
  try {
    $resolved = Resolve-Path -LiteralPath $PathValue -ErrorAction Stop
  } catch {
    throw "Artifact directory '$PathValue' does not exist."
  }

  if (-not (Test-Path -LiteralPath $resolved.Path -PathType Container)) {
    throw "Artifact path '$($resolved.Path)' is not a directory."
  }

  return $resolved.Path
}

function Assert-RequiredArtifacts {
  param(
    [Parameter(Mandatory=$true)][string]$ArtifactPath,
    [Parameter(Mandatory=$true)][string[]]$RequiredFileNames
  )

  foreach ($name in $RequiredFileNames) {
    $path = Join-Path $ArtifactPath $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
      throw "Missing required artifact '$name' in '$ArtifactPath'."
    }
    if ((Get-Item -LiteralPath $path).Length -le 0) {
      throw "Required artifact '$name' is empty."
    }
  }
}

function Write-Checksums {
  param(
    [Parameter(Mandatory=$true)][string]$ArtifactPath,
    [Parameter(Mandatory=$true)][System.IO.FileInfo[]]$ArtifactFiles
  )

  if ($ArtifactFiles.Count -eq 0) {
    throw "No artifact files available for checksum generation in '$ArtifactPath'."
  }

  $checksumsPath = Join-Path $ArtifactPath "checksums.txt"
  $lines = foreach ($file in $ArtifactFiles) {
    $hash = Get-FileHash -Algorithm SHA256 -Path $file.FullName
    "{0}  {1}" -f $hash.Hash.ToLowerInvariant(), $file.Name
  }

  Set-Content -LiteralPath $checksumsPath -Value $lines -Encoding utf8
  return $checksumsPath
}

function Verify-Checksums {
  param(
    [Parameter(Mandatory=$true)][string]$ArtifactPath,
    [Parameter(Mandatory=$true)][string]$ChecksumsPath
  )

  if (-not (Test-Path -LiteralPath $ChecksumsPath -PathType Leaf)) {
    throw "Checksum file '$ChecksumsPath' was not generated."
  }

  foreach ($line in Get-Content -LiteralPath $ChecksumsPath) {
    if (-not $line.Trim()) {
      continue
    }
    if ($line -notmatch '^(?<hash>[A-Fa-f0-9]{64})\s{2}(?<name>.+)$') {
      throw "Invalid checksum line format: '$line'."
    }

    $expected = $Matches.hash.ToLowerInvariant()
    $name = $Matches.name.Trim()
    $filePath = Join-Path $ArtifactPath $name

    if (-not (Test-Path -LiteralPath $filePath -PathType Leaf)) {
      throw "Missing artifact referenced by checksums.txt: '$name'."
    }

    $actual = (Get-FileHash -Algorithm SHA256 -Path $filePath).Hash.ToLowerInvariant()
    if ($expected -ne $actual) {
      throw "Checksum mismatch for '$name'. Expected '$expected', got '$actual'."
    }
  }
}

if ($Version -notmatch '^\d+\.\d+\.\d+$') {
  throw "Version must be semantic format like 1.0.0."
}

Assert-CommandAvailable -Name "git"
Assert-CommandAvailable -Name "gh"

$artifactPath = Resolve-ArtifactPath -PathValue $ArtifactDir
$requiredArtifacts = @(
  "ArenaCompanionSetup.exe",
  "ArenaCompanion-onefolder.zip"
)
Assert-RequiredArtifacts -ArtifactPath $artifactPath -RequiredFileNames $requiredArtifacts

$releaseNotesPath = (Resolve-Path -LiteralPath "docs/release-notes.md" -ErrorAction Stop).Path

$artifactFilesForChecksums = Get-ChildItem -LiteralPath $artifactPath -File |
  Where-Object { $_.Name -ne "checksums.txt" } |
  Sort-Object Name

if ($artifactFilesForChecksums.Count -eq 0) {
  throw "Artifact directory '$artifactPath' does not contain release files."
}

$checksumsPath = Write-Checksums -ArtifactPath $artifactPath -ArtifactFiles $artifactFilesForChecksums
Verify-Checksums -ArtifactPath $artifactPath -ChecksumsPath $checksumsPath

$tag = "v$Version"

if ($DryRun) {
  Write-Host "Preflight passed for '$tag'. Dry run enabled; skipping tag creation and GitHub release publish."
  exit 0
}

$null = git rev-parse --verify --quiet $tag 2>$null
if ($LASTEXITCODE -eq 0) {
  throw "Tag '$tag' already exists."
}
if ($LASTEXITCODE -gt 1) {
  throw "Unable to verify whether tag '$tag' exists (exit code $LASTEXITCODE)."
}

Invoke-CheckedCommand -Description "Create git tag '$tag'" -Command {
  git tag -a $tag -m "Release $tag"
}

Invoke-CheckedCommand -Description "Push git tag '$tag' to origin" -Command {
  git push origin $tag
}

$artifactFiles = Get-ChildItem -LiteralPath $artifactPath -File |
  Sort-Object Name |
  ForEach-Object { $_.FullName }

Invoke-CheckedCommand -Description "Create GitHub release '$tag'" -Command {
  gh release create $tag --title "Arena Companion $tag" --notes-file $releaseNotesPath @artifactFiles
}
