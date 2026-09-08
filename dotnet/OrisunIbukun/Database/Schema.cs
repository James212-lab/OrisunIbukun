using System;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Data.Sqlite;

namespace OrisunIbukun.Database
{
    public static class Schema
    {
        public static void Create()
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();

            cmd.CommandText = @"
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    pin_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'Member',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS roles (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS members (
    id TEXT PRIMARY KEY,
    member_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    date_of_birth TEXT,
    gender TEXT,
    occupation TEXT,
    next_of_kin TEXT,
    next_of_kin_phone TEXT,
    entrance_fee REAL NOT NULL DEFAULT 0,
    date_joined TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Active',
    photo_path TEXT,
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS member_documents (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    uploaded_by TEXT,
    uploaded_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (uploaded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS digital_forms (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    form_type TEXT NOT NULL,
    form_data TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Draft',
    created_by TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS meetings (
    id TEXT PRIMARY KEY,
    meeting_number INTEGER NOT NULL,
    meeting_date TEXT NOT NULL,
    notes TEXT,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS attendance (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    member_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Present',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (meeting_id) REFERENCES meetings(id),
    FOREIGN KEY (member_id) REFERENCES members(id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    type TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT,
    reference TEXT,
    recorded_by TEXT NOT NULL,
    transaction_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (recorded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS transaction_reversals (
    id TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    reversed_by TEXT NOT NULL,
    reason TEXT NOT NULL,
    reversed_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (transaction_id) REFERENCES transactions(id),
    FOREIGN KEY (reversed_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS savings (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    amount REAL NOT NULL,
    balance REAL NOT NULL,
    method TEXT NOT NULL DEFAULT 'Cash',
    notes TEXT,
    recorded_by TEXT NOT NULL,
    savings_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (recorded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS shares (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    shares_count INTEGER NOT NULL DEFAULT 1,
    amount REAL NOT NULL,
    recorded_by TEXT NOT NULL,
    share_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (recorded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS loans (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    amount REAL NOT NULL,
    interest_rate REAL NOT NULL DEFAULT 0,
    total_payable REAL NOT NULL,
    purpose TEXT,
    status TEXT NOT NULL DEFAULT 'Pending',
    approved_by TEXT,
    disbursed_by TEXT,
    applied_date TEXT NOT NULL,
    approved_date TEXT,
    disbursed_date TEXT,
    due_date TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (disbursed_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS loan_guarantors (
    id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    member_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (loan_id) REFERENCES loans(id),
    FOREIGN KEY (member_id) REFERENCES members(id)
);

CREATE TABLE IF NOT EXISTS loan_repayments (
    id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL,
    amount REAL NOT NULL,
    recorded_by TEXT NOT NULL,
    payment_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (loan_id) REFERENCES loans(id),
    FOREIGN KEY (recorded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS expenses (
    id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT,
    approved_by TEXT,
    recorded_by TEXT NOT NULL,
    expense_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (approved_by) REFERENCES users(id),
    FOREIGN KEY (recorded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS headquarters_remittances (
    id TEXT PRIMARY KEY,
    amount REAL NOT NULL,
    description TEXT,
    remitted_by TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    remittance_date TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (remitted_by) REFERENCES users(id),
    FOREIGN KEY (recorded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS minutes (
    id TEXT PRIMARY KEY,
    meeting_id TEXT NOT NULL,
    content TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (meeting_id) REFERENCES meetings(id),
    FOREIGN KEY (recorded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS member_notes (
    id TEXT PRIMARY KEY,
    member_id TEXT NOT NULL,
    note TEXT NOT NULL,
    recorded_by TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (recorded_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS member_charges (
    id TEXT PRIMARY KEY,
    charge_id TEXT UNIQUE NOT NULL,
    member_id TEXT NOT NULL,
    meeting_id TEXT,
    charge_type TEXT NOT NULL,
    description TEXT,
    amount REAL NOT NULL DEFAULT 0,
    amount_paid REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Owed',
    created_by TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (member_id) REFERENCES members(id),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    action TEXT NOT NULL,
    table_name TEXT,
    record_id TEXT,
    old_value TEXT,
    new_value TEXT,
    ip_address TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS backups (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    created_by TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (created_by) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
);
";
            cmd.ExecuteNonQuery();
            SeedData(conn);
        }

        private static void SeedData(SqliteConnection conn)
        {
            using var cmd = conn.CreateCommand();

            cmd.CommandText = "SELECT COUNT(*) FROM roles";
            var count = Convert.ToInt32(cmd.ExecuteScalar());
            if (count == 0)
            {
                cmd.CommandText = @"INSERT INTO roles (id, name, description) VALUES 
                    ('role_admin', 'Administrator', 'Full system access'),
                    ('role_treasurer', 'Treasurer', 'Financial management access'),
                    ('role_secretary', 'Secretary', 'Minutes and attendance access')";
                cmd.ExecuteNonQuery();
            }

            cmd.CommandText = "SELECT COUNT(*) FROM settings";
            count = Convert.ToInt32(cmd.ExecuteScalar());
            if (count == 0)
            {
                cmd.CommandText = @"INSERT INTO settings (key, value, description) VALUES
                    ('app_name', 'ORISUN IBUKUN', 'Application name'),
                    ('unit_name', 'Owode Unit', 'Cooperative unit name'),
                    ('currency', '₦', 'Currency symbol'),
                    ('meeting_day', 'Friday', 'Default meeting day'),
                    ('share_price', '1000', 'Price per share'),
                    ('entrance_fee', '5000', 'Default entrance fee'),
                    ('max_loan_multiplier', '3', 'Max loan as multiple of savings'),
                    ('interest_rate', '5', 'Default interest rate percentage'),
                    ('savings_target', '50000', 'Monthly savings target per member')";
                cmd.ExecuteNonQuery();
            }

            cmd.CommandText = "SELECT COUNT(*) FROM users WHERE username='admin'";
            count = Convert.ToInt32(cmd.ExecuteScalar());
            if (count == 0)
            {
                string pin = new Random().Next(100000, 999999).ToString();
                string pinHash = Utils.Helpers.HashPin(pin);
                cmd.CommandText = "INSERT INTO users (id, username, pin_hash, full_name, role) VALUES (@id, @uname, @pin, @fname, @role)";
                cmd.Parameters.AddWithValue("@id", Utils.Helpers.GenerateId("usr"));
                cmd.Parameters.AddWithValue("@uname", "admin");
                cmd.Parameters.AddWithValue("@pin", pinHash);
                cmd.Parameters.AddWithValue("@fname", "Administrator");
                cmd.Parameters.AddWithValue("@role", "Administrator");
                cmd.ExecuteNonQuery();

                cmd.CommandText = "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('initial_admin_pin', @initpin, datetime('now'))";
                cmd.Parameters.Clear();
                cmd.Parameters.AddWithValue("@initpin", pin);
                cmd.ExecuteNonQuery();
            }
        }

        public static string GetSetting(string key)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT value FROM settings WHERE key=@key";
            cmd.Parameters.AddWithValue("@key", key);
            var result = cmd.ExecuteScalar();
            return result?.ToString() ?? "";
        }

        public static void SetSetting(string key, string value)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (@key, @val, datetime('now'))";
            cmd.Parameters.AddWithValue("@key", key);
            cmd.Parameters.AddWithValue("@val", value);
            cmd.ExecuteNonQuery();
        }
    }
}
