"""
build_exe.py - Automated PyInstaller packaging script for GPT Wrapped.

Compiles the desktop GUI application into a standalone Windows executable
(GPTWrapped.exe) with all CustomTkinter assets bundled.
"""

from pathlib import Path
import subprocess
import sys

# Reconfigure encoding
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def build():
    print("🔨 Starting build process for GPT Wrapped Standalone EXE...")

    root_dir = Path(__file__).parent.resolve()
    gui_script = root_dir / "gui.py"

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name", "GPTWrapped",
        "--collect-all", "customtkinter",
        "--clean",
        str(gui_script)
    ]

    print(f"Running command:\n{' '.join(cmd)}\n")
    res = subprocess.run(cmd, cwd=str(root_dir))

    if res.returncode == 0:
        exe_path = root_dir / "dist" / "GPTWrapped.exe"
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print("\n" + "=" * 60)
            print("  🎉 BUILD SUCCESSFUL!")
            print("=" * 60)
            print(f"Executable created: {exe_path}")
            print(f"File Size:          {size_mb:.1f} MB")
            print("You can now double-click GPTWrapped.exe to run the application!\n")
            return True

    print("❌ Build failed with return code:", res.returncode)
    return False


if __name__ == "__main__":
    success = build()
    sys.exit(0 if success else 1)
