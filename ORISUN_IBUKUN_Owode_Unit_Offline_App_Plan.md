# ORISUN IBUKUN – Owode Unit
## Offline Cooperative Management System — Product & Technical Plan

**Document status:** First design specification  
**Primary environment:** Installed, offline desktop application  
**Primary users:** Cooperative administrators with limited computer literacy  
**Brand:** Blue and white  
**Cooperative meeting day:** Every Friday

---

## 1. Product Vision

Build a simple, secure, offline-first cooperative management application that behaves like a familiar digital cooperative register rather than a complicated accounting program.

The application must make everyday work easy:

- Find a member quickly.
- Record Friday attendance.
- Record savings, shares, loan repayments, loan collections and other approved transactions.
- See the complete financial history of a member in one place.
- Provide a virtual savings booklet for every member.
- Track loans, guarantors and outstanding obligations.
- See monthly money-in / money-out figures.
- Track amounts remitted to headquarters.
- Preserve an auditable history of every financial action.
- Survive software upgrades without losing historical records.
- Provide reliable backup and restore without internet access.

### Core design principle

> **Simple on the surface, rigorous underneath.**

The operator should see a small number of clear actions while the software handles calculations, validation, history, permissions and data integrity in the background.

---

# 2. Design Principles

## 2.1 Simplicity

Avoid unnecessary graphics, animations, charts and technical terminology.

Prefer:

- Large readable buttons.
- Clear labels.
- Familiar cooperative language.
- Short forms.
- One task per screen.
- Strong confirmation messages.
- Search instead of long lists.

Avoid:

- Crowded dashboards.
- Excessive menus.
- Small icons without labels.
- Technical database terminology.
- Manual calculations wherever software can calculate safely.

## 2.2 Offline First

The application must function completely without internet access.

Internet connectivity must never be required for:

- Member registration.
- Attendance.
- Savings entries.
- Loan entries.
- Repayments.
- Reports.
- Printing.
- Searching.
- Backup.
- Restore.

Future versions may support controlled import/export or synchronization, but the first version should not depend on a server.

## 2.3 Financial History Is Sacred

Do not make a changing balance the only source of truth.

The system should preserve the underlying transactions. Current balances should be calculated from transactions and approved adjustments.

A financial transaction should normally be **reversed/corrected**, not silently deleted.

---

# 3. Target Users and Roles

A simple role system is recommended.

## 3.1 Administrator

Can:

- Manage users.
- Register and edit members.
- Configure cooperative rules.
- Approve sensitive actions.
- View all records.
- Run reports.
- Manage backups/restores.
- Correct or reverse transactions with a reason.
- View audit history.

## 3.2 Treasurer / Finance Officer

Can:

- Record savings.
- Record shares.
- Record loan collections/disbursements.
- Record loan repayments.
- Record approved withdrawals.
- View financial reports.

Should not be able to silently delete or alter historical financial transactions.

## 3.3 Secretary

Can:

- Register members.
- Update permitted member information.
- Record Friday attendance.
- Record meeting minutes.
- View member records.
- Print member information and statements.

Permissions should be configurable because actual duties may differ.

---

# 4. Main Application Structure

The home screen should contain only the most important actions.

```text
ORISUN IBUKUN
Owode Unit

[ MEMBERS ]        [ ATTENDANCE ]

[ SAVINGS ]        [ LOANS ]

[ TRANSACTIONS ]   [ REPORTS ]

[ MEETINGS ]       [ BACKUP ]

[ SETTINGS ]
```

A global search should be available from the top of the application:

```text
Search member by:
[ Member ID / Name / Phone ]
```

Searching a member should lead directly to that member's profile.

---

# 5. Member Profile

Each member gets one permanent profile.

## 5.1 Identity and membership information

Recommended fields:

- Member ID
- Full name
- Phone number
- Address
- Date of joining
- Membership status
- Date membership ended
- Reason for ending membership
- Registration/entrance fee
- Share ownership
- Notes

Personal data should be limited to information the cooperative actually needs.

