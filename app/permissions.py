"""Role-Based Access Control for ORISUN IBUKUN.

Permission matrix (Admin=full; Treasurer=ops sans reverse/settings/users; Secretary=members/attendance/reports):
"""
import functools
from database.connection import get_connection

# ── Permission constants ─────────────────────────────────────────
PERM_MEMBERS_MANAGE = "members.manage"
PERM_SAVINGS_EDIT = "savings.edit"
PERM_LOANS_MANAGE = "loans.manage"
PERM_ATTENDANCE = "attendance.manage"
PERM_REPORTS_VIEW = "reports.view"
PERM_BACKUP_RESTORE = "backup.restore"
PERM_REVERSE_TXN = "transactions.reverse"
PERM_SETTINGS_EDIT = "settings.edit"
PERM_USERS_MANAGE = "users.manage"
PERM_APP_UPDATE = "app.update"

ROLE_ADMIN = "Administrator"
ROLE_TREASURER = "Treasurer"
ROLE_SECRETARY = "Secretary"

# ── Permission matrix ────────────────────────────────────────────
_ROLE_PERMISSIONS: dict[str, set[str]] = {
    ROLE_ADMIN: {
        PERM_MEMBERS_MANAGE, PERM_SAVINGS_EDIT, PERM_LOANS_MANAGE,
        PERM_ATTENDANCE, PERM_REPORTS_VIEW, PERM_BACKUP_RESTORE,
        PERM_REVERSE_TXN, PERM_SETTINGS_EDIT, PERM_USERS_MANAGE,
        PERM_APP_UPDATE,
    },
    ROLE_TREASURER: {
        PERM_MEMBERS_MANAGE, PERM_SAVINGS_EDIT, PERM_LOANS_MANAGE,
        PERM_ATTENDANCE, PERM_REPORTS_VIEW, PERM_BACKUP_RESTORE,
    },
    ROLE_SECRETARY: {
        PERM_MEMBERS_MANAGE, PERM_ATTENDANCE, PERM_REPORTS_VIEW,
    },
}


def get_role_permissions(role_name: str) -> set[str]:
    """Return the set of permission strings for a role."""
    return _ROLE_PERMISSIONS.get(role_name, set())


def has_permission(role_name: str, perm: str) -> bool:
    """Check if a role has a specific permission."""
    return perm in _ROLE_PERMISSIONS.get(role_name, set())


def get_user_role(user_id: int) -> str:
    """Look up a user's role from the DB."""
    conn = get_connection()
    row = conn.execute(
        """SELECT r.name as role_name
           FROM users u JOIN roles r ON u.role_id = r.id
           WHERE u.id = ?""",
        (user_id,),
    ).fetchone()
    return row["role_name"] if row else ""


def require_permission(perm: str):
    """Decorator for engine functions that need RBAC.

    The decorated function must accept `entered_by` (user_id) as a keyword arg.
    Raises PermissionError if the user lacks the permission.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            user_id = kwargs.get("entered_by") or kwargs.get("created_by")
            if user_id is None:
                # Fallback: try positional args (common: second arg is user_id)
                for a in args[1:3]:
                    if isinstance(a, int) and a > 0:
                        user_id = a
                        break
            if user_id:
                role = get_user_role(user_id)
                if not has_permission(role, perm):
                    raise PermissionError(
                        f"Action not permitted for role '{role}': {perm}")
            return func(*args, **kwargs)
        return wrapper
    return decorator
