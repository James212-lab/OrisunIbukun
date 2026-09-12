# ORISUN IBUKUN — Cooperative Management System

Offline cooperative management app built with Python/Tkinter. Tracks members, savings, loans, attendance, passbooks, treasury, and reports. Works fully offline — all data stored in a local SQLite database.

## Requirements

- Python 3.14+
- pip packages: `pyinstaller`, `Pillow`, `tkcalendar`, `numpy`

## Quick Start (development)

```bash
cd app
python main.py
```

Default admin: username `admin`, PIN printed on first launch.

## Build the Executable

```bash
cd app
python build.py
```

Produces `app/dist/OrisunIbukun.exe` (~41 MB). Prints the SHA-256 hash for release notes.

## Release and Update Flow

### Making a release

```bash
cd app

# Option 1: Automated (requires gh CLI authenticated)
python release.py --publish

# Option 2: Semi-automated
python release.py
# Then follow the printed manual steps to create a GitHub Release

# Override version if needed
python release.py --version 1.2.0 --publish
```

### How updates reach other computers

1. You push a new GitHub Release with the `.exe` attached + `SHA256: <hex>` in the notes.
2. On the other computer: **Settings > About > Unlock (login PIN) > Check for Updates**.
3. The app fetches `api.github.com/repos/James212-lab/OrisunIbukun/releases/latest`, compares versions, downloads the `.exe`, verifies the SHA-256, then offers to close and replace.
4. A detached batch script replaces the exe after exit and relaunches. User data (DB in `%APPDATA%`) is untouched; schema migrations run automatically on next launch.

**Important:** Pushing source code alone does NOT update installed apps. Only GitHub Releases trigger updates.

### Version convention

- `APP_VERSION` in `app/constants.py` must match the release tag (e.g. `1.2.0` → tag `v1.2.0`).
- Tag must be numerically greater than the installed version for the app to detect it as "newer."

## Security Features

| Feature | Description |
|---|---|
| **Master PIN lock** | App locked on startup. Set on first launch; change/remove in Settings > About. |
| **Admin-PIN gate** | "Check for Updates" is locked by default; requires your login PIN to unlock per session. |
| **SHA-256 checksum** | Download blocked unless release notes contain a valid `SHA256: <hex>` line matching the exe. |
| **Fixed repo** | Update source is hardcoded to `James212-lab/OrisunIbukun` — not editable from the UI. |

## Project Structure

```
Orisun_Ibukun/
├── app/
│   ├── main.py                  # Entry point
│   ├── constants.py             # APP_VERSION, GITHUB_REPO, TXN types, roles
│   ├── build.py                 # PyInstaller build script
│   ├── release.py               # Release helper (build + GitHub upload)
│   ├── database/
│   │   ├── connection.py        # SQLite connection, DB path resolution
│   │   ├── schema.py            # create_schema, get_setting, set_setting
│   │   └── migrations.py        # Schema migrations v1–v10
│   ├── engines/
│   │   ├── transaction_engine.py  # All business logic (savings, loans, passbook, etc.)
│   │   ├── backup_engine.py       # Backup/restore
│   │   └── update_engine.py       # GitHub Releases auto-update
│   ├── ui/
│   │   ├── login_form.py       # Login + master PIN lock overlay
│   │   ├── main_form.py        # Dashboard with IN/OUT/Net treasury
│   │   ├── member_form.py      # Member CRUD + departure
│   │   ├── savings_form.py     # Passbook (Money-In) + savings detail
│   │   ├── loan_form.py        # Loan lifecycle + guarantors + documents
│   │   ├── attendance_form.py  # Meeting/attendance + charges
│   │   ├── report_form.py      # Financial/member/treasury reports
│   │   ├── backup_form.py      # Backup/restore UI
│   │   └── settings_form.py    # Coop info, financial, users, updates, master PIN
│   ├── simulation/              # Engine-only test suite (89 scenarios)
│   │   ├── harness.py
│   │   ├── test_scenarios.py
│   │   └── run.py
│   └── assets/                  # Icons, images
└── README.md
```

## Simulation (engine tests)

```bash
cd app
python simulation/run.py
```

Runs 89 headless scenarios covering schema, members, savings, passbook Money-In, loans, loan fees, external guarantors, attendance charges, reversals, treasury, shares (neutralized), reports, update engine, and master PIN. Report saved to `app/simulation/report_<timestamp>.txt`.

## Default Credentials

| Account | Username | PIN |
|---|---|---|
| Admin | `admin` | Printed on first launch (shown once) |
| Master PIN | — | Set on first app launch |

Change both in **Settings** after logging in.

## Data Location

| Mode | Database path |
|---|---|
| Source (`python main.py`) | `app/data/orisun_ibukun.db` |
| Frozen (`.exe`) | `%APPDATA%/OrisunIbukun/orisun_ibukun_py.db` |

Backups stored in `app/data/backups/` (source) or `%APPDATA%/OrisunIbukun/backups/` (frozen).