## 5.2 Membership status

Suggested states:

- Active
- Suspended
- Exited

A member who exits remains searchable historically. Historical savings, loans, attendance and transactions must not be deleted merely because membership ended.

---

# 6. Unified Member Financial View

The member profile should have a clear summary at the top.

```text
MEMBER
CHUKWU OKAFOR

ID: ORI-00231
Status: ACTIVE
Joined: 14/03/2022

--------------------------------
TOTAL PAID         ₦450,000
TOTAL OWED          ₦84,000
TOTAL REMAINING     ₦84,000
SHARES             ₦120,000
SAVINGS            ₦450,000
ACTIVE LOAN        ₦250,000
LOAN PAID          ₦166,000
--------------------------------
```

The displayed figures should be calculated by the application from the underlying records. Labels such as **amount owed** and **amount remaining** should be configured to match the cooperative's actual terminology and loan rules.

---

# 7. Virtual Savings Booklet

This is a core feature.

The digital booklet should imitate the simplicity of a physical cooperative savings book.

```text
ORISUN IBUKUN – OWODE UNIT
MEMBER: CHUKWU OKAFOR
ID: ORI-00231

DATE       MINUTES   SHARE   SAVINGS   REPAYMENT   LOAN   BALANCE
07/08/26   241       ₦2,000  ₦10,000   ₦0          ₦0     ₦...
14/08/26   242       ₦0      ₦10,000   ₦15,000     ₦0     ₦...
21/08/26   243       ₦0      ₦5,000    ₦10,000     ₦0     ₦...
```

Possible transaction columns/categories:

- Date
- Meeting/minutes reference
- Share contribution
- Savings
- Loan repayment
- Loan collection/disbursement
- Withdrawal
- Fines/charges
- Other approved transaction
- Running balance

The exact display can be adjusted when real historical records become available.

### Important terminology

A **loan collection/disbursement** is money paid out to the member as a loan.

A **loan repayment** is money paid back by the member.

These must remain separate transaction types.

The booklet should be accessible from the member profile and should reflect the same source records used by reports, so there is one consistent financial history everywhere.

---

# 8. Transaction System

All money movement should pass through one controlled transaction engine.

Transaction types may include:

- Share contribution
- Savings contribution
- Loan collection/disbursement
- Loan repayment
- Withdrawal
- Fine
- Fee
- Refund
- Dividend
- Adjustment
- Headquarters remittance
- Other configured transaction types

Every transaction should have:

- Unique transaction ID
- Date
- Meeting/minutes reference where applicable
- Member reference where applicable
- Transaction type
- Amount
- Payment method if needed
- Entered by
- Date/time entered
- Status
- Description where needed
- Reversal/reference information if corrected

---

# 9. Friday Attendance

Because the cooperative meets every Friday, attendance should be a first-class feature.

## 9.1 Attendance screen

```text
FRIDAY ATTENDANCE
Friday, 11 September 2026

Member                Status

1. Chukwu Okafor       ✓
2. Adaobi Eze          X
3. Emeka Nwosu         ✓
4. Ngozi Obi           ✓
5. Ifeanyi Okoro       X
```

Visual requirements:

- Present = large tick **✓**.
- Absent = large red **X**.
- Large click/touch target.
- Simple one-action toggle.
- No tiny checkbox as the primary interaction.

The application should remember the meeting date and prevent duplicate attendance records for the same member/date unless an authorized user reopens the record.

If absence attracts a fine or affects any cooperative benefit, that rule should be configurable rather than assumed.

---

# 10. Meetings and Minutes

Each Friday meeting should have a meeting record.

Recommended fields:

- Meeting ID
- Date
- Meeting/minutes number
- Attendance
- Meeting notes
- Decisions/resolutions
- Financial totals for that meeting

Transactions recorded during a meeting can reference that meeting/minutes number.

Example:

```text
Transaction:
₦10,000 Savings

Meeting:
Minutes No. 243
Friday, 21 August 2026
```

This allows the member booklet and financial records to trace transactions back to the meeting where they occurred.

