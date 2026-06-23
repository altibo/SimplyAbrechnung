# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

import reportlab


reportlab_fonts = Path(reportlab.__file__).resolve().parent / "fonts"
app_icon_ico = Path("assets/icons/app_icon.ico").resolve()
app_icon_icns = Path("assets/icons/app_icon.icns").resolve()

a = Analysis(
    ["run_simply_abrechnung.py"],
    pathex=["src"],
    binaries=[],
    datas=[
        ("assets/icons/app_icon.png", "assets/icons"),
        (str(reportlab_fonts / "Vera.ttf"), "reportlab/fonts"),
        (str(reportlab_fonts / "VeraBd.ttf"), "reportlab/fonts"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

if sys.platform == "darwin":
    exe = EXE(
        pyz, a.scripts, [], exclude_binaries=True,
        name="SimplyAbrechnung", debug=False, bootloader_ignore_signals=False,
        strip=False, upx=True, console=False,
    )
    collected = COLLECT(
        exe, a.binaries, a.datas, strip=False, upx=True,
        name="SimplyAbrechnung",
    )
    app = BUNDLE(
        collected, name="SimplyAbrechnung.app", icon=str(app_icon_icns),
        bundle_identifier="de.altibo.simplyabrechnung",
    )
else:
    exe = EXE(
        pyz, a.scripts, a.binaries, a.datas, [],
        name="SimplyAbrechnung", debug=False, bootloader_ignore_signals=False,
        strip=False, upx=True, console=False, icon=str(app_icon_ico),
    )
