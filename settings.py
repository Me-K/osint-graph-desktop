"""Paths shared by the source and portable builds."""
import os
from pathlib import Path
import sys


# Resolve the writable application data directory, honoring an explicit environment override.
def data_directory() -> Path:
    override = os.environ.get("OSINT_GRAPH_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "OSINTGraph"


# Locate bundled resources in a portable build or beside the Python source files.
def resource_directory() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
