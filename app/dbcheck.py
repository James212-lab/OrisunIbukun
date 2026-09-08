import sqlite3, os
db = os.path.join(os.environ.get("APPDATA", ""), "OrisunIbukun", "orisun_ibukun.db")
c = sqlite3.connect(db, timeout=5)
try:
    print("integrity:", c.execute("PRAGMA integrity_check").fetchone()[0])
    print("migrations:", [r[0] for r in c.execute("SELECT version FROM schema_migrations ORDER BY version").fetchall()])
    print("users:", c.execute("SELECT count(*) FROM users").fetchone()[0])
    print("members:", c.execute("SELECT count(*) FROM members").fetchone()[0])
except Exception as e:
    print("CHECK_FAIL:", type(e).__name__, e)
