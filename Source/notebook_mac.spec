# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['notebook.py'],
    pathex=[],
    binaries=[],
    datas=[('splash.png', '.'),
       ('icon.ico', '.'),
       ('help', 'help')],
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
    name='EPL ABR Analysis',
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
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EPL ABR Analysis',
)
app = BUNDLE(
    coll,
    name='EPL ABR Analysis.app',
    icon='icon.ico',
    bundle_identifier=None,
)
