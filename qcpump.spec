# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

data_files = [
    # add icons etc
    ("LICENSE", "."),
    ("README.md", "."),
    ("qcpump/resources/", "resources"),
    # add pumps
    ("qcpump/contrib/pumps/", "contrib/pumps"),
]

hidden_imports = [
    # core
    "qcpump.core.db",
    "qcpump.core.json",
    "qcpump.pumps.common.qatrack",

    # third party
    "jinja2",
    "requests",
    "PyPAC",
    "python-certifi-win32",
    "fdb",
    "firebirdsql",
    "pyodbc",
]

a = Analysis(  # noqa: F821
    ['launch_qcpump.py'],
    pathex=['.'],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)  # noqa: F821
exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='qcpump',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # don't show a console window
    icon="qcpump/resources/img/qcpump.ico",
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='qcpump',
    icon="qcpump/resources/img/qcpump.ico",
)
