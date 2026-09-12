# ORISUN IBUKUN — Acceptance Checklist

## Security
- [x] PINs hashed with PBKDF2-HMAC-SHA256 (100k iterations)
- [x] Legacy unsalted SHA-256 hashes auto-upgraded on login
- [x] Master PIN stored in lock.key file (separate from DB)
- [x] Master PIN reset requires deleting lock.key file
- [x] RBAC matrix: Admin=all, Treasurer=6 perms, Secretary=3 perms
- [x] Tab gating by role (Settings/Admin only, Reports/Backup restricted)
- [x] Button gating: Reverse, Approve, Disburse, Add Guarantor all role-gated
- [x] Engine-level RBAC enforcement on reverse_transaction + record_expense
- [x] Single-instance mutex prevents duplicate app instances
- [x] Session timeout: 20 minutes with 5-minute warning

## Data Integrity
- [x] Backup/restore: close connection before overwriting DB file
- [x] Auto-backup on every app close, keeps last 10
- [x] Pre-restore safety copy created before restore
- [x] Migration dry-run: v8→v10 upgrade preserves all data
- [x] Schema v10: external_guarantors + charge_payment_applications
- [x] Loan fees (processing_fee, other_charges) recorded as Money-In
- [x] Reversal window: both savings and loan reversal dialogs work
- [x] Loan repayment: principal-first allocation verified

## Reliability
- [x] 174 simulation scenarios passing (engine-only, report-only)
- [x] Adversarial tests: zero amounts, negative amounts, exceeded balances
- [x] Adversarial tests: disburse non-approved, repay completed
- [x] All form modules import cleanly (8 forms + 3 engines + 5 helpers)
- [x] Global excepthook logs unhandled exceptions to logs/app.log
- [x] Crash log written to APPDATA/OrisunIbukun/crash.log

## Deployment
- [x] Auto-update engine: GitHub Releases API via urllib
- [x] SHA-256 checksum verification on downloaded updates
- [x] Manual "Check for Updates" button in Settings → About
- [x] PIN-gated update check
- [x] Writability check for exe directory
- [x] update.bat script for detached exe replacement
- [x] README.md + .gitignore in repo
- [x] release.py helper for building + publishing releases

## Verification
- [x] Compile-all passes with no errors
- [x] Simulation: 174/174 pass, 0 fail
- [x] Exe built successfully
- [x] Git pushed to James212-lab/OrisunIbukun
