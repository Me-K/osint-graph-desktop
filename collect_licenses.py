"""Collect installed dependency notices into the portable distribution."""
from importlib.metadata import distribution
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parent
target = root / "licenses"
packages = ["PySide6", "PySide6_Addons", "PySide6_Essentials", "shiboken6", "fastapi", "starlette",
            "pydantic", "pydantic_core", "httpx", "httpcore", "h11", "anyio", "idna", "certifi",
            "annotated-doc", "annotated-types", "typing-extensions", "typing-inspection"]
versions = []
for name in packages:
    dist = distribution(name)
    versions.append(f"{dist.metadata['Name']}=={dist.version}")
    for entry in dist.files or []:
        if any(word in entry.name.lower() for word in ("license", "copying", "notice")):
            source = Path(dist.locate_file(entry))
            if source.is_file():
                destination = target / name / entry.name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
for name in ["react", "react-dom", "scheduler", "cytoscape"]:
    package = root / "ui/node_modules" / name
    for source in package.iterdir():
        if (source.is_file() and source.suffix.lower() not in {".js", ".mjs"}
                and any(word in source.name.lower() for word in ("license", "copying", "notice"))):
            destination = target / name / source.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
target.mkdir(parents=True, exist_ok=True)
python_license = Path(sys.base_prefix) / "LICENSE.txt"
if python_license.is_file():
    shutil.copyfile(python_license, target / "Python-LICENSE.txt")
(target / "versions.txt").write_text("\n".join(versions) + "\n", encoding="utf-8")
