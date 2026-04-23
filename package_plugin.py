import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
PLUGIN_ID = ROOT.name
DIST_DIR = ROOT / "dist"
PLUGIN_JSON = ROOT / "plugin.json"
INCLUDED_FILES = {
    "plugin.json",
    "__init__.py",
    "SpoolmanClient.py",
    "MaterialWriter.py",
    "SpoolmanMaterialExtension.py",
    "README.md",
    "LICENSE",
}
EXCLUDES = {
    ".git",
    ".github",
    ".pytest_cache",
    "__pycache__",
    "dist",
}
EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
}


def read_version() -> str:
    plugin_metadata = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    version = plugin_metadata.get("version")
    if not isinstance(version, str) or not version.strip():
        raise RuntimeError("plugin.json is missing a valid string version")
    return version.strip()


def iter_package_files():
    for path in ROOT.rglob("*"):
        relative_path = path.relative_to(ROOT)
        parts = set(relative_path.parts)
        if parts & EXCLUDES:
            continue
        if path.is_dir():
            continue
        if path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        if relative_path.as_posix() not in INCLUDED_FILES:
            continue
        yield path, relative_path


def build_archive() -> Path:
    version = read_version()
    DIST_DIR.mkdir(exist_ok=True)
    archive_path = DIST_DIR / f"{PLUGIN_ID}-{version}.zip"
    if archive_path.exists():
        archive_path.unlink()

    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for source_path, relative_path in sorted(iter_package_files(), key=lambda item: item[1].as_posix()):
            archive_name = Path(PLUGIN_ID) / relative_path
            archive.write(source_path, archive_name.as_posix())

    return archive_path


def clean_dist() -> None:
    if DIST_DIR.exists():
        shutil.rmtree(DIST_DIR)


if __name__ == "__main__":
    archive_path = build_archive()
    print(archive_path)
