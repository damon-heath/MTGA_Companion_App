param(
  [Parameter(Mandatory = $true)]
  [string[]]$ArtifactPaths,
  [Parameter(Mandatory = $true)]
  [string]$PfxPath,
  [Parameter(Mandatory = $true)]
  [string]$PfxPassword,
  [string]$TimestampUrl = "http://timestamp.digicert.com"
)

$ErrorActionPreference = "Stop"

function Resolve-SignTool {
  $cmd = Get-Command signtool.exe -ErrorAction SilentlyContinue
  if ($cmd) {
    return $cmd.Source
  }

  $candidateRoots = @(
    "C:\\Program Files (x86)\\Windows Kits\\10\\bin",
    "C:\\Program Files (x86)\\Windows Kits\\11\\bin",
    "C:\\Program Files (x86)\\Windows Kits\\10\\App Certification Kit",
    "C:\\Program Files (x86)\\Windows Kits\\11\\App Certification Kit"
  )

  $matches = @()
  foreach ($root in $candidateRoots) {
    if (-not (Test-Path $root)) {
      continue
    }
    $matches += Get-ChildItem -Path $root -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue
  }

  if (-not $matches -or $matches.Count -eq 0) {
    throw "Unable to locate signtool.exe. Checked paths: $($candidateRoots -join ', ')"
  }

  $preferred = $matches |
    Where-Object { $_.FullName -match "\\x64\\signtool.exe$" } |
    Sort-Object FullName -Descending
  if ($preferred -and $preferred.Count -gt 0) {
    return $preferred[0].FullName
  }

  $fallback = $matches | Sort-Object FullName -Descending
  return $fallback[0].FullName
}

if (-not (Test-Path $PfxPath)) {
  throw "PFX certificate file not found: $PfxPath"
}

$signtool = Resolve-SignTool

foreach ($artifact in $ArtifactPaths) {
  if (-not (Test-Path $artifact)) {
    throw "Artifact not found for signing: $artifact"
  }

  & $signtool sign /fd SHA256 /f $PfxPath /p $PfxPassword /tr $TimestampUrl /td SHA256 $artifact
  if ($LASTEXITCODE -ne 0) {
    throw "signtool sign failed for '$artifact' with exit code $LASTEXITCODE"
  }

  & $signtool verify /pa $artifact
  if ($LASTEXITCODE -ne 0) {
    throw "signtool verify failed for '$artifact' with exit code $LASTEXITCODE"
  }
}

Write-Host "Signing completed for $($ArtifactPaths.Count) artifact(s)."
