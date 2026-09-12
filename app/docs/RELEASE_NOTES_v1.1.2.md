# ORISUN IBUKUN v1.1.2 — Release Notes (copy into GitHub)

## Tag: v1.1.2
## Title: ORISUN IBUKUN v1.1.2

## Exe:
  C:\Users\Public\Orisun_Ibukun\app\dist\OrisunIbukun.exe (41.0 MB)

## SHA256:
f2157797b318cce601fe581297dde87833beb531681c61b6fd26c481c30aa421

---

## Release Notes (paste below):

## ORISUN IBUKUN v1.1.2

### Hotfix: Loan tab NameError (v1.1.1 regression)
- Fixed NameError on Loan tab: `REPAY_MONTHLY`/`REPAY_WEEKLY` were accidentally dropped from the constants import during the v1.1.1 RBAC change
- Added missing `TXN_EXPENSE` import in transaction engine
- Fixed lambda capture scope issue in Settings > About update dialog

### New: Static analysis gate
- Added `pyflakes` scan to the simulation suite (scenario #175) — catches undefined names across all app source files automatically
- Zero undefined names across the entire codebase

### All existing features unchanged
- 175 simulation scenarios passing (175/175)
- PBKDF2 PIN hashing, RBAC, master lock, backup/restore, single-instance, excepthook, version-info

### How to update
1. Download OrisunIbukun.exe below
2. Replace the old exe on your computer
3. Launch the new exe — your data is untouched

Or use Settings > About > Check for Updates in the app.
