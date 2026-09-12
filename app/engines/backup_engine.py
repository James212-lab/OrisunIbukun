"""Backup and restore engine."""
import os
import shutil
import datetime
from pathlib import Path
from database.connection import get_connection, close_connection, DB_PATH, DB_DIR

BACKUP_DIR = DB_DIR / "backups"
BACKUP_RETENTION = 10


def _ensure_backup_dir() -> None:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def create_backup(notes: str = "", created_by: int | None = None,
                   backup_type: str = "Manual") -> str:
    _ensure_backup_dir()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    backup_name = f"backup_{ts}.db"
    backup_path = BACKUP_DIR / backup_name

    # VACUUM INTO fails if the target already exists; remove stale file
    if backup_path.exists():
        backup_path.unlink()

    conn = get_connection()
    conn.execute("VACUUM INTO ?", (str(backup_path),))

    file_size = backup_path.stat().st_size if backup_path.exists() else 0
    conn.execute(
        """INSERT INTO backups (backup_path, backup_type, file_size, notes, created_by)
           VALUES (?, ?, ?, ?, ?)""",
        (str(backup_path), backup_type, file_size, notes, created_by),
    )
    conn.commit()
    _enforce_retention()
    return str(backup_path)


def auto_backup() -> str | None:
    """Create an automatic backup on close. Returns the path or None on failure."""
    try:
        path = create_backup(notes="Auto-backup on close", backup_type="Automatic")
        return path
    except Exception:
        return None


def _enforce_retention() -> None:
    """Keep only the last BACKUP_RETENTION automatic backups."""
    if not BACKUP_DIR.exists():
        return
    conn = get_connection()
    rows = conn.execute(
        """SELECT backup_path FROM backups
           WHERE backup_type = 'Automatic'
           ORDER BY created_at DESC"""
    ).fetchall()
    if len(rows) <= BACKUP_RETENTION:
        return
    for row in rows[BACKUP_RETENTION:]:
        path = Path(row["backup_path"])
        if path.exists():
            path.unlink()
    conn.execute(
        """DELETE FROM backups
           WHERE backup_type = 'Automatic'
           AND id NOT IN (
               SELECT id FROM backups
               WHERE backup_type = 'Automatic'
               ORDER BY created_at DESC LIMIT ?
           )""",
        (BACKUP_RETENTION,),
    )
    conn.commit()


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

    # Close all connections before overwriting the DB file
    close_connection()

    shutil.copy2(src, DB_PATH)
