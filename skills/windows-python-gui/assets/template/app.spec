# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec ファイル
# 使い方: pyinstaller app.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # データファイルを追加する場合:
        # ('src_path', 'dest_dir'),
        # 例: ('assets/', 'assets/'),
    ],
    hiddenimports=[
        # 自動検出されないモジュールを追加:
        # 例: 'PIL._tkinter_finder',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',           # 出力exeのファイル名
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,               # GUIアプリはFalse（コンソールウィンドウを非表示）
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                   # アイコン: 'assets/icon.ico'
)
