# User Acceptance Test — ORISUN IBUKUN v1.1.1

For the Owode Unit Cooperative — run by cooperative operators on real data.

---

## Pre-requisites
- OrisunIbukun.exe v1.1.1 placed in a user-writable folder on the target computer
- The cooperative's real database available (or a copy for testing)

---

## Test Scenarios

### Scenario 1: First-Time Setup
| Step | Action | Pass? |
|------|--------|-------|
| 1 | Launch the app | Login form appears |
| 2 | Set a master lock PIN (e.g. `1234`) | Master lock set successfully |
| 3 | Create an Administrator account | Admin user created |
| 4 | Create a Treasurer account | Treasurer user created |
| 5 | Create a Secretary account | Secretary user created |
| 6 | Log out | Returns to login screen |

---

### Scenario 2: Administrator Full Access
| Step | Action | Pass? |
|------|--------|-------|
| 1 | Log in as Administrator | All tabs visible: Members, Savings, Loans, Attendance, Reports, Backup, Settings |
| 2 | Register a new member | Member appears with auto-generated ID |
| 3 | Record savings for the member | Savings balance increases |
| 4 | Create a loan for the member | Loan appears with status "Applied" |
| 5 | Approve the loan | Status changes to "Approved" |
| 6 | Disburse the loan | Status changes to "Disbursed"; processing fee recorded |
| 7 | Record a partial repayment | Principal decreases first, then interest |
| 8 | Record a full repayment | Loan status changes to "Completed" |
| 9 | Reverse a savings transaction | Transaction marked "Reversed"; balance restored |
| 10 | Create a backup | Backup file appears in the list |
| 11 | Restore from the backup | Data restored to previous state |
| 12 | Open Settings > About | Version shows v1.1.1 |

---

### Scenario 3: Treasurer Limited Access
| Step | Action | Pass? |
|------|--------|-------|
| 1 | Log in as Treasurer | Members, Savings, Loans, Attendance, Reports visible. Settings and Backup hidden. |
| 2 | Register a new member | Works (Treasurer has member access) |
| 3 | Record savings | Works |
| 4 | Create and approve a loan | Works |
| 5 | Try to reverse a transaction | Reverse button hidden — CANNOT reverse |
| 6 | Try to access Settings | Settings tab hidden — CANNOT access |
| 7 | Try to access Backup | Backup tab hidden — CANNOT access |

---

### Scenario 4: Secretary Limited Access
| Step | Action | Pass? |
|------|--------|-------|
| 1 | Log in as Secretary | Members, Attendance, Reports visible. Savings, Loans, Backup, Settings hidden. |
| 2 | Register a new member | Works (Secretary has member access) |
| 3 | Open Reports tab | Works; generate Member Savings Statement |
| 4 | Try to record savings | Savings tab hidden — CANNOT access |
| 5 | Try to create a loan | Loans tab hidden — CANNOT access |
| 6 | Try to reverse a transaction | CANNOT access (no Loans tab) |
| 7 | Try to access Backup | Backup tab hidden — CANNOT access |
| 8 | Try to access Settings | Settings tab hidden — CANNOT access |

---

### Scenario 5: Attendance and Charges
| Step | Action | Pass? |
|------|--------|-------|
| 1 | Log in as Administrator | All tabs visible |
| 2 | Create a new meeting | Meeting created |
| 3 | Mark members Present and Absent | Attendance saved |
| 4 | Apply absence fines | Charge applied to absent members |
| 5 | Apply minutes levy | Charge applied to all members |
| 6 | Pay an absence fine | Charge marked "Paid"; audit trail updated |
| 7 | Print attendance sheet | HTML opens in browser |

---

### Scenario 6: External Guarantors
| Step | Action | Pass? |
|------|--------|-------|
| 1 | Open a loan detail view | Guarantors section visible |
| 2 | Click "Add External Guarantor" | Form opens for non-member guarantor |
| 3 | Enter name and relationship | External guarantor saved |
| 4 | Verify guarantor appears in loan detail | Shows name and relationship |

---

### Scenario 7: Auto-Backup on Close
| Step | Action | Pass? |
|------|--------|-------|
| 1 | Record a savings transaction | Transaction saved |
| 2 | Close the app (X button or File > Exit) | App closes normally |
| 3 | Check `%APPDATA%/OrisunIbukun/backups/` | Auto-backup file present |
| 4 | Verify only last 10 auto-backups are kept | Older auto-backups deleted |

---

### Scenario 8: Single Instance
| Step | Action | Pass? |
|------|--------|-------|
| 1 | Launch the app | First instance opens |
| 2 | Launch a second instance | Second instance closes immediately or shows "already running" |

---

### Scenario 9: Auto-Update (requires v1.1.1 release published)
| Step | Action | Pass? |
|------|--------|-------|
| 1 | Log in as Administrator | All tabs visible |
| 2 | Open Settings > About | "Check for Updates" button visible |
| 3 | Click "Check for Updates" | Requires master PIN |
| 4 | Enter master PIN | App checks GitHub for newer version |
| 5 | If v1.1.1 is available | "Update available" dialog shown |
| 6 | Confirm download | Exe downloads with progress bar |
| 7 | Confirm install | App closes, exe replaced, app relaunches |
| 8 | Check version in Settings > About | Shows v1.1.1 |

---

### Scenario 10: Data Integrity After Update
| Step | Action | Pass? |
|------|--------|-------|
| 1 | Before update: note member count and savings balance | Recorded |
| 2 | After update: check member count and savings balance | Same as before |
| 3 | Check loan statuses | Same as before |
| 4 | Check attendance records | Same as before |

---

## Sign-off

All scenarios passed:  [ ] Yes  [ ] No

Tester name: _______________________

Date: _______________________

Signature: _______________________

Notes:
_________________________________________________________________
_________________________________________________________________
