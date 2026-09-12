"""Database migration system for ORISUN IBUKUN."""
import sqlite3
from database.connection import get_connection
from database.schema import SCHEMA_VERSION


MIGRATIONS = {
    1: """
        -- Initial schema (already in schema.py)
    """,
    2: """
        -- Add indexes for better query performance
        -- (applied by _ensure_indexes: skipped when tables/columns are absent)
        CREATE INDEX IF NOT EXISTS idx_transactions_member_date
        ON transactions(member_id, date);
        CREATE INDEX IF NOT EXISTS idx_transactions_type_date
        ON transactions(transaction_type, date);
        CREATE INDEX IF NOT EXISTS idx_savings_member_created
        ON savings(member_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_loans_member_status
        ON loans(member_id, status);
        CREATE INDEX IF NOT EXISTS idx_attendance_meeting_member
        ON attendance(meeting_id, member_id);
    """,

    3: """
        -- Add PIN change tracking
        ALTER TABLE users ADD COLUMN pin_changed_at TEXT;
        ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0;
        ALTER TABLE users ADD COLUMN locked_until TEXT;
    """,
    4: """
        -- Add audit log improvements
        ALTER TABLE audit_logs ADD COLUMN table_name TEXT;
        ALTER TABLE audit_logs ADD COLUMN record_id TEXT;
        ALTER TABLE audit_logs ADD COLUMN old_values TEXT;
        ALTER TABLE audit_logs ADD COLUMN new_values TEXT;
    """,
    5: """
        -- Add meeting minutes table
        CREATE TABLE IF NOT EXISTS meeting_minutes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            meeting_id INTEGER NOT NULL REFERENCES meetings(id),
            agenda TEXT,
            decisions TEXT,
            action_items TEXT,
            created_by INTEGER REFERENCES users(id),
            created_at TEXT DEFAULT (datetime('now'))
        );
    """,
    8: """
        -- Physical loan document vault
        CREATE TABLE IF NOT EXISTS loan_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL REFERENCES loans(id),
            member_id INTEGER NOT NULL REFERENCES members(id),
            doc_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            uploaded_at TEXT DEFAULT (datetime('now')),
            uploaded_by INTEGER REFERENCES users(id)
        );
    """,
    7: """
        -- Member charges: absence fines, minutes levies, other tagged charges
        CREATE TABLE IF NOT EXISTS member_charges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            charge_id TEXT NOT NULL UNIQUE,
            member_id INTEGER NOT NULL REFERENCES members(id),
            meeting_id INTEGER REFERENCES meetings(id),
            charge_type TEXT NOT NULL,
            description TEXT,
            amount REAL NOT NULL DEFAULT 0,
            amount_paid REAL DEFAULT 0,
            status TEXT DEFAULT 'Owed',
            created_by INTEGER REFERENCES users(id),
            created_at TEXT DEFAULT (datetime('now'))
        );
    """,
    6: """
        -- KYC personal details + photograph for members
        ALTER TABLE members ADD COLUMN dob TEXT;
        ALTER TABLE members ADD COLUMN gender TEXT;
        ALTER TABLE members ADD COLUMN occupation TEXT;
        ALTER TABLE members ADD COLUMN email TEXT;
        ALTER TABLE members ADD COLUMN next_of_kin TEXT;
        ALTER TABLE members ADD COLUMN next_of_kin_phone TEXT;
        ALTER TABLE members ADD COLUMN id_type TEXT;
        ALTER TABLE members ADD COLUMN id_number TEXT;
        ALTER TABLE members ADD COLUMN photo_path TEXT;
    """,
    9: """
        -- Absentism fines audit log
        CREATE TABLE IF NOT EXISTS absentism_fines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id INTEGER NOT NULL REFERENCES members(id),
            meeting_id INTEGER NOT NULL REFERENCES meetings(id),
            amount REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Owed',
            amount_paid REAL NOT NULL DEFAULT 0,
            entered_by INTEGER REFERENCES users(id),
            created_at TEXT DEFAULT (datetime('now'))
        );
    """,
    10: """
        -- External guarantors + charge payment audit trail
        CREATE TABLE IF NOT EXISTS external_guarantors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_id INTEGER NOT NULL REFERENCES loans(id),
            full_name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            id_type TEXT,
            id_number TEXT,
            photo_path TEXT,
            relationship TEXT,
            guarantee_amount REAL DEFAULT 0,
            date_guaranteed TEXT DEFAULT (datetime('now')),
            status TEXT DEFAULT 'Active'
        );
        CREATE TABLE IF NOT EXISTS charge_payment_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            txn_id TEXT NOT NULL,
            charge_id TEXT NOT NULL,
            amount_applied REAL NOT NULL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """,
}


