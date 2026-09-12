# ORISUN IBUKUN v1.1.1 — Release Notes (copy into GitHub)

## Tag: v1.1.1
## Title: ORISUN IBUKUN v1.1.1

## Exe:
  C:\Users\Public\Orisun_Ibukun\app\dist\OrisunIbukun.exe (41.0 MB)

## SHA256:
0282cfebf0478bce0b0be9c12e9778dd8295d06ccde92512d1ed969f74615496

---

## Release Notes (paste below):

## ORISUN IBUKUN v1.1.1

### Security
- PINs hashed with PBKDF2-HMAC-SHA256 (100k iterations)
- Legacy unsalted SHA-256 hashes auto-upgraded on login
- Master PIN stored in lock.key file (separate from DB)
- Master PIN reset requires deleting lock.key file
- RBAC matrix: Administrator = all, Treasurer = 6 permissions, Secretary = 3 permissions
- Tab and button gating enforced by role
- Single-instance mutex prevents duplicate app instances
- Session timeout: 20 minutes with 5-minute warning

### Data Integrity
- Backup/restore: connection closed before overwriting DB file
- Auto-backup on every app close, keeps last 10
- Migration dry-run tested: v8 → v10 preserves all data
- Loan fees (processing_fee, other_charges) recorded as Money-In
- Loan repayment: principal-first allocation verified

### Reliability
- 174 simulation scenarios passing (174/174)
- Adversarial tests: zero/negative amounts, balance exceeded, state violations
- All form modules import cleanly (8 forms + 3 engines + 5 helpers)
- Global excepthook logs unhandled exceptions to logs/app.log

### Deployment
- Windows version-info resource embedded in exe
- Auto-update via GitHub Releases with SHA-256 verification
- Writability check for exe directory
- 41.0 MB single-file exe, no installation required

### How to update
1. Download OrisunIbukun.exe below
2. Replace the old exe on your computer
3. Launch the new exe — your data is untouched

Or use Settings > About > Check for Updates in the app.
