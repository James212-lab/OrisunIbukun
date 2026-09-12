"""Simulation harness — isolated temp DB + result recorder."""
import os
import sys
import tempfile
import shutil
import datetime
from pathlib import Path

# Add app dir to path so imports resolve
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


class SimResult:
    def __init__(self, name, passed, detail=""):
        self.name = name
        self.passed = passed
        self.detail = detail

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.name}: {self.detail}" if self.detail else f"[{status}] {self.name}"


class SimHarness:
    def __init__(self):
        self.results = []
        self._tmp_dir = None
        self._db_path = None

    def setup(self):
        self._tmp_dir = Path(tempfile.mkdtemp(prefix="orisun_sim_"))
        self._db_path = self._tmp_dir / "test.db"

        import database.connection as conn_mod
        conn_mod.DB_PATH = self._db_path
        conn_mod.DB_DIR = self._tmp_dir
        conn_mod._connection = None

        from database.schema import create_schema
        create_schema()

        # Admin user is seeded by create_schema; just fetch it
        from database.connection import get_connection
        conn = get_connection()
        self._admin_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()["id"]

    def teardown(self):
        from database.connection import close_connection
        close_connection()
        if self._tmp_dir and self._tmp_dir.exists():
            shutil.rmtree(self._tmp_dir, ignore_errors=True)

    def record(self, name, passed, detail=""):
        r = SimResult(name, passed, detail)
        self.results.append(r)
        return r

    def assert_true(self, name, condition, detail=""):
        return self.record(name, bool(condition), detail)

    def assert_eq(self, name, actual, expected, detail=""):
        ok = actual == expected
        d = detail or f"expected={expected}, got={actual}"
        return self.record(name, ok, d)

    def assert_raises(self, name, exc_type, fn, *args, **kwargs):
        try:
            fn(*args, **kwargs)
            return self.record(name, False, "Expected exception not raised")
        except exc_type as e:
            return self.record(name, True, str(e))
        except Exception as e:
            return self.record(name, False, f"Wrong exception: {type(e).__name__}: {e}")

    def summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        lines = [
            f"Total: {total} | Passed: {passed} | Failed: {failed}",
            "",
        ]
        for r in self.results:
            status = "PASS" if r.passed else "FAIL"
            detail = f" -- {r.detail}" if r.detail else ""
            lines.append(f"  [{status}] {r.name}{detail}")
        return "\n".join(lines)