def get_current_schema_version() -> int:
    """Get the current schema version from the database."""
    conn = get_connection()
    try:
        cur = conn.execute("SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return row["version"]
    except sqlite3.OperationalError:
        pass
    return 0


def _table_columns(conn, table: str) -> set:
    try:
        return {r[1] for r in conn.execute(f"PRAGMA table_info([{table}])").fetchall()}
    except sqlite3.Error:
        return set()


def _ensure_indexes(conn) -> None:
    """Create performance indexes, skipping any whose table/columns are absent."""
    wanted = [
        ("idx_transactions_member_date", "transactions", ["member_id", "date"]),
        ("idx_transactions_type_date", "transactions", ["transaction_type", "date"]),
        ("idx_savings_member_created", "savings", ["member_id", "created_at"]),
        ("idx_loans_member_status", "loans", ["member_id", "status"]),
        ("idx_attendance_meeting_member", "attendance", ["meeting_id", "member_id"]),
    ]
    for idx_name, table, cols in wanted:
        if not all(c in _table_columns(conn, table) for c in cols):
            print(f"Skipping index {idx_name}: column(s) missing in {table}")
            continue
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS {idx_name} ON [{table}] ({', '.join(cols)})"
        )


def run_migrations() -> None:
    """Run all pending migrations."""
    current_version = get_current_schema_version()
    target_version = SCHEMA_VERSION
    
    if current_version >= target_version:
        return
    
    import time as _t
    conn = get_connection()
    for version in range(current_version + 1, target_version + 1):
        if version == 2:
            # Index-only migration: apply safely, record version regardless
            for attempt in range(5):
                try:
                    _ensure_indexes(conn)
                    conn.execute(
                        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, datetime('now'))",
                        (version,)
                    )
                    conn.commit()
                    print(f"Applied migration v{version}")
                    break
                except sqlite3.Error as e:
                    conn.rollback()
                    if "locked" in str(e).lower() and attempt < 4:
                        _t.sleep(1.5)
                        continue
                    raise RuntimeError(f"Migration v{version} failed: {e}")
            continue
        if version in MIGRATIONS:
            migration_sql = MIGRATIONS[version]
            for attempt in range(5):
                try:
                    # Run statement-by-statement so idempotent migrations
                    # (e.g. ADD COLUMN on fresh DBs) don't abort the whole version
                    for stmt in [s.strip() for s in migration_sql.split(";")]:
                        if not stmt or stmt.startswith("--"):
                            # strip comment-only chunks
                            lines = [l for l in stmt.splitlines() if not l.strip().startswith("--") and l.strip()]
                            if not lines:
                                continue
                            stmt = "\n".join(lines)
                        try:
                            conn.execute(stmt)
                        except sqlite3.OperationalError as oe:
                            if "duplicate column name" in str(oe).lower():
                                continue
                            raise
                    conn.execute(
                        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, datetime('now'))",
                        (version,)
                    )
                    conn.commit()
                    print(f"Applied migration v{version}")
                    break
                except sqlite3.Error as e:
                    conn.rollback()
                    if "locked" in str(e).lower() and attempt < 4:
                        _t.sleep(1.5)
                        continue
                    raise RuntimeError(f"Migration v{version} failed: {e}")
    
    print(f"Database migrated from v{current_version} to v{target_version}")


def rollback_migration(version: int) -> None:
    """Rollback a specific migration (for development only)."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
        conn.commit()
        print(f"Rolled back migration v{version}")
    except sqlite3.Error as e:
        conn.rollback()
        raise RuntimeError(f"Rollback v{version} failed: {e}")