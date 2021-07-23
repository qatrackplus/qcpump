# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

pem_path = os.path.join(os.environ['LOCALAPPDATA'], '.certifi', 'cacert.pem')

data_files = [
    # add icons etc
    ("LICENSE", "."),
    ("README.md", "."),
    ("qcpump/resources/", "resources"),
    # add pumps
    ("qcpump/contrib/pumps/", "contrib/pumps"),
    (pem_path, ".certifi/cacert.pem"),
]

hidden_imports = [
    # core
    "qcpump.core.db",
    "qcpump.core.json",
    "qcpump.pumps.common.qatrack",

    # third party
    "certifi",
    "jinja2",
    "requests",
    "pypac",
    "certifi_win32",
    "win32",
    "fdb",
    "firebirdsql",
    "pyodbc",
    "wrapt",
]

a = Analysis(  # noqa: F821
    ['launch_qcpump.py'],
    pathex=['.'],
    binaries=[],
    datas=data_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=["patch_certs.py"],
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
