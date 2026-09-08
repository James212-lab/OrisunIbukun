"""Backup and restore engine."""
import os
import shutil
import datetime
from pathlib import Path
from database.connection import get_connection, DB_PATH, DB_DIR

BACKUP_DIR = DB_DIR / "backups"


def _ensure_backup_dir() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def create_backup(notes: str = "", created_by: int | None = None) -> str:
    _ensure_backup_dir()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{ts}.db"
    backup_path = BACKUP_DIR / backup_name
    conn = get_connection()
    conn.execute("VACUUM INTO ?", (str(backup_path),))

    file_size = backup_path.stat().st_size if backup_path.exists() else 0
    conn.execute(
        """INSERT INTO backups (backup_path, backup_type, file_size, notes, created_by)
           VALUES (?, 'Manual', ?, ?, ?)""",
        (str(backup_path), file_size, notes, created_by),
    )
    conn.commit()
    return str(backup_path)


def list_backups() -> list[dict]:
    conn = get_connection()
    cur = conn.execute(
        "SELECT * FROM backups ORDER BY created_at DESC LIMIT 20"
    )
    return [dict(row) for row in cur.fetchall()]


def restore_backup(backup_path: str) -> None:
    src = Path(backup_path)
    if not src.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")

    safety_name = f"pre_restore_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    safety_path = DB_DIR / safety_name
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, safety_path)

    shutil.copy2(src, DB_PATH)
