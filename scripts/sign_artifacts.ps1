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

  $kitRoot = "C:\\Program Files (x86)\\Windows Kits\\10\\bin"
  if (-not (Test-Path $kitRoot)) {
    throw "signtool.exe not found and Windows Kits path '$kitRoot' is missing."
  }

  $matches = Get-ChildItem -Path $kitRoot -Recurse -Filter signtool.exe -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -like "*\\x64\\signtool.exe" } |
    Sort-Object FullName -Descending

  if (-not $matches) {
    throw "Unable to locate signtool.exe under '$kitRoot'."
  }

  return $matches[0].FullName
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