---

# 11. Loans

Loans require stronger controls than ordinary savings.

Each loan should have a permanent loan record.

Recommended fields:

- Loan ID
- Member ID
- Application date
- Approval date
- Disbursement date
- Principal amount
- Interest rate / interest amount
- Processing fee if applicable
- Other approved charges
- Total repayable
- Repayment frequency
- Expected repayment amount
- Start date
- Due date / maturity date
- Outstanding principal
- Outstanding interest/charges
- Loan status
- Guarantors
- Approval notes

Suggested loan states:

```text
Applied
Approved
Disbursed
Active
Overdue
Completed
Cancelled
Written Off
```

Actual states and formulas must be configured to match ORISUN IBUKUN's rules.

---

# 12. Guarantors

A loan should be able to reference one or more guarantors.

Recommended information:

- Guarantor member ID
- Name
- Guarantee amount
- Date of guarantee
- Guarantee status

The system should validate guarantor eligibility where cooperative rules define eligibility or exposure limits.

The number of guarantors should be configurable.

---

# 13. Monthly Calculations and Metrics

Administrators need a monthly management view showing money coming in, money going out and headquarters remittances.

Example:

```text
SEPTEMBER 2026

MONEY IN
Savings received        ₦850,000
Shares received         ₦120,000
Loan repayments         ₦540,000
Other income             ₦35,000
--------------------------------
TOTAL IN              ₦1,545,000

MONEY OUT
Loans disbursed         ₦700,000
Withdrawals             ₦180,000
Expenses                 ₦95,000
Headquarters remittance ₦400,000
--------------------------------
TOTAL OUT             ₦1,375,000

NET CASH MOVEMENT       ₦170,000
```

The real categories and definitions should be configured to the cooperative's accounting practice.

Use neutral terms such as **money in**, **money out**, **net cash movement**, **loans disbursed**, **repayments received**, and **remitted to headquarters** unless the cooperative's accounting policy explicitly defines a formal profit figure.

---

# 14. Headquarters Remittance

Because the unit remits money to headquarters, remittance should have its own record.

Recommended fields:

- Remittance ID
- Date
- Period covered
- Amount
- Destination/headquarters
- Payment method
- Reference number
- Person who prepared it
- Person who approved it
- Notes

Monthly reports should answer:

- How much was remitted to headquarters this month?
- When was it remitted?
- What reference was used?
- Who prepared and approved it?

The system should only automatically calculate **amount due for remittance** once the exact headquarters remittance formula is established.

---

# 15. Monthly Reporting

Recommended report presets:

1. Monthly money-in / money-out report
2. Monthly savings collection report
3. Monthly loan disbursement report
4. Monthly loan repayment report
5. Outstanding loans report
6. Member savings statement
7. Member loan statement
8. Attendance report
9. Share register
10. Headquarters remittance report
11. Expense report
12. Transaction/audit report

Reports should support:

- On-screen viewing
- Printing
- PDF export
- CSV/Excel export where useful

All exports should be generated locally.

---

# 16. Database Model

A relational local database is recommended.

SQLite is a strong first-version candidate for an offline desktop application because it is self-contained and does not require a database server installation.

Conceptual relationships:

```text
Member
 ├── Shares
 ├── Savings Transactions
 ├── Loans
 │    ├── Guarantors
 │    └── Loan Repayments
 ├── Attendance
 ├── Meetings/Minutes
 └── General Transactions

Meeting
 ├── Attendance
 ├── Minutes
 └── Transactions

Loan
 ├── Member
 ├── Guarantors
 └── Repayments

Transaction
 ├── Member
 ├── Meeting
 └── User

Headquarters Remittance
 └── User / Approval

User
 └── Audit Log
```

---

# 17. Data Integrity Rules

The software should enforce rules instead of relying on operator memory.

Examples:

### Member

- Member ID must be unique.
- A member cannot have two active profiles with the same ID.
- Exiting a member does not erase history.

### Attendance

- One attendance record per member per meeting.
- Changes after meeting closure require authorization.

