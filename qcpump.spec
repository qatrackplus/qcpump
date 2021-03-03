# -*- mode: python ; coding: utf-8 -*-
import glob
from pathlib import Path

block_cipher = None

data_files = [
    # add icons etc
    ("LICENSE", "."),
    ("README.md", "."),
    ("qcpumpui/resources/", "resources"),
    # add pumps
    ("qcpumpui/contrib/pumps/", "contrib/pumps"),
]

hidden_imports = [
    # core
    "qcpumpui.core.db",
    "qcpumpui.core.json",

    # third party
    "jinja2",
    "requests",
    "fdb",
    "firebirdsql",
    "pyodbc",
]

a = Analysis(  # noqa: F821
    ['qcpump.py'],
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
    icon="qcpumpui/resources/img/qcpump.ico",
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
    icon="qcpumpui/resources/img/qcpump.ico",
)
