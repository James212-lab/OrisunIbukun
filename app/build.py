"""Build script for ORISUN IBUKUN - Owode Unit."""
import subprocess
import sys
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(APP_DIR, "main.py")
ICON = os.path.join(APP_DIR, "assets", "icon.ico")
RUNTIME_HOOK = os.path.join(APP_DIR, "runtime_hook.py")

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--noconfirm",
    "--onefile",
    "--windowed",
    "--name", "OrisunIbukun",
    "--runtime-hook", RUNTIME_HOOK,
    "--add-data", f"{os.path.join(APP_DIR, 'database')};database",
    "--add-data", f"{os.path.join(APP_DIR, 'engines')};engines",
    "--add-data", f"{os.path.join(APP_DIR, 'models')};models",
    "--add-data", f"{os.path.join(APP_DIR, 'ui')};ui",
    "--add-data", f"{os.path.join(APP_DIR, 'utils')};utils",
    "--add-data", f"{os.path.join(APP_DIR, 'assets')};assets",
    "--hidden-import", "database",
    "--hidden-import", "database.connection",
    "--hidden-import", "database.schema",
    "--hidden-import", "database.migrations",
    "--hidden-import", "engines",
    "--hidden-import", "engines.transaction_engine",
    "--hidden-import", "engines.backup_engine",
    "--hidden-import", "models",
    "--hidden-import", "ui",
    "--hidden-import", "ui.login_form",
    "--hidden-import", "ui.main_form",
    "--hidden-import", "ui.member_form",
    "--hidden-import", "ui.savings_form",
    "--hidden-import", "ui.loan_form",
    "--hidden-import", "ui.attendance_form",
    "--hidden-import", "ui.report_form",
    "--hidden-import", "ui.backup_form",
    "--hidden-import", "ui.settings_form",
    "--hidden-import", "utils",
    "--hidden-import", "utils.helpers",
    "--hidden-import", "utils.validators",
    "--hidden-import", "utils.date_picker",
    "--hidden-import", "PIL",
    "--hidden-import", "PIL.Image",
    "--hidden-import", "PIL.ImageTk",
    "--hidden-import", "errors",
    "--hidden-import", "session",
    "--hidden-import", "constants",
    "--clean",
]

if os.path.exists(ICON):
    cmd.extend(["--icon", ICON])

cmd.append(MAIN)

print("Building ORISUN IBUKUN executable...")
print(f"Command: {' '.join(cmd)}")
result = subprocess.run(cmd, cwd=APP_DIR)

if result.returncode == 0:
    exe_path = os.path.join(APP_DIR, "dist", "OrisunIbukun.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"\nBuild successful!")
        print(f"Executable: {exe_path}")
        print(f"Size: {size_mb:.1f} MB")
    else:
        print("\nBuild completed but exe not found at expected path.")
else:
    print(f"\nBuild failed with return code {result.returncode}")