### Savings

- Amount must be valid.
- Transaction must have a date.
- Posted transactions cannot be silently removed.

### Loans

- Loan must belong to an existing member.
- Repayment cannot exceed permitted outstanding balance without an approved adjustment process.
- Completed loans cannot continue receiving ordinary repayments.
- Guarantors must be valid members where required.

### Transactions

- Every posted transaction receives a unique ID.
- Posted transactions are immutable to normal users.
- Corrections require a reason and audit record.

---

# 18. Correction and Reversal Logic

Never use a simple “Edit Amount” workflow for posted financial transactions.

Example:

```text
Original Transaction
₦50,000
        ↓
Reversal
-₦50,000
        ↓
Correct Transaction
₦5,000
```

The audit trail should record:

- Who corrected it.
- When.
- Why.
- Original transaction.
- Reversal transaction.
- Replacement transaction.

This protects the cooperative in audits and member disputes.

---

# 19. Backup and Recovery

Because the application is offline, backup is a critical feature.

## Recommended strategy

Maintain multiple local backup generations.

```text
Backups
├── Today
├── Yesterday
├── Weekly
└── Monthly
```

The application should display:

```text
LAST BACKUP
Today, 4:15 PM ✓

[ BACK UP NOW ]
```

It should warn when backups are overdue.

## Backup destinations

At minimum:

- Local backup folder
- External USB drive

A later version may support a second approved computer or local network backup.

## Restore

```text
RESTORE DATA

○ Today – 4:15 PM
○ Yesterday – 5:02 PM
○ 01 Sep – Monthly

[ RESTORE ]
```

Restoration should require administrator authorization and create a safety backup of the current database before replacing it.

---

# 20. Backward Compatibility and Database Migration

The application must expect future software versions.

Every database should have a schema version.

Example:

```text
Database v1
     ↓ migration
Database v2
     ↓ migration
Database v3
```

The application should migrate old data automatically where possible.

It must never require the cooperative to recreate years of member records after an upgrade.

Historical transaction IDs and dates should be retained wherever possible.

---

# 21. Importing Existing/Old Records

Because current paper/Excel documentation is unavailable at present, the first release should still include a controlled path for historical data entry/import.

Potential source formats:

- CSV
- Excel
- Structured manual entry
- Future scanned-document assistance

Migration process:

```text
OLD RECORDS
     ↓
IMPORT / ENTRY
     ↓
VALIDATE
     ↓
SHOW ERRORS
     ↓
ADMIN CONFIRMS
     ↓
FINALIZE
```

Historical records should be tagged as imported/legacy data.

The system should never assume that an unknown old value equals zero.

---

# 22. Security

The application should have local user accounts and role-based permissions.

Recommended:

- Username
- PIN/password
- Role
- Active/inactive status
- Last login
- Audit activity

Sensitive actions should require appropriate authorization.

Examples:

- Restore database
- Reverse posted financial transaction
- Change cooperative configuration
- Disable a user
- Close/reopen a meeting
- Modify historical records

Because the application is offline, security must not depend on a cloud login.

---

# 23. Audit Log

Important actions should generate an audit record.

Example:

```text
07/09/2026  10:32
Treasurer recorded ₦20,000 savings
Member: ORI-00231

07/09/2026  10:41
Administrator reversed TX-000841
Reason: Duplicate entry

07/09/2026  11:05
Administrator restored backup B-20260906-1700
```

Audit records should not be editable by ordinary users.

---

# 24. User Experience Rules

### Rule 1 — One main action per screen

Do not present many competing actions when the operator is recording savings.

### Rule 2 — Large controls

Buttons should be easy to click on an ordinary office computer.

### Rule 3 — Plain language

Use:

- Add Member
- Record Savings
- Record Repayment
- Give Loan
- Take Attendance
- View Statement

Avoid:

- Create Entity
- Post Ledger
- Execute Disbursement

### Rule 4 — Explain errors

Bad:

> Error 422: Validation failed.

Good:

> Please enter the amount before saving.

