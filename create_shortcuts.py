"""
create_shortcuts.py - Sets up click-to-run launchers that bypass Windows Smart App Control.

Smart App Control blocks unsigned compiled .exe binaries on Windows 11.
This script creates:
1. 'Launch GPT Wrapped.vbs' in the workspace folder (double-click to run with NO console window).
2. 'Launch GPT Wrapped.bat' fallback.
3. A Windows Desktop Shortcut 'GPT Wrapped.lnk' on the user's Desktop.
"""

import os
from pathlib import Path
import subprocess
import sys

workspace_dir = Path(__file__).parent.resolve()
gui_py = workspace_dir / "gui.py"
pythonw_path = Path(sys.executable).parent / "pythonw.exe"
if not pythonw_path.exists():
    pythonw_path = Path(sys.executable)

# 1. Create Launch GPT Wrapped.vbs (completely silent windowed launch)
vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "{workspace_dir}"
WshShell.Run """{pythonw_path}"" ""{gui_py}""", 0, False
'''

vbs_file = workspace_dir / "Launch GPT Wrapped.vbs"
with open(vbs_file, "w", encoding="utf-8") as f:
    f.write(vbs_content)
print(f"Created VBS launcher: {vbs_file.name}")

# 2. Create Launch GPT Wrapped.bat
bat_content = f'''@echo off
cd /d "{workspace_dir}"
start "" "{pythonw_path}" "{gui_py}"
exit
'''

bat_file = workspace_dir / "Launch GPT Wrapped.bat"
with open(bat_file, "w", encoding="utf-8") as f:
    f.write(bat_content)
print(f"Created BAT launcher: {bat_file.name}")

# 3. Create Windows Shortcut (.lnk) on Desktop
desktop_dir = Path.home() / "Desktop"
if not desktop_dir.exists():
    # Check OneDrive Desktop
    one_drive_desktop = Path.home() / "OneDrive" / "Desktop"
    if one_drive_desktop.exists():
        desktop_dir = one_drive_desktop

try:
    ps_cmd = (
        f'$ws = New-Object -ComObject WScript.Shell; '
        f'$s = $ws.CreateShortcut("{desktop_dir}\\GPT Wrapped.lnk"); '
        f'$s.TargetPath = "{pythonw_path}"; '
        f'$s.Arguments = "`"{gui_py}`""; '
        f'$s.WorkingDirectory = "{workspace_dir}"; '
        f'$s.Description = "GPT Wrapped - ChatGPT Recap"; '
        f'$s.Save()'
    )
    subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=True)
    print(f"Created Desktop Shortcut: {desktop_dir}\\GPT Wrapped.lnk")
except Exception as e:
    print(f"Could not create Desktop shortcut automatically: {e}")

print("\nSetup complete! You can now launch GPT Wrapped without Smart App Control blocks.")
