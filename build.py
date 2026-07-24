"""
Build script for ocpp standalone executable using PyInstaller.

Usage:
    python build.py [--clean] [--nuitka]
    --clean: Remove existing build/dist directories before building.
    --nuitka: Use Nuitka instead of PyInstaller.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

def build_pyinstaller(clean: bool = False) -> None:
    """Build ocpp executable using PyInstaller."""
    if clean:
        for dirname in ["build", "dist"]:
            dirpath = Path(dirname)
            if dirpath.exists():
                print(f"Removing {dirpath}...")
                shutil.rmtree(dirpath)

    print("Building ocpp executable with PyInstaller...")
    result = subprocess.run(
        [
            sys.executable, 
            "-m", "PyInstaller",
            "--onefile",
            "--name", "ocpp",
            "--distpath", "dist",
            "--workpath", "build",
            "src/ocpp/__main__.py",
        ],
        check=False,
    )
    if result.returncode != 0:
        print("PyInstaller build failed.", file=sys.stderr)
        sys.exit(1)

    print("\nBuild successful!")
    print("Executable location:")
    print(f"  Windows: {Path('dist/ocpp.exe').resolve()}")
    print(f"  macOS/Linux: {Path('dist/ocpp').resolve()}")
    print("\nRun it with:")
    print("  Windows: .\\dist\\ocpp.exe")
    print("  macOS/Linux: ./dist/ocpp")

def build_nuitka(clean: bool = False) -> None:
    """Build ocpp executable using Nuitka."""
    if clean:
        for dirname in ["build", "dist"]:
            dirpath = Path(dirname)
            if dirpath.exists():
                print(f"Removing {dirpath}...")
                shutil.rmtree(dirpath)

    print("Building ocpp executable with Nuitka...")
    result = subprocess.run(
        [
            sys.executable, 
            "-m", "nuitka",
            "--onefile",
            "--output-dir=dist",
            "--output-filename=ocpp",
            "src/ocpp/__main__.py",
        ],
        check=False,
    )
    if result.returncode != 0:
        print("Nuitka build failed.", file=sys.stderr)
        sys.exit(1)

    print("\nBuild successful!")
    print("Executable location:")
    print(f"  Windows: {Path('dist/ocpp.exe').resolve()}")
    print(f"  macOS/Linux: {Path('dist/ocpp').resolve()}")
    print("\nRun it with:")
    print("  Windows: .\\dist\\ocpp.exe")
    print("  macOS/Linux: ./dist/ocpp")

def main() -> None:
    parser = argparse.ArgumentParser(description="Build ocpp standalone executable.")
    parser.add_argument("--clean", action="store_true", help="Clean build directories before building.")
    parser.add_argument("--nuitka", action="store_true", help="Use Nuitka instead of PyInstaller.")
    args = parser.parse_args()

    if args.nuitka:
        build_nuitka(clean=args.clean)
    else:
        build_pyinstaller(clean=args.clean)


if __name__ == "__main__":
    main()