### Rule 5 — Confirm important actions

Example:

> Record ₦50,000 savings for Chukwu Okafor?

[ CANCEL ] [ YES, RECORD ]

### Rule 6 — Do not overuse confirmation

Routine navigation should remain fast.

### Rule 7 — Show success clearly

Example:

> Savings recorded successfully.

Then show the resulting balance.

---

# 25. Accessibility and Operating Environment

Assume:

- Low to medium computer literacy.
- Windows desktop/laptop.
- Modest hardware.
- Mouse and keyboard.
- Possibly small or low-resolution displays.
- Electricity interruptions are possible.

Therefore:

- Application should start quickly.
- Avoid resource-heavy graphics.
- Save safely and frequently.
- Avoid animations that provide no functional benefit.
- Support keyboard navigation.
- Use readable fonts and strong contrast.
- Never depend on continuous connectivity.
- Recover gracefully after unexpected shutdowns.

The blue-and-white brand should be applied primarily to headers, buttons, highlights and identity—not as decoration on every screen.

---

# 26. Power Failure and Crash Protection

Financial entries should be committed atomically.

A transaction should either:

```text
SUCCESS → fully saved
```

or:

```text
FAILURE → not partially saved
```

The system should never leave half-completed financial entries after a shutdown.

The database should use safe transactional writes and recovery mechanisms supported by the chosen database technology.

---

# 27. Printing

Printing is important because cooperative administration may still require paper records.

Useful printouts:

- Member savings booklet/statement
- Loan statement
- Receipt
- Attendance sheet
- Monthly report
- Headquarters remittance report
- Member register

Printed reports should include:

- ORISUN IBUKUN – Owode Unit
- Report type
- Date/period
- Page number where appropriate
- Generated by
- Generated date

---

# 28. Proposed Application Navigation

A member of staff should be able to perform common work in three or fewer major steps.

### Record Savings

```text
Home
  ↓
Savings
  ↓
Search Member
  ↓
Enter Amount
  ↓
Confirm
```

### Attendance

```text
Home
  ↓
Attendance
  ↓
Friday Meeting
  ↓
Tick ✓ / Mark X
  ↓
Save
```

### View Member

```text
Home
  ↓
Search
  ↓
Member
  ↓
Profile
```

### Record Loan Repayment

```text
Home
  ↓
Repayments
  ↓
Search Member
  ↓
Select Active Loan
  ↓
Enter Amount
  ↓
Confirm
```

---

# 29. Dashboard Philosophy

The dashboard should not become a wall of charts.

Use important numbers only.

Example:

```text
THIS MONTH

Members                  428
Present this Friday      351
Savings received      ₦850k
Loans disbursed        ₦700k
Repayments received    ₦540k
Remitted to HQ         ₦400k
Outstanding loans    ₦3.2m
```

The administrator can click a figure to see its supporting records.

The dashboard is therefore a summary, not the accounting system itself.

---

# 30. Configuration and Scalability

Cooperative rules should be configurable wherever practical.

Examples:

- Minimum savings.
- Share price.
- Loan interest method.
- Maximum loan multiplier.
- Required guarantors.
- Repayment frequency.
- Penalty rules.
- Meeting day.
- Remittance rules.
- Transaction categories.

Do not hard-code assumptions that may later change.

Advanced settings should be hidden from ordinary users.

---

# 31. Future Scalability

The architecture should allow future features without redesigning the entire data model.

Possible future features:

- Multiple cooperative units.
- Multi-branch management.
- Local-network synchronization.
- Controlled synchronization between Owode Unit and headquarters.
- SMS/notification integrations when connectivity is introduced.
- Mobile companion application.
- QR/member-card identification.
- Advanced financial statements.
- Headquarters consolidation.

These should not complicate the first release.

---

# 32. Suggested Technology Direction

For the first offline desktop release:

### Database

**SQLite** is a strong candidate.

### Application

A Windows-first desktop framework should be selected based on printer support, deployment simplicity, local maintenance capability and developer familiarity. Suitable families include:

