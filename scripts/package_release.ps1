param(
  [string]$Version = "1.0.0",
  [switch]$BuildInstaller
)

$ErrorActionPreference = "Stop"

Write-Host "Building cards DB asset..."
python scripts/build_cards_db.py

Write-Host "Running unit tests..."
python -m unittest discover -s tests -p "test_*.py" -v

Write-Host "Packaging one-folder build..."
python -m PyInstaller build/pyinstaller/arena_companion.spec --clean --noconfirm

if ($BuildInstaller) {
  $candidates = @(
    (Join-Path $env:USERPROFILE "AppData\\Local\\Programs\\InnoSetup\\ISCC.exe"),
    (Join-Path $env:USERPROFILE "AppData\\Local\\Programs\\Inno Setup 6\\ISCC.exe")
  )
  $isccPath = $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1

  if (-not $isccPath) {
    $isccCmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($isccCmd) {
      $isccPath = $isccCmd.Source
    }
  }

  if (-not $isccPath) {
    throw "ISCC.exe not found in standard user locations or PATH."
  }

  Write-Host "Building installer via Inno Setup..."
  & $isccPath "build\\installer\\arena_companion.iss"
}

Write-Host "Build completed for version $Version"
