"""ORISUN IBUKUN – Owode Unit | Offline Cooperative Management System."""
import sys
import os
import traceback
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.schema import create_schema, get_setting
from database.connection import close_connection, get_connection


def validate_startup() -> bool:
    """Validate critical database tables exist after schema creation."""
    try:
        conn = get_connection()
        critical_tables = [
            "users", "roles", "members", "meetings", "attendance",
            "transactions", "savings", "shares", "loans", "loan_repayments",
            "expenses", "headquarters_remittances", "audit_logs", "backups", "settings"
        ]
        for table in critical_tables:
            cur = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            )
            if not cur.fetchone():
                print(f"WARNING: Critical table '{table}' not found")
                return False
        print("Startup validation: All critical tables present")
        return True
    except Exception as e:
        print(f"Startup validation failed: {e}")
        traceback.print_exc()
        return False


_INSTANCE_SOCKET = None

def ensure_single_instance(port: int = 47653):
    """Prevent multiple app instances (which can lock/corrupt migrations).

    Returns the bound socket (must be kept alive) or None if another
    instance is already running.
    """
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
    except OSError:
        return None
    global _INSTANCE_SOCKET
    _INSTANCE_SOCKET = s
    return s


def write_crash_log(text: str) -> str:
    """Append crash info to a log file in APPDATA. Returns the log path."""
    import datetime
    from pathlib import Path
    log_dir = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "OrisunIbukun"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "crash.log"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n===== {datetime.datetime.now().isoformat()} =====\n{text}\n")
        return str(log_path)
    except Exception:
        return ""


def show_error_and_exit(title: str, message: str) -> None:
    """Show error dialog and exit."""
    log_path = write_crash_log(f"{title}: {message}")
    if log_path:
        message += f"\n\nDetails saved to:\n{log_path}"
    try:
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        root.lift()
        root.focus_force()
        messagebox.showerror(title, message, parent=root)
        root.destroy()
    except Exception:
        print(f"{title}: {message}")
    sys.exit(1)


def main():
    try:
        if ensure_single_instance() is None:
            show_error_and_exit(
                "Already Running",
                "ORISUN IBUKUN is already running.\n\nPlease use the open window (check the taskbar) instead of starting a new one."
            )
        print("Creating/updating database schema...")
        create_schema()
        
        if not validate_startup():
            show_error_and_exit(
                "Database Error",
                "Database schema validation failed. Please check logs and restart."
            )
        
        print("Schema validation passed. Starting application...")
        
        from ui.login_form import LoginForm

        def on_login_success(user_id, username, role_name):
            from ui.main_form import MainForm
            app = MainForm(user_id, username, role_name)
            app.mainloop()

        login = LoginForm(on_success=on_login_success)
        login.mainloop()
        close_connection()
        
    except Exception as e:
        tb = traceback.format_exc()
        print(tb)
        write_crash_log(tb)
        show_error_and_exit(
            "Application Error",
            f"Failed to start application:\n\n{e}"
        )


if __name__ == "__main__":
    main()