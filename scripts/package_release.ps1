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
  $isccPath = Join-Path $env:USERPROFILE "AppData\\Local\\Programs\\InnoSetup\\ISCC.exe"
  if (-not (Test-Path $isccPath)) {
    throw "ISCC.exe not found at '$isccPath'. Install Inno Setup or provide compiler in PATH."
  }

  Write-Host "Building installer via Inno Setup..."
  & $isccPath "build\\installer\\arena_companion.iss"
}

Write-Host "Build completed for version $Version"
