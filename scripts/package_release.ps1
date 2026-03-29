param(
  [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"

Write-Host "Building cards DB asset..."
python scripts/build_cards_db.py

Write-Host "Running unit tests..."
python -m unittest discover -s tests -p "test_*.py" -v

Write-Host "Packaging one-folder build..."
pyinstaller build/pyinstaller/arena_companion.spec --clean --noconfirm

Write-Host "Build completed for version $Version"
