# PyInstaller spec for Arena Companion one-folder builds.

block_cipher = None


a = Analysis(
    ['src/arena_companion/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[('src/arena_companion/assets/cards.sqlite', 'arena_companion/assets')],
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
