"""Application constants for ORISUN IBUKUN."""

# Transaction Types
TXN_SAVINGS = "Savings"
TXN_SHARE_CONTRIBUTION = "Share Contribution"
TXN_LOAN_DISBURSEMENT = "Loan Disbursement"
TXN_LOAN_REPAYMENT = "Loan Repayment"
TXN_WITHDRAWAL = "Withdrawal"
TXN_EXPENSE = "Expense"
TXN_ENTRANCE_FEE = "Entrance Fee"
TXN_CHARGE_PAYMENT = "Charge Payment"
TXN_MINUTES = "Minutes"
TXN_OTHER = "Other"
TXN_HQ_FUNDING = "Headquarters Funding"

# Transaction Status
TXN_STATUS_POSTED = "Posted"
TXN_STATUS_REVERSED = "Reversed"

# Member Status
MEMBER_STATUS_ACTIVE = "Active"
MEMBER_STATUS_SUSPENDED = "Suspended"
MEMBER_STATUS_ABSCONDED = "Absconded"
MEMBER_STATUS_INACTIVE = "Inactive"
MEMBER_STATUS_EXITED = "Exited"

MEMBER_STATUSES = (
    MEMBER_STATUS_ACTIVE,
    MEMBER_STATUS_SUSPENDED,
    MEMBER_STATUS_ABSCONDED,
    MEMBER_STATUS_INACTIVE,
    MEMBER_STATUS_EXITED,
)

# Loan Status
LOAN_STATUS_APPLIED = "Applied"
LOAN_STATUS_APPROVED = "Approved"
LOAN_STATUS_DISBURSED = "Disbursed"
LOAN_STATUS_ACTIVE = "Active"
LOAN_STATUS_OVERDUE = "Overdue"
LOAN_STATUS_COMPLETED = "Completed"

LOAN_ACTIVE_STATUSES = (LOAN_STATUS_DISBURSED, LOAN_STATUS_ACTIVE, LOAN_STATUS_OVERDUE)

# Attendance Status
ATTENDANCE_PRESENT = "Present"
ATTENDANCE_ABSENT = "Absent"

# Backup Types
BACKUP_MANUAL = "Manual"
BACKUP_AUTO = "Automatic"

# Member Charge Types
CHARGE_ABSENCE_FINE = "Absence Fine"
CHARGE_MINUTES_LEVY = "Minutes Levy"
CHARGE_ICT = "ICT"
CHARGE_AGM = "AGM"
CHARGE_ABSENTISM = "Absentism"
CHARGE_OTHER = "Other"

CHARGE_STATUS_OWED = "Owed"
CHARGE_STATUS_PARTIAL = "Partial"
CHARGE_STATUS_PAID = "Paid"

# Standard fee columns shown in passbook (order matters for display)
PASSBOOK_FEE_COLUMNS = [
    ("minutes", "Minutes", CHARGE_MINUTES_LEVY),
    ("ict", "ICT", CHARGE_ICT),
    ("agm", "AGM", CHARGE_AGM),
    ("absentism", "Absentism", CHARGE_ABSENTISM),
    ("fines", "Fines", CHARGE_ABSENCE_FINE),
]

# Roles
ROLE_ADMINISTRATOR = "Administrator"
ROLE_TREASURER = "Treasurer"
ROLE_SECRETARY = "Secretary"

# Default Settings Keys
SETTING_APP_NAME = "app_name"
SETTING_UNIT_NAME = "unit_name"
SETTING_CURRENCY = "currency"
SETTING_MEETING_DAY = "meeting_day"
SETTING_SHARE_PRICE = "share_price"
SETTING_ENTRANCE_FEE = "entrance_fee"
SETTING_MIN_SAVINGS_WITHDRAWAL = "min_savings_withdrawal"
SETTING_MAX_LOAN_MULTIPLIER = "max_loan_multiplier"
SETTING_REQUIRED_GUARANTORS = "required_guarantors"
SETTING_INTEREST_RATE = "interest_rate"
SETTING_INTEREST_METHOD = "interest_method"
SETTING_SCHEMA_VERSION = "schema_version"

# Interest Methods
INTEREST_METHOD_FLAT = "Flat"
INTEREST_METHOD_REDUCING = "Reducing"

# Repayment Frequencies
REPAY_MONTHLY = "Monthly"
REPAY_WEEKLY = "Weekly"

# Database
DB_NAME = "orisun_ibukun.db"
BACKUP_DIR_NAME = "backups"

# App Version & Update (hardcoded — not user-editable)
APP_VERSION = "1.2.9"
GITHUB_REPO = "James212-lab/OrisunIbukun"