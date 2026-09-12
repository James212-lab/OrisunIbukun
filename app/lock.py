"""Master PIN lock file — separate from DB so deleting the DB does not bypass it."""
from database.connection import DB_DIR
from utils.helpers import hash_pin, verify_pin

LOCK_FILE = DB_DIR / "lock.key"


def has_master_lock() -> bool:
    """Return True if a master PIN lock file exists."""
    return LOCK_FILE.exists()


def get_master_lock_hash() -> str:
    """Read the stored master PIN hash from the lock file."""
    if not LOCK_FILE.exists():
        return ""
    return LOCK_FILE.read_text(encoding="utf-8").strip()


def set_master_lock(pin: str) -> None:
    """Write a new master PIN hash to the lock file."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    LOCK_FILE.write_text(hash_pin(pin), encoding="utf-8")


def verify_master_lock(pin: str) -> bool:
    """Verify a PIN against the master lock file. Auto-upgrades legacy hashes."""
    stored = get_master_lock_hash()
    if not stored:
        return False
    if verify_pin(pin, stored):
        # Auto-upgrade legacy hash
        if not stored.startswith("pbkdf2_sha256$"):
            set_master_lock(pin)
        return True
    return False


def remove_master_lock() -> None:
    """Delete the lock file (reset master PIN)."""
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()


def change_master_lock(old_pin: str, new_pin: str) -> bool:
    """Change the master PIN. Returns True on success."""
    if not verify_master_lock(old_pin):
        return False
    set_master_lock(new_pin)
    return True
