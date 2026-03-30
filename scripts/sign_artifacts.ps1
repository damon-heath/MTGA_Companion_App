param(
  [Parameter(Mandatory = $true)]
  [string[]]$ArtifactPaths,
  [Parameter(Mandatory = $true)]
  [string]$PfxPath,
  [Parameter(Mandatory = $true)]
  [string]$PfxPassword,
  [string]$TimestampUrl = "https://timestamp.digicert.com"
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

function Resolve-TimestampArguments {
  param(
    [Parameter(Mandatory = $true)]
    [string]$SignToolPath,
    [Parameter(Mandatory = $true)]
    [string]$Url
  )

  $help = & $SignToolPath sign /? 2>&1 | Out-String
  if ($help -match '(?i)\s/tr\s') {
    return @("/tr", $Url, "/td", "SHA256")
  }
  return @("/t", $Url)
}

if (-not (Test-Path $PfxPath)) {
  throw "PFX certificate file not found: $PfxPath"
}

$signtool = Resolve-SignTool
$timestampArgs = Resolve-TimestampArguments -SignToolPath $signtool -Url $TimestampUrl

foreach ($artifact in $ArtifactPaths) {
  if (-not (Test-Path $artifact)) {
    throw "Artifact not found for signing: $artifact"
  }

  & $signtool sign /fd SHA256 /f $PfxPath /p $PfxPassword @timestampArgs $artifact
  if ($LASTEXITCODE -ne 0) {
    throw "signtool sign failed for '$artifact' with exit code $LASTEXITCODE"
  }

  & $signtool verify /pa $artifact
  if ($LASTEXITCODE -ne 0) {
    throw "signtool verify failed for '$artifact' with exit code $LASTEXITCODE"
  }
}

Write-Host "Signing completed for $($ArtifactPaths.Count) artifact(s)."
