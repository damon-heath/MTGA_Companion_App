# PyInstaller spec for Arena Companion one-folder builds.

block_cipher = None

from pathlib import Path


PROJECT_ROOT = Path(SPECPATH).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
MAIN_SCRIPT = SRC_ROOT / "arena_companion" / "main.py"
CARDS_DB = SRC_ROOT / "arena_companion" / "assets" / "cards.sqlite"


a = Analysis(
    [str(MAIN_SCRIPT)],
    pathex=[str(SRC_ROOT)],
    binaries=[],
    datas=[(str(CARDS_DB), 'arena_companion/assets')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ArenaCompanion',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ArenaCompanion',
)