- C# / .NET desktop
- Python with an appropriate desktop UI framework
- Tauri/Electron where web technology provides a clear maintenance advantage

The application should feel native and remain lightweight.

---

# 33. Initial Database Tables

A starting schema could include:

```text
users
roles
members
member_status_history
meetings
attendance
transactions
transaction_reversals
shares
loans
loan_guarantors
loan_repayments
expenses
headquarters_remittances
member_notes
minutes
audit_logs
backups
settings
schema_migrations
```

The final schema may consolidate or split tables after the exact rules are known.

---

# 34. Business Rules Still to Confirm

The application should be built so the following decisions can be supplied later without major redesign.

### Membership

- Entrance fee.
- Share price.
- Maximum share ownership, if any.
- Minimum savings requirement.
- Exit procedure and settlement rules.

### Savings

- Withdrawal rules.
- Minimum balance.
- Treatment of savings at exit.

### Loans

- Maximum loan amount.
- Interest method.
- Interest rate.
- Repayment schedule.
- Guarantor count and exposure limits.
- Late-payment penalties.
- Restructuring rules.
- Default/write-off rules.

### Attendance

- Absence fine, if any.
- Approved reasons.
- Whether attendance affects eligibility or dividends.

### Dividends

- Whether dividends are based on shares, savings, surplus/profit or another formula.

### Headquarters

- What is remitted.
- When it is remitted.
- Whether a fixed amount or formula is used.

These must become explicit configuration/business rules before financial calculations are finalized.

---

# 35. Version 1 — Recommended Scope

The first release should concentrate on the operational core:

```text
1. Login & permissions
2. Member registration
3. Member search
4. Member profile
5. Friday attendance
6. Meeting/minutes records
7. Savings
8. Shares
9. Loans
10. Loan repayments
11. Guarantors
12. Member virtual booklet
13. Transactions
14. Monthly dashboard
15. Headquarters remittance
16. Reports & printing
17. Audit log
18. Backup / restore
19. Database migration/versioning
```

Avoid adding decorative or non-essential features until these are stable.

---

# 36. Acceptance Criteria

The first version should be considered successful when an ordinary cooperative officer can:

1. Register a member without technical assistance.
2. Find an existing member quickly.
3. Mark Friday attendance with one click.
4. Record savings without manually calculating balances.
5. Record a loan and its guarantors.
6. Record a repayment and see the new outstanding balance.
7. Open a member and see their complete financial history.
8. View/print the member's virtual booklet or statement.
9. View monthly money-in and money-out.
10. See headquarters remittance totals.
11. Correct a financial mistake without destroying history.
12. Backup the database without touching database files.
13. Restore a previous backup through the application.
14. Upgrade the application without losing historical records.

---

# 37. Recommended Development Order

The project should be developed in this order:

```text
PHASE 1
Business rules
       ↓
PHASE 2
Database model
       ↓
PHASE 3
Core transaction engine
       ↓
PHASE 4
Member management
       ↓
PHASE 5
Savings / shares / booklet
       ↓
PHASE 6
Loans / guarantors / repayments
       ↓
PHASE 7
Attendance / meetings / minutes
       ↓
PHASE 8
Reports / remittances
       ↓
PHASE 9
Security / audit
       ↓
PHASE 10
Backup / restore / migration
       ↓
PHASE 11
Usability testing with a non-technical operator
```

The business rules and transaction engine should be stabilized before the UI is considered finished.

---

# 38. Overall Product Definition

**ORISUN IBUKUN – Owode Unit** should become a dependable digital cooperative register that preserves the familiarity of the existing cooperative process while removing the weaknesses of paper:

- Difficult searching
- Arithmetic errors
- Lost records
- Repeated writing
- Unclear balances
- Weak audit trails
- Difficult monthly reporting
- Difficult historical retrieval

The application should feel simple enough for a non-technical operator to learn quickly, while the underlying system is robust enough to maintain many years of membership and financial history.

> **Simple interface. Strong records. Clear history. Safe money.**
