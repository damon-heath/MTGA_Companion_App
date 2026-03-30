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
        if (
          $assetNames -contains "checksums.txt" -and
          $assetNames -contains "ArenaCompanionSetup.exe" -and
          $assetNames -contains "ArenaCompanion-onefolder.zip"
        ) {
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

function Invoke-FirstRunValidation {
  param(
    [Parameter(Mandatory = $true)][string]$ExePath,
    [Parameter(Mandatory = $true)][string]$AppDataRoot,
    [Parameter(Mandatory = $true)][string]$OutputDir,
    [Parameter(Mandatory = $true)][string]$Prefix
  )

  $result = [ordered]@{
    executable_found = $false
    launch_exit_code = $null
    launch_ok = $false
    created_appdata = $false
    created_db = $false
    created_config = $false
    run_ok = $false
    output_path = $null
    paths_path = $null
  }

  if (-not (Test-Path -LiteralPath $ExePath -PathType Leaf)) {
    return $result
  }

  $result.executable_found = $true
  New-Item -ItemType Directory -Path $AppDataRoot -Force | Out-Null

  $outputPath = Join-Path $OutputDir "${Prefix}_first_run_output.txt"
  $pathsPath = Join-Path $OutputDir "${Prefix}_first_run_paths.txt"
  $result.output_path = $outputPath
  $result.paths_path = $pathsPath

  $exitCode = 1
  $previousAppData = $env:APPDATA
  try {
    $env:APPDATA = (Resolve-Path $AppDataRoot).Path
    & $ExePath --print-paths *>&1 | Set-Content -LiteralPath $outputPath -Encoding utf8
    $exitCode = $LASTEXITCODE
  }
  finally {
    $env:APPDATA = $previousAppData
  }

  $appRoot = Join-Path $AppDataRoot "ArenaCompanion"
  $dbPath = Join-Path $appRoot "arena_companion.db"
  $configPath = Join-Path $appRoot "config.json"

  $result.launch_exit_code = $exitCode
  $result.launch_ok = ($exitCode -eq 0)
  $result.created_appdata = Test-Path -LiteralPath $appRoot
  $result.created_db = Test-Path -LiteralPath $dbPath
  $result.created_config = Test-Path -LiteralPath $configPath
  $result.run_ok = $result.launch_ok -and $result.created_appdata -and $result.created_db -and $result.created_config

  @(
    "appdata_root=$appRoot"
    "db_path=$dbPath"
    "config_path=$configPath"
  ) | Set-Content -LiteralPath $pathsPath -Encoding utf8

  return $result
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

$oneFolderZipPath = Join-Path $outputDir "ArenaCompanion-onefolder.zip"
if (-not (Test-Path $oneFolderZipPath)) {
  throw "One-folder ZIP asset not found: $oneFolderZipPath"
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
$installerFirstRun = Invoke-FirstRunValidation `
  -ExePath $appExe `
  -AppDataRoot (Join-Path $outputDir "AppDataRoaming-installer") `
  -OutputDir $outputDir `
  -Prefix "installer"

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

$oneFolderExtractDir = Join-Path $outputDir "onefolder-extracted"
if (Test-Path -LiteralPath $oneFolderExtractDir) {
  Remove-Item -LiteralPath $oneFolderExtractDir -Recurse -Force
}

$oneFolderExtracted = $false
$oneFolderExtractionError = $null
try {
  Expand-Archive -LiteralPath $oneFolderZipPath -DestinationPath $oneFolderExtractDir -Force
  $oneFolderExtracted = $true
}
catch {
  $oneFolderExtractionError = $_.Exception.Message
}

$oneFolderExe = Join-Path $oneFolderExtractDir "ArenaCompanion.exe"
$oneFolderFirstRun = Invoke-FirstRunValidation `
  -ExePath $oneFolderExe `
  -AppDataRoot (Join-Path $outputDir "AppDataRoaming-onefolder") `
  -OutputDir $outputDir `
  -Prefix "onefolder"

$installerAllGood = $installOk -and $installerFirstRun.run_ok -and $uninstallOk -and $postUninstallRemovedBinary
$oneFolderAllGood = $oneFolderExtracted -and $oneFolderFirstRun.run_ok

$summary = [ordered]@{
  release = $safeTag
  release_url = $releasePayload.url
  checksums_verified = $checksumsVerified
  installer = [ordered]@{
    install_ok = $installOk
    uninstall_ok = $uninstallOk
    post_uninstall_removed_binary = $postUninstallRemovedBinary
    all_good = $installerAllGood
    first_run = $installerFirstRun
  }
  onefolder = [ordered]@{
    zip_path = $oneFolderZipPath
    extraction_ok = $oneFolderExtracted
    extraction_error = $oneFolderExtractionError
    executable_path = $oneFolderExe
    all_good = $oneFolderAllGood
    first_run = $oneFolderFirstRun
  }
  verified_assets = $verifiedAssets
  artifacts_dir = (Resolve-Path $outputDir).Path
}

$summaryPath = Join-Path $outputDir "smoke_summary.json"
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $summaryPath -Encoding utf8

$installerStatus = if ($installerAllGood) { "PASS" } else { "FAIL" }
$oneFolderStatus = if ($oneFolderAllGood) { "PASS" } else { "FAIL" }
$checksumStatus = if ($checksumsVerified) { "PASS" } else { "FAIL" }
if ($env:GITHUB_STEP_SUMMARY) {
  @"
### Post-Release Smoke
- release: $safeTag
- checksums: $checksumStatus
- installer path: $installerStatus
- one-folder path: $oneFolderStatus
- summary json: $summaryPath
"@ | Add-Content -LiteralPath $env:GITHUB_STEP_SUMMARY
}

$allGood = $checksumsVerified -and $installerAllGood -and $oneFolderAllGood
if (-not $allGood) {
  Write-Host "Post-release smoke validation FAILED."
  $summary | ConvertTo-Json -Depth 6 | Write-Host
  exit 1
}

Write-Host "Post-release smoke validation passed."
Write-Host "Artifacts: $outputDir"
