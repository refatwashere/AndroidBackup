# Refat's Android Full Backup V1.0.1 — PyInstaller Build Spec
# ─────────────────────────────────────────────────────────────────────────────
# Build steps:
#   1. python build_icon.py          <- generates assets/Icon.ico
#   2. pyinstaller build.spec        <- produces dist/RefatAndroidBackup/RefatAndroidBackup.exe
# ─────────────────────────────────────────────────────────────────────────────

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

BASE = os.path.dirname(os.path.abspath(SPEC))
ctk_datas = collect_data_files("customtkinter")

TCL_SRC = os.path.join(BASE, "tcl_extracted", "_tcl_data")
TK_SRC  = os.path.join(BASE, "tcl_extracted", "_tk_data")
MTK_SRC = os.path.join(BASE, "mtkclient-2.1.4.1")

a = Analysis(
    [os.path.join(BASE, "gui.py")],
    pathex=[BASE, MTK_SRC],
    binaries=[],
    datas=[
        (os.path.join(BASE, "assets"),                 "assets"),
        (os.path.join(BASE, "requirements.txt"),       "."),
        (os.path.join(BASE, "refat_backup_engine.py"), "."),
        (MTK_SRC, "mtkclient-2.1.4.1"),
        (TCL_SRC, "_tcl_data"),
        (TK_SRC,  "_tk_data"),
    ] + ctk_datas,
    hiddenimports=[
        "customtkinter",
        "PIL",
        "PIL.Image",
        "PIL.ImageTk",
        "mtk",
        "refat_backup_engine",
    ] + collect_submodules("mtkclient"),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

# ── Executable ────────────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RefatAndroidBackup",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(BASE, "assets", "Icon.ico"),
    version_file=None,
)

# ── One-folder bundle ─────────────────────────────────────────────────────────
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RefatAndroidBackup",
)

# ── Post-build: copy python314.dll next to the exe and into _internal ─────────
import shutil
_dll_src = os.path.join("C:\\", "Python314", "python314.dll")
if os.path.exists(_dll_src):
    for _dst in [
        os.path.join(BASE, "dist", "RefatAndroidBackup", "python314.dll"),
        os.path.join(BASE, "dist", "RefatAndroidBackup", "_internal", "python314.dll"),
    ]:
        shutil.copy2(_dll_src, _dst)
        print(f"Copied python314.dll -> {_dst}")
