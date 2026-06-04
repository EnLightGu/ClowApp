# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.ico', '.'), ('MainWindow.ui', '.'), ('Widgets/Sidebars/Topbar.ui', 'Widgets/Sidebars'), ('Widgets/Sidebars/LeftSidebar.ui', 'Widgets/Sidebars'), ('Widgets/Sidebars/RightSidebar.ui', 'Widgets/Sidebars'), ('Widgets/LeftWidget/FileManage.ui', 'Widgets/LeftWidget'), ('Widgets/Sidebars/icon1.ico', 'Widgets/Sidebars'), ('Widgets/Sidebars/icon2.ico', 'Widgets/Sidebars'), ('Widgets/Sidebars/icon3.ico', 'Widgets/Sidebars'), ('Widgets/Sidebars/icon4.ico', 'Widgets/Sidebars')],
    hiddenimports=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.uic', 'ctypes', 'ctypes.wintypes', 'platform', 'os', 'sys'],
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
    name='MainApp',
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
    icon=['icon.ico'],
)
