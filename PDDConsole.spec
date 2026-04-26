# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules


project_dir = Path.cwd()

datas = []
for directory in ['templates', 'browsers', 'extensions']:
    path = project_dir / directory
    if path.exists():
        datas.append((str(path), directory))

for filename in ['app_config.example.json', 'README.md', 'DEPLOY.md', 'requirements.txt']:
    path = project_dir / filename
    if path.exists():
        datas.append((str(path), '.'))

datas += collect_data_files('DrissionPage')

hiddenimports = []
for package in ['DrissionPage', 'uvicorn']:
    hiddenimports += collect_submodules(package)

hiddenimports += [
    'multipart.multipart',
    'uvicorn.lifespan.on',
    'uvicorn.loops.auto',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets.auto',
]


a = Analysis(
    ['desktop_launcher.py'],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'unittest', 'tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PDDConsole',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
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
    upx=False,
    upx_exclude=[],
    name='PDDConsole',
)
