param(
  [Parameter(Mandatory = $true)][string]$ReleaseTag,
  [Parameter(Mandatory = $true)][string]$Repo,
  [string]$OutputRoot = "artifacts/postrelease-ci"
)

$ErrorActionPreference = "Stop"

function Wait-ReleaseAssets {
  param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][string]$RepoName,
    [int]$MaxAttempts = 24,
    [int]$SleepSeconds = 10
  )

  for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
    try {
      $payload = gh release view $Tag --repo $RepoName --json assets,url,tagName | ConvertFrom-Json
      if ($payload -and $payload.assets) {
        $assetNames = @($payload.assets | ForEach-Object { $_.name })
        if ($assetNames -contains "checksums.txt" -and $assetNames -contains "ArenaCompanionSetup.exe") {
          return $payload
        }
      }
    }
    catch {
      # Release may not exist yet for freshly pushed tags.
    }

    if ($attempt -lt $MaxAttempts) {
      Start-Sleep -Seconds $SleepSeconds
    }
  }

  throw "Timed out waiting for release assets for tag '$Tag' in repo '$RepoName'."
}

$safeTag = $ReleaseTag.Trim()
if (-not $safeTag.StartsWith("v")) {
  $safeTag = "v$safeTag"
}

$outputDir = Join-Path $OutputRoot $safeTag
if (Test-Path $outputDir) {
  Remove-Item -LiteralPath $outputDir -Recurse -Force
}
New-Item -ItemType Directory -Path $outputDir -Force | Out-Null

$releasePayload = Wait-ReleaseAssets -Tag $safeTag -RepoName $Repo
gh release download $safeTag --repo $Repo --dir $outputDir --clobber

$checksumsPath = Join-Path $outputDir "checksums.txt"
if (-not (Test-Path $checksumsPath)) {
  throw "checksums.txt not found after release download."
}

$checksumsVerified = $true
$verifiedAssets = @()
foreach ($line in Get-Content -LiteralPath $checksumsPath) {
  if ([string]::IsNullOrWhiteSpace($line)) {
    continue
  }

  if ($line -notmatch '^(?<hash>[A-Fa-f0-9]{64})\s+(?<name>.+)$') {
    throw "Invalid checksum line format: $line"
  }

  $expected = $Matches.hash.ToLower()
  $name = $Matches.name.Trim()
  $assetPath = Join-Path $outputDir $name
  if (-not (Test-Path $assetPath)) {
    throw "Missing artifact referenced by checksums.txt: $name"
  }

  $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $assetPath).Hash.ToLower()
  if ($actual -ne $expected) {
    $checksumsVerified = $false
    throw "Checksum mismatch for '$name'. expected=$expected actual=$actual"
  }

  $verifiedAssets += [ordered]@{
    name = $name
    sha256 = $actual
  }
}

$installerPath = Join-Path $outputDir "ArenaCompanionSetup.exe"
if (-not (Test-Path $installerPath)) {
  throw "Installer asset not found: $installerPath"
}

$installRoot = Join-Path $outputDir "install-root"
New-Item -ItemType Directory -Path $installRoot -Force | Out-Null

$installLog = Join-Path $outputDir "install.log"
$installArgs = @(
  "/VERYSILENT",
  "/SUPPRESSMSGBOXES",
  "/NORESTART",
  "/SP-",
  "/LOG=$installLog",
  "/DIR=$installRoot"
)
$installProc = Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -PassThru
$installOk = ($installProc.ExitCode -eq 0)

$appExe = Join-Path $installRoot "ArenaCompanion.exe"
$appDataRoot = Join-Path $outputDir "AppDataRoaming"
New-Item -ItemType Directory -Path $appDataRoot -Force | Out-Null

$firstRunOutputPath = Join-Path $outputDir "first_run_output.txt"
$firstRunPathsPath = Join-Path $outputDir "first_run_paths.txt"
$firstRunAppData = $false
$firstRunDb = $false
$firstRunConfig = $false
if (Test-Path $appExe) {
  $previousAppData = $env:APPDATA
  $env:APPDATA = (Resolve-Path $appDataRoot).Path
  & $appExe --print-paths *>&1 | Set-Content -LiteralPath $firstRunOutputPath -Encoding utf8
  $env:APPDATA = $previousAppData

  $appRoot = Join-Path $appDataRoot "ArenaCompanion"
  $dbPath = Join-Path $appRoot "arena_companion.db"
  $configPath = Join-Path $appRoot "config.json"
  $firstRunAppData = Test-Path $appRoot
  $firstRunDb = Test-Path $dbPath
  $firstRunConfig = Test-Path $configPath

  @(
    "appdata_root=$appRoot"
    "db_path=$dbPath"
    "config_path=$configPath"
  ) | Set-Content -LiteralPath $firstRunPathsPath -Encoding utf8
}

$uninstallExe = Join-Path $installRoot "unins000.exe"
$uninstallOk = $false
if (Test-Path $uninstallExe) {
  $uninstallArgs = @(
    "/VERYSILENT",
    "/SUPPRESSMSGBOXES",
    "/NORESTART"
  )
  $uninstallProc = Start-Process -FilePath $uninstallExe -ArgumentList $uninstallArgs -Wait -PassThru
  $uninstallOk = ($uninstallProc.ExitCode -eq 0)
}

$postUninstallRemovedBinary = -not (Test-Path $appExe)

$summary = [ordered]@{
  release = $safeTag
  release_url = $releasePayload.url
  checksums_verified = $checksumsVerified
  install_ok = $installOk
  uninstall_ok = $uninstallOk
  post_uninstall_removed_binary = $postUninstallRemovedBinary
  first_run_created_appdata = $firstRunAppData
  first_run_created_db = $firstRunDb
  first_run_created_config = $firstRunConfig
  verified_assets = $verifiedAssets
  artifacts_dir = (Resolve-Path $outputDir).Path
}

$summaryPath = Join-Path $outputDir "smoke_summary.json"
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $summaryPath -Encoding utf8

$allGood = $checksumsVerified -and $installOk -and $uninstallOk -and $postUninstallRemovedBinary -and $firstRunAppData -and $firstRunDb -and $firstRunConfig
if (-not $allGood) {
  Write-Host "Post-release smoke validation FAILED."
  $summary | ConvertTo-Json -Depth 6 | Write-Host
  exit 1
}

Write-Host "Post-release smoke validation passed."
Write-Host "Artifacts: $outputDir"
