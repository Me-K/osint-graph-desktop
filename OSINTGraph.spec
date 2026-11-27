# PyInstaller detects Qt WebEngine's helper process, resources and DLLs through its hooks.
from pathlib import Path

root = Path(SPECPATH)
a = Analysis(
    [str(root / 'main.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / 'web'), 'web'), (str(root / 'licenses'), 'licenses'),
           (str(root / 'README.md'), '.'), (str(root / 'THIRD_PARTY.md'), '.'),
           (str(root / 'LICENSE'), '.')],
    hiddenimports=['backend', 'sqlite3'],
    hookspath=[],
    excludes=['tkinter', 'PyQt5', 'PyQt6', 'PySide2', 'uvicorn', 'neo4j'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='OSINTGraph',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='OSINTGraph')
