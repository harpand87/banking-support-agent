# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path


PROJECT_ROOT = Path(SPECPATH).resolve().parent

a = Analysis(
    [str(PROJECT_ROOT / "app" / "standalone.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[(str(PROJECT_ROOT / "data"), "data")],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="BankingSupportEvaluation",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
