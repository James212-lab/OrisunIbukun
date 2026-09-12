"""Database schema creation and migration."""
import sqlite3
from database.connection import get_connection

SCHEMA_VERSION = 10

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    permissions TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    pin_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL REFERENCES roles(id),
    is_active INTEGER DEFAULT 1,
    last_login TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    date_joined TEXT NOT NULL,
    status TEXT DEFAULT 'Active',
    date_ended TEXT,
    exit_reason TEXT,
    entrance_fee REAL DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    share_value REAL DEFAULT 0,
    notes TEXT,
    dob TEXT,
    gender TEXT,
    occupation TEXT,
    email TEXT,
    next_of_kin TEXT,
    next_of_kin_phone TEXT,
    id_type TEXT,
    id_number TEXT,
    photo_path TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS meetings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_number INTEGER NOT NULL UNIQUE,
    date TEXT NOT NULL,
    notes TEXT,
    decisions TEXT,
    is_closed INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id),
    member_id INTEGER NOT NULL REFERENCES members(id),
    status TEXT DEFAULT 'Present',
    notes TEXT,
    recorded_by INTEGER REFERENCES users(id),
    recorded_at TEXT DEFAULT (datetime('now')),
    UNIQUE(meeting_id, member_id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL UNIQUE,
    date TEXT NOT NULL,
    meeting_id INTEGER REFERENCES meetings(id),
    member_id INTEGER REFERENCES members(id),
    transaction_type TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0,
    payment_method TEXT,
    description TEXT,
    status TEXT DEFAULT 'Posted',
    entered_by INTEGER REFERENCES users(id),
    entered_at TEXT DEFAULT (datetime('now')),
    is_imported INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS transaction_reversals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_transaction_id TEXT NOT NULL,
    reversal_transaction_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    reversed_by INTEGER REFERENCES users(id),
    reversed_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS savings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL REFERENCES members(id),
    transaction_id TEXT NOT NULL REFERENCES transactions(transaction_id),
    type TEXT NOT NULL,
    amount REAL NOT NULL DEFAULT 0,
    balance_after REAL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL REFERENCES members(id),
    transaction_id TEXT NOT NULL REFERENCES transactions(transaction_id),
    shares_added INTEGER DEFAULT 0,
    total_shares INTEGER DEFAULT 0,
    value_per_share REAL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS loans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id TEXT NOT NULL UNIQUE,
    member_id INTEGER NOT NULL REFERENCES members(id),
    application_date TEXT NOT NULL,
    approval_date TEXT,
    disbursement_date TEXT,
    principal_amount REAL NOT NULL DEFAULT 0,
    interest_rate REAL DEFAULT 0,
    interest_amount REAL DEFAULT 0,
    processing_fee REAL DEFAULT 0,
    other_charges REAL DEFAULT 0,
    total_repayable REAL DEFAULT 0,
    repayment_frequency TEXT DEFAULT 'Monthly',
    expected_repayment REAL DEFAULT 0,
    start_date TEXT,
    due_date TEXT,
    outstanding_principal REAL DEFAULT 0,
    outstanding_interest REAL DEFAULT 0,
    status TEXT DEFAULT 'Applied',
    approval_notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS loan_guarantors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    guarantor_member_id INTEGER NOT NULL REFERENCES members(id),
    guarantee_amount REAL DEFAULT 0,
    date_guaranteed TEXT DEFAULT (datetime('now')),
    status TEXT DEFAULT 'Active'
);

CREATE TABLE IF NOT EXISTS loan_repayments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    transaction_id TEXT NOT NULL REFERENCES transactions(transaction_id),
    amount REAL NOT NULL DEFAULT 0,
    principal_portion REAL DEFAULT 0,
    interest_portion REAL DEFAULT 0,
    balance_after REAL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL REFERENCES transactions(transaction_id),
    category TEXT,
    description TEXT,
    amount REAL NOT NULL DEFAULT 0,
    approved_by INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS headquarters_remittances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    remittance_id TEXT NOT NULL UNIQUE,
    date TEXT NOT NULL,
    period_covered TEXT,
    amount REAL NOT NULL DEFAULT 0,
    destination TEXT,
    payment_method TEXT,
    reference_number TEXT,
    prepared_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    notes TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS minutes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meeting_id INTEGER NOT NULL REFERENCES meetings(id),
    content TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS member_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER NOT NULL REFERENCES members(id),
    note TEXT NOT NULL,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    details TEXT,
    ip_address TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS backups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    backup_path TEXT NOT NULL,
    backup_type TEXT DEFAULT 'Manual',
    file_size INTEGER,
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TEXT DEFAULT (datetime('now'))
);

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

CREATE TABLE IF NOT EXISTS loan_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    loan_id INTEGER NOT NULL REFERENCES loans(id),
    member_id INTEGER NOT NULL REFERENCES members(id),
    doc_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    uploaded_at TEXT DEFAULT (datetime('now')),
    uploaded_by INTEGER REFERENCES users(id)
);

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
"""


def create_schema() -> None:
    conn = get_connection()
    conn.executescript(SCHEMA_SQL)
    _seed_defaults(conn)
    conn.commit()
    # Run any pending migrations
    from database.migrations import run_migrations
    run_migrations()


def _seed_defaults(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM roles")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO roles (name, permissions) VALUES (?, ?)",
            [
                ("Administrator", '{"all": true}'),
                ("Treasurer", '{"savings": true, "shares": true, "loans": true, "reports": true}'),
                ("Secretary", '{"members": true, "attendance": true, "meetings": true}'),
            ],
        )

    cur.execute("SELECT COUNT(*) FROM settings")
    if cur.fetchone()[0] == 0:
        defaults = {
            "app_name": "ORISUN IBUKUN",
            "unit_name": "Owode Unit",
            "currency": "₦",
            "meeting_day": "Friday",
            "share_price": "1000",
            "entrance_fee": "5000",
            "min_savings_withdrawal": "10000",
            "max_loan_multiplier": "3",
            "required_guarantors": "2",
            "interest_rate": "5",
            "absent_fine": "0",
            "interest_method": "Flat",
            "late_payment_penalty": "500",
            "schema_version": str(SCHEMA_VERSION),
        }
        cur.executemany(
            "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
            list(defaults.items()),
        )

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        import hashlib
        import random
        import string
        pin = "".join(random.choices(string.digits, k=6))
        pin_hash = hashlib.sha256(pin.encode()).hexdigest()
        cur.execute(
            "INSERT INTO users (username, pin_hash, role_id) VALUES (?, ?, ?)",
            ("admin", pin_hash, 1),
        )
        cur.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
            ("initial_admin_pin", pin),
        )


def get_setting(key: str, default: str = "") -> str:
    conn = get_connection()
    cur = conn.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cur.fetchone()
    return row["value"] if row else default


def get_and_clear_initial_admin_pin() -> str:
    """Return and clear the one-time initial admin PIN from settings, if present."""
    conn = get_connection()
    cur = conn.execute("SELECT value FROM settings WHERE key = ?", ("initial_admin_pin",))
    row = cur.fetchone()
    if not row:
        return ""
    pin = row["value"]
    conn.execute("DELETE FROM settings WHERE key = ?", ("initial_admin_pin",))
    conn.commit()
    return pin



def set_setting(key: str, value: str) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime('now'))",
        (key, value),
    )
    conn.commit()
