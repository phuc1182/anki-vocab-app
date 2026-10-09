# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

project_root = Path(SPECPATH)

datas, binaries, hiddenimports = collect_all("edge_tts")
datas += [(str(project_root / "src" / "anki_vocab_app" / "data"), "anki_vocab_app/data")]
hiddenimports += collect_submodules("genanki")
hiddenimports += collect_submodules("anki_vocab_app")
hiddenimports += ["aiohttp", "mdict_utils"]

a = Analysis(
    [str(project_root / "scripts" / "run_app.py")],
    pathex=[str(project_root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="AnkiVocabApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
