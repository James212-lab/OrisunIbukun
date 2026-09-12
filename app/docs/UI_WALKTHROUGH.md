# UI Walkthrough — ORISUN IBUKUN v1.1.1

Run this on a machine with a display (the exe cannot show windows in a headless environment).

---

## Pre-conditions
- OrisunIbukun.exe placed in a user-writable folder (e.g. Desktop or Documents)
- At least one Administrator account exists (default: PIN `0000` if freshly created)

---

## 1. Launch + Single-Instance Check

| Step | Action | Expected |
|------|--------|----------|
| 1 | Double-click `OrisunIbukun.exe` | Login form appears, title "ORISUN IBUKUN" |
| 2 | Launch a **second** instance of the same exe | Second window closes immediately or shows "already running" message |

---

## 2. Master Lock (Administrator only)

| Step | Action | Expected |
|------|--------|----------|
| 1 | On first launch, click "Set Master Lock" | Prompt for a 4-6 digit master PIN |
| 2 | Enter a master PIN (e.g. `1234`) | Confirmation message: "Master lock set" |
| 3 | Click "Set Master Lock" again | "Master lock already exists" message |
| 4 | Click "Remove Master Lock" | Requires entering the current master PIN first |
| 5 | Enter correct master PIN | Lock removed; next launch shows "Set Master Lock" again |
| 6 | Re-set the master PIN, then close the app | Master lock persists; next launch requires PIN to enter |

---

## 3. Login + RBAC

| Step | Action | Expected |
|------|--------|----------|
| 1 | Enter a user PIN (e.g. `1234` for admin) | Login succeeds; main form opens with a welcome message |
| 2 | Enter a wrong PIN | "Incorrect PIN" error; no login |
| 3 | Log in as Administrator | All tabs visible: Members, Savings, Loans, Attendance, Reports, Backup, Settings |
| 4 | Log in as Treasurer | Members, Savings, Loans, Attendance, Reports visible. Settings and Backup tabs hidden. Reverse button hidden in Savings/Loans. |
| 5 | Log in as Secretary | Members, Attendance, Reports visible. Savings, Loans, Backup, Settings hidden. No edit buttons in Savings or Loans. |

---

## 4. Session Timeout

| Step | Action | Expected |
|------|--------|----------|
| 1 | Log in, then leave the app idle for ~20 minutes | Session expires; app returns to login screen |
| 2 | Log in, leave idle for ~15 minutes | Warning dialog appears: "Session will expire in 5 minutes" |

---

## 5. Members Tab

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Register New Member" | Form appears with fields: Name, Phone, Address, Category |
| 2 | Register a member | Member appears in the list with an auto-generated ID (ORI-XXXX) |
| 3 | Double-click a member in the list | Member detail view opens |
| 4 | In member detail, click "Record Savings" | Savings dialog opens; enter amount and save |
| 5 | In member detail, click "Approve Loan" (if loan exists) | Only visible if logged in as Administrator or Treasurer |
| 6 | In member detail, click "Add Guarantor" | Guarantor selection dialog opens |
| 7 | Log in as Secretary, open Members tab | "Approve Loan" and "Add Guarantor" buttons hidden |

---

## 6. Savings Tab

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Record Savings" | Savings entry form opens |
| 2 | Enter a valid amount and save | Transaction appears in savings list with status "Posted" |
| 3 | Enter 0 or negative amount | "Amount must be greater than zero" error |
| 4 | Click "Reverse" on a savings transaction | Reversal reason dialog opens (only if logged in as Administrator or Treasurer) |
| 5 | Log in as Secretary, open Savings tab | Savings list is read-only; "Record Savings" and "Reverse" buttons hidden |

---

## 7. Loans Tab

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "New Loan" tab | Loan entry form opens |
| 2 | Select a member, enter amount and interest | Loan created with status "Applied" |
| 3 | Click "Approve" on the loan | Status changes to "Approved" |
| 4 | Click "Disburse" on the loan | Status changes to "Disbursed"; processing fee and other charges recorded as Money-In |
| 5 | Click "Repay" on the loan | Payment dialog opens; enter amount |
| 6 | Repay less than outstanding principal | Principal decreases first, then interest |
| 7 | Repay full amount | Loan status changes to "Completed" |
| 8 | Log in as Treasurer, open Loans tab | "Reverse" button hidden |
| 9 | Log in as Secretary, open Loans tab | Loans tab hidden entirely |

---

## 8. Attendance Tab

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "New Meeting" | Meeting creation form opens |
| 2 | Mark members Present/Absent | Save attendance; absence fines applied automatically |
| 3 | Click "Print Attendance" | HTML attendance sheet opens in browser |

---

## 9. Reports Tab

| Step | Action | Expected |
|------|--------|----------|
| 1 | Select "Member Savings Statement" from dropdown | Treeview updates with savings data |
| 2 | Select "Monthly Money In/Out" | Monthly summary with savings, minutes, loans disbursed, expenses |
| 3 | Select "Attendance Report" | Attendance percentages by member |
| 4 | Log in as Secretary | Reports tab is visible (Secretary has report access) |

---

## 10. Backup Tab (Administrator / Treasurer only)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Click "Create Backup" | Backup created; appears in the list |
| 2 | Select a backup from the list | Restore button becomes active |
| 3 | Click "Restore" | Confirmation dialog: "This will replace all current data" |
| 4 | Confirm restore | Connection closed, DB replaced, success message shown |
| 5 | Log in as Secretary | Backup tab hidden entirely |

---

## 11. Settings Tab (Administrator only)

| Step | Action | Expected |
|------|--------|----------|
| 1 | Open Settings tab | Four sub-tabs: Cooperative Info, Financial, Users, About |
| 2 | Log in as Treasurer | Settings tab hidden |
| 3 | Log in as Secretary | Settings tab hidden |
| 4 | In "About" sub-tab, click "Check for Updates" | Requires master PIN to unlock; checks GitHub for newer version |

---

## 12. Auto-Backup on Close

| Step | Action | Expected |
|------|--------|----------|
| 1 | Make a change (e.g. record savings), then close the app | Auto-backup runs before closing |
| 2 | Open the Backups folder (`%APPDATA%/OrisunIbukun/backups/`) | Auto-backup file present with "Automatic" label |

---

## 13. Auto-Update (after publishing v1.1.1 release)

| Step | Action | Expected |
|------|--------|----------|
| 1 | On a machine running v1.1.0, open Settings > About | Click "Check for Updates" |
| 2 | Enter master PIN when prompted | App checks GitHub for v1.1.1 |
| 3 | If newer version found | "Update available" dialog with download progress |
| 4 | Confirm update | App closes, update.bat replaces exe, app relaunches |
| 5 | Check version in Settings > About | Shows v1.1.1 |

---

## 14. Crash Log

| Step | Action | Expected |
|------|--------|----------|
| 1 | If the app crashes, check `%APPDATA%/OrisunIbukun/logs/app.log` | Timestamped entry with full traceback |

---

**Time to complete all steps:** ~30 minutes

**Sign-off:** _________________  Date: _________________
