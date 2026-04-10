# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['/Users/ltzz/Desktop/Python/txt-to-srt-converter/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
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
    [],
    exclude_binaries=True,
    name='txt_to_srt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['/Users/ltzz/Desktop/Python/txt-to-srt-converter/assets/icon/txt_to_srt.icns'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='txt_to_srt',
)
app = BUNDLE(
    coll,
    name='txt_to_srt.app',
    icon='/Users/ltzz/Desktop/Python/txt-to-srt-converter/assets/icon/txt_to_srt.icns',
    bundle_identifier='com.ltzz.txttosrt',
)
