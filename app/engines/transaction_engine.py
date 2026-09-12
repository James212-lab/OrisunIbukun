"""Core transaction engine — all financial operations go through here."""
import datetime
from database.connection import get_connection
from utils.helpers import generate_id
from permissions import require_permission, PERM_REVERSE_TXN, PERM_SETTINGS_EDIT
from constants import (
    TXN_STATUS_POSTED,
    TXN_STATUS_REVERSED,
    TXN_SAVINGS,
    TXN_SHARE_CONTRIBUTION,
    TXN_LOAN_DISBURSEMENT,
    TXN_LOAN_REPAYMENT,
    TXN_ENTRANCE_FEE,
    TXN_CHARGE_PAYMENT,
    TXN_WITHDRAWAL,
    TXN_OTHER,
    CHARGE_ABSENCE_FINE,
    CHARGE_MINUTES_LEVY,
    CHARGE_ICT,
    CHARGE_AGM,
    CHARGE_LATENESS,
    CHARGE_ABSENTISM,
    CHARGE_OTHER,
    CHARGE_STATUS_OWED,
    CHARGE_STATUS_PARTIAL,
    CHARGE_STATUS_PAID,
    PASSBOOK_FEE_COLUMNS,
    MEMBER_STATUS_ACTIVE,
    LOAN_STATUS_DISBURSED,
    LOAN_STATUS_ACTIVE,
    LOAN_STATUS_OVERDUE,
    LOAN_STATUS_APPLIED,
    LOAN_STATUS_APPROVED,
    LOAN_STATUS_COMPLETED,
)


def _next_member_id() -> str:
    conn = get_connection()
    cur = conn.execute("SELECT COUNT(*) as cnt FROM members")
    count = cur.fetchone()["cnt"] + 1
    return f"ORI-{count:05d}"


def _next_meeting_number() -> int:
    conn = get_connection()
    cur = conn.execute("SELECT COALESCE(MAX(meeting_number), 0) as mx FROM meetings")
    return cur.fetchone()["mx"] + 1


EARLIEST_ENTRY_DATE = "2015-01-01"


def resolve_entry_date(date_str: str | None, allow_backdate: bool = False) -> str:
    """Validate and normalize a record date.

    Empty/None means today. Backdated entries (any date before today, back
    to 2015) require allow_backdate=True (administrators only). Future
    dates are always rejected.
    """
    today = datetime.date.today().isoformat()
    date_str = (date_str or "").strip() or today
    try:
        parsed = datetime.date.fromisoformat(date_str)
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format.")
    if date_str > today:
        raise ValueError("Date cannot be in the future.")
    if date_str < EARLIEST_ENTRY_DATE:
        raise ValueError(f"Date cannot be earlier than {EARLIEST_ENTRY_DATE}.")
    if date_str < today and not allow_backdate:
        raise PermissionError("Only administrators can enter backdated records.")
    return date_str


def record_transaction(
    conn,
    member_id: int | None,
    transaction_type: str,
    amount: float,
    meeting_id: int | None = None,
    payment_method: str | None = None,
    description: str | None = None,
    entered_by: int | None = None,
    date: str | None = None,
) -> str:
    txn_id = generate_id("TX")
    # Callers pass dates already validated by resolve_entry_date.
    date = date or datetime.date.today().isoformat()
    conn.execute(
        """INSERT INTO transactions
           (transaction_id, date, meeting_id, member_id, transaction_type,
            amount, payment_method, description, status, entered_by)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (txn_id, date, meeting_id, member_id, transaction_type, amount,
         payment_method, description, TXN_STATUS_POSTED, entered_by),
    )
    return txn_id


def register_member(full_name: str, phone: str = "", address: str = "",
                    entrance_fee: float = 0, date_joined: str = None,
                    entered_by: int = None, dob: str = "", gender: str = "",
                    occupation: str = "", email: str = "",
                    next_of_kin: str = "", next_of_kin_phone: str = "",
                    id_type: str = "", id_number: str = "",
                    photo_path: str = "", allow_backdate: bool = False) -> dict:
    conn = get_connection()
    date_joined = resolve_entry_date(date_joined, allow_backdate)
    member_id = _next_member_id()

    with conn:
        txn_id = record_transaction(
            conn, None, TXN_ENTRANCE_FEE, entrance_fee,
            description=f"Entrance fee for {full_name}",
            entered_by=entered_by, date=date_joined,
        )
        conn.execute(
            """INSERT INTO members (member_id, full_name, phone, address,
               date_joined, entrance_fee, status, dob, gender, occupation,
               email, next_of_kin, next_of_kin_phone, id_type, id_number,
               photo_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (member_id, full_name, phone, address, date_joined, entrance_fee,
             MEMBER_STATUS_ACTIVE, dob, gender, occupation, email,
             next_of_kin, next_of_kin_phone, id_type, id_number, photo_path),
        )
        cur = conn.execute("SELECT last_insert_rowid() as id")
        row_id = cur.fetchone()["id"]

    return {"id": row_id, "member_id": member_id, "full_name": full_name}


def update_member_details(member_db_id: int, entered_by: int = None,
                          **fields) -> None:
    """Update a member's personal/KYC details (correction of mistakes).

    Allowed fields: full_name, phone, address, dob, gender, occupation,
    email, next_of_kin, next_of_kin_phone, id_type, id_number, photo_path,
    status, notes. Status changes are recorded in the audit log.
    """
    allowed = {"full_name", "phone", "address", "dob", "gender",
               "occupation", "email", "next_of_kin", "next_of_kin_phone",
               "id_type", "id_number", "photo_path", "status", "notes"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    if "full_name" in updates and not (updates["full_name"] or "").strip():
        raise ValueError("Full Name is required.")
    conn = get_connection()
    with conn:
        old = conn.execute("SELECT * FROM members WHERE id = ?",
                           (member_db_id,)).fetchone()
        if not old:
            raise ValueError("Member not found.")
        cols = [r[1] for r in conn.execute("PRAGMA table_info(members)").fetchall()]
        sets, params = [], []
        for k, v in updates.items():
            if k in cols:
                sets.append(f"[{k}] = ?")
                params.append(v)
        if sets:
            params.append(member_db_id)
            conn.execute(f"UPDATE members SET {', '.join(sets)} WHERE id = ?",
                         params)
        if "status" in updates and old["status"] != updates["status"]:
            conn.execute(
                """INSERT INTO audit_logs (user_id, action, details)
                   VALUES (?, ?, ?)""",
                (entered_by, "Member Status Change",
                 f"{old['full_name']} ({old['member_id']}): {old['status']} -> {updates['status']}"),
            )


def record_savings(member_db_id: int, amount: float, meeting_id: int = None,
                   payment_method: str = "Cash", entered_by: int = None,
                   date: str = None, txn_type: str = "Savings",
                   allow_backdate: bool = False) -> str:
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    conn = get_connection()
    date = resolve_entry_date(date, allow_backdate)
    with conn:
        txn_id = record_transaction(
            conn, member_db_id, txn_type, amount, meeting_id,
            payment_method, entered_by=entered_by, date=date,
        )
        conn.execute(
            """INSERT INTO savings (member_id, transaction_id, type, amount, balance_after)
               SELECT ?, ?, ?, ?,
                      COALESCE((SELECT SUM(amount) FROM savings WHERE member_id = ?), 0) + ?""",
            (member_db_id, txn_id, txn_type, amount, member_db_id, amount),
        )
    return txn_id


def record_share(member_db_id: int, shares: float, value_per_share: float,
                 meeting_id: int = None, entered_by: int = None,
                 date: str = None, allow_backdate: bool = False,
                 exact_amount: float | None = None,
                 payment_method: str = "Cash") -> str:
    raise ValueError("Share contributions are discontinued.")


def create_loan(member_db_id: int, principal: float, interest_rate: float = 0,
                processing_fee: float = 0, other_charges: float = 0,
                repayment_frequency: str = "Monthly", entered_by: int = None,
                date: str = None, allow_backdate: bool = False) -> str:
    conn = get_connection()
    date = resolve_entry_date(date, allow_backdate)
    loan_id = generate_id("LN")
    interest_amount = principal * interest_rate / 100 if interest_rate else 0
    total_repayable = principal + interest_amount

    loan_id_num = None
    with conn:
        cur = conn.execute(
            """INSERT INTO loans
               (loan_id, member_id, application_date, principal_amount,
                interest_rate, interest_amount, processing_fee, other_charges,
                total_repayable, outstanding_principal, outstanding_interest,
                repayment_frequency, status, created_by)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (loan_id, member_db_id, date, principal, interest_rate,
             interest_amount, processing_fee, other_charges, total_repayable,
             principal, interest_amount, repayment_frequency, LOAN_STATUS_APPLIED, entered_by),
        )
        loan_id_num = cur.lastrowid
    return loan_id


def _resolve_loan(loan_ref):
    """Look up a loan row by loan_id string or DB row id."""
    conn = get_connection()
    cur = conn.execute("SELECT * FROM loans WHERE loan_id = ? OR id = ?", (loan_ref, loan_ref))
    loan = cur.fetchone()
    if not loan:
        raise ValueError("Loan not found: {}".format(loan_ref))
    return loan, conn


def approve_loan(loan_db_id: int, approved_by: int = None, notes: str = ""):
    loan, conn = _resolve_loan(loan_db_id)
    with conn:
        conn.execute(
            "UPDATE loans SET status = ?, approval_date = datetime('now'), approval_notes = ? WHERE id = ?",
            (LOAN_STATUS_APPROVED, notes, loan["id"]),
        )


def disburse_loan(loan_db_id: int, member_db_id: int, entered_by: int = None,
                   meeting_id: int = None, date: str = None,
                   allow_backdate: bool = False) -> str:
    loan, conn = _resolve_loan(loan_db_id)
    date = resolve_entry_date(date, allow_backdate)
    if loan["status"] != LOAN_STATUS_APPROVED:
        raise ValueError(
            f"Loan must be Approved before disbursement (is {loan['status']}).")
    with conn:
        txn_id = record_transaction(
            conn, member_db_id, TXN_LOAN_DISBURSEMENT, loan["principal_amount"],
            meeting_id, entered_by=entered_by, date=date,
        )
        conn.execute(
            "UPDATE loans SET status = ?, disbursement_date = ? WHERE id = ?",
            (LOAN_STATUS_DISBURSED, date, loan["id"]),
        )
        processing_fee = loan["processing_fee"] or 0
        other_charges = loan["other_charges"] or 0
        if processing_fee > 0:
            record_transaction(
                conn, member_db_id, TXN_OTHER, processing_fee,
                meeting_id, "Cash",
                description="Loan Processing Fee",
                entered_by=entered_by, date=date,
            )
        if other_charges > 0:
            record_transaction(
                conn, member_db_id, TXN_OTHER, other_charges,
                meeting_id, "Cash",
                description="Other Loan Charges",
                entered_by=entered_by, date=date,
            )
    return txn_id


def record_repayment(loan_db_id: int, amount: float, member_db_id: int,
                      meeting_id: int = None, entered_by: int = None,
                      date: str = None, allow_backdate: bool = False) -> str:
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    loan, conn = _resolve_loan(loan_db_id)
    date = resolve_entry_date(date, allow_backdate)
    total_out = ((loan["outstanding_principal"] or 0)
                 + (loan["outstanding_interest"] or 0))
    if amount > total_out + 1e-9:
        raise ValueError(
            f"Amount {amount:,.0f} exceeds loan outstanding ({total_out:,.0f}).")
    with conn:
        principal_portion = min(amount, loan["outstanding_principal"])
        interest_portion = amount - principal_portion
        new_principal = loan["outstanding_principal"] - principal_portion
        new_interest = loan["outstanding_interest"] - interest_portion

        txn_id = record_transaction(
            conn, member_db_id, TXN_LOAN_REPAYMENT, amount, meeting_id,
            entered_by=entered_by, date=date,
        )
        conn.execute(
            """INSERT INTO loan_repayments
               (loan_id, transaction_id, amount, principal_portion,
                interest_portion, balance_after)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (loan["id"], txn_id, amount, principal_portion, interest_portion,
             new_principal),
        )
        new_status = LOAN_STATUS_COMPLETED if new_principal <= 0 else LOAN_STATUS_ACTIVE
        conn.execute(
            """UPDATE loans SET outstanding_principal = ?,
               outstanding_interest = ?, status = ? WHERE id = ?""",
            (new_principal, new_interest, new_status, loan["id"]),
        )
    return txn_id


def add_guarantor(loan_db_id: int, guarantor_member_db_id: int,
                  guarantee_amount: float = 0):
    conn = get_connection()
    with conn:
        conn.execute(
            """INSERT INTO loan_guarantors
               (loan_id, guarantor_member_id, guarantee_amount)
               VALUES (?, ?, ?)""",
            (loan_db_id, guarantor_member_db_id, guarantee_amount),
        )


def add_external_guarantor(loan_db_id: int, full_name: str,
                           phone: str = "", address: str = "",
                           id_type: str = "", id_number: str = "",
                           photo_path: str = "", relationship: str = "",
                           guarantee_amount: float = 0):
    conn = get_connection()
    with conn:
        conn.execute(
            """INSERT INTO external_guarantors
               (loan_id, full_name, phone, address, id_type, id_number,
                photo_path, relationship, guarantee_amount)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (loan_db_id, full_name, phone, address, id_type, id_number,
             photo_path, relationship, guarantee_amount),
        )


def get_loan_guarantors(loan_db_id: int) -> dict:
    conn = get_connection()
    members = conn.execute(
        """SELECT lg.*, m.full_name, m.member_id, m.phone
           FROM loan_guarantors lg
           JOIN members m ON lg.guarantor_member_id = m.id
           WHERE lg.loan_id = ?""",
        (loan_db_id,),
    ).fetchall()
    external = conn.execute(
        "SELECT * FROM external_guarantors WHERE loan_id = ?",
        (loan_db_id,),
    ).fetchall()
    return {
        "members": [dict(r) for r in members],
        "external": [dict(r) for r in external],
        "total_count": len(members) + len(external),
    }


def get_member_loans(member_db_id: int) -> list:
    """Return all loans for a member, ordered by most recent first."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT l.*,
                  (SELECT COUNT(*) FROM loan_guarantors lg WHERE lg.loan_id = l.id)
                      as guarantor_count,
                  (SELECT COALESCE(SUM(lr.amount), 0) FROM loan_repayments lr
                   WHERE lr.loan_id = l.id) as total_repaid
           FROM loans l
           WHERE l.member_id = ?
           ORDER BY l.id DESC""",
        (member_db_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def get_all_loan_members(status_filter: str = "All") -> list:
    """Return members who have loans, with aggregated loan info.

    One row per member. If a member has multiple loans, shows the
    most recent loan's status and aggregates outstanding amounts.
    """
    conn = get_connection()
    status_clause = ""
    params = []
    if status_filter and status_filter != "All":
        status_clause = "WHERE l.status = ?"
        params.append(status_filter)

    sql = f"""SELECT m.id as db_id, m.member_id, m.full_name, m.phone,
                     COUNT(DISTINCT l.id) as loan_count,
                     SUM(l.principal_amount) as total_principal,
                     SUM(l.outstanding_principal + l.outstanding_interest)
                         as total_outstanding,
                     (SELECT l2.status FROM loans l2
                      WHERE l2.member_id = m.id
                      ORDER BY l2.id DESC LIMIT 1) as latest_status,
                     (SELECT l2.disbursement_date FROM loans l2
                      WHERE l2.member_id = m.id
                      ORDER BY l2.id DESC LIMIT 1) as latest_disbursement
              FROM members m
              JOIN loans l ON l.member_id = m.id
              {status_clause}
              GROUP BY m.id
              ORDER BY m.full_name"""
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


@require_permission(PERM_REVERSE_TXN)
def reverse_transaction(transaction_id: str, reason: str, reversed_by: int,
                        conn=None):
    own_conn = conn is None
    if own_conn:
        conn = get_connection()
    with conn:
        cur = conn.execute(
            "SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,)
        )
        txn = cur.fetchone()
        if not txn:
            raise ValueError("Transaction not found.")
        if txn["status"] == TXN_STATUS_REVERSED:
            raise ValueError("Transaction is already reversed.")

        txn_type = txn["transaction_type"]
        member_id = txn["member_id"]

        if txn_type in (TXN_SAVINGS, TXN_WITHDRAWAL):
            conn.execute("DELETE FROM savings WHERE transaction_id = ?",
                         (transaction_id,))
        elif txn_type == TXN_LOAN_REPAYMENT:
            repay = conn.execute(
                "SELECT * FROM loan_repayments WHERE transaction_id = ?",
                (transaction_id,)).fetchone()
            if repay:
                conn.execute("DELETE FROM loan_repayments WHERE transaction_id = ?",
                             (transaction_id,))
                conn.execute(
                    """UPDATE loans
                       SET outstanding_principal = outstanding_principal + ?,
                           outstanding_interest = outstanding_interest + ?,
                           status = CASE
                               WHEN outstanding_principal + ? > 0 THEN 'Disbursed'
                               ELSE status END
                       WHERE id = ?""",
                    (repay["principal_portion"], repay["interest_portion"],
                     repay["principal_portion"], repay["loan_id"]),
                )
        elif txn_type == TXN_CHARGE_PAYMENT:
            apps = conn.execute(
                "SELECT charge_id, amount_applied FROM charge_payment_applications WHERE txn_id = ?",
                (transaction_id,)).fetchall()
            for app in apps:
                conn.execute(
                    """UPDATE member_charges
                       SET amount_paid = MAX(0, amount_paid - ?),
                           status = CASE
                               WHEN MAX(0, amount_paid - ?) < 0.01 THEN 'Owed'
                               WHEN MAX(0, amount_paid - ?) < amount - 0.01 THEN 'Partial'
                               ELSE 'Paid' END
                       WHERE charge_id = ?""",
                    (app["amount_applied"], app["amount_applied"],
                     app["amount_applied"], app["charge_id"]),
                )
                charge = conn.execute(
                    "SELECT member_id, meeting_id, charge_type FROM member_charges WHERE charge_id = ?",
                    (app["charge_id"],)).fetchone()
                if charge and charge["charge_type"] == CHARGE_ABSENTISM:
                    conn.execute(
                        """UPDATE absentism_fines
                           SET amount_paid = MAX(0, amount_paid - ?),
                               status = CASE
                                   WHEN MAX(0, amount_paid - ?) < 0.01 THEN 'Owed'
                                   ELSE 'Partial' END
                           WHERE member_id = ? AND meeting_id = ? AND status != 'Paid'
                           ORDER BY created_at ASC LIMIT 1""",
                        (app["amount_applied"], app["amount_applied"],
                         charge["member_id"], charge["meeting_id"]),
                    )
            conn.execute(
                "DELETE FROM charge_payment_applications WHERE txn_id = ?",
                (transaction_id,))
        elif txn_type == TXN_LOAN_DISBURSEMENT:
            conn.execute(
                """UPDATE loans
                   SET status = 'Approved', disbursement_date = NULL
                   WHERE member_id = ? AND disbursement_date = ?
                     AND status = 'Disbursed'""",
                (member_id, txn["date"]),
            )
        elif txn_type == TXN_EXPENSE:
            conn.execute("DELETE FROM expenses WHERE transaction_id = ?",
                         (transaction_id,))

        reversal_id = record_transaction(
            conn, txn["member_id"], f"Reversal: {txn['transaction_type']}",
            -txn["amount"], txn["meeting_id"],
            description=f"Reversal of {transaction_id}: {reason}",
            entered_by=reversed_by,
        )
        conn.execute(
            "UPDATE transactions SET status = ? WHERE transaction_id = ?",
            (TXN_STATUS_REVERSED, transaction_id),
        )
        conn.execute(
            """INSERT INTO transaction_reversals
               (original_transaction_id, reversal_transaction_id, reason, reversed_by)
               VALUES (?, ?, ?, ?)""",
            (transaction_id, reversal_id, reason, reversed_by),
        )
    return reversal_id


def get_member_financial_summary(member_db_id: int) -> dict:
    conn = get_connection()
    cur = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM savings WHERE member_id = ? AND type = 'Savings'",
        (member_db_id,),
    )
    total_savings = cur.fetchone()["total"]

    cur = conn.execute(
        """SELECT COALESCE(SUM(principal_amount), 0) as total,
                  COALESCE(SUM(outstanding_principal), 0) as outstanding
           FROM loans WHERE member_id = ? AND status IN ('Disbursed', 'Active', 'Overdue')""",
        (member_db_id,),
    )
    loan_row = cur.fetchone()
    active_loan = loan_row["total"]
    outstanding = loan_row["outstanding"]

    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total
           FROM loan_repayments lr
           JOIN loans l ON lr.loan_id = l.id
           WHERE l.member_id = ?""",
        (member_db_id,),
    )
    loan_paid = cur.fetchone()["total"]

    charges = {"minutes_owed": 0, "fines_owed": 0, "other_owed": 0,
               "charges_paid": 0}
    try:
        cur = conn.execute(
            """SELECT charge_type,
                      COALESCE(SUM(amount), 0) as billed,
                      COALESCE(SUM(amount_paid), 0) as paid
               FROM member_charges WHERE member_id = ? GROUP BY charge_type""",
            (member_db_id,),
        )
        for crow in cur.fetchall():
            owed = (crow["billed"] or 0) - (crow["paid"] or 0)
            charges["charges_paid"] += crow["paid"] or 0
            if crow["charge_type"] == CHARGE_MINUTES_LEVY:
                charges["minutes_owed"] = owed
            elif crow["charge_type"] == CHARGE_ABSENCE_FINE:
                charges["fines_owed"] = owed
            else:
                charges["other_owed"] += owed
    except Exception:
        pass
    charges["total_owed"] = (charges["minutes_owed"] + charges["fines_owed"]
                             + charges["other_owed"])

    return {
        "total_savings": total_savings,
        "active_loan": active_loan,
        "outstanding": outstanding,
        "loan_paid": loan_paid,
        "total_paid": total_savings + loan_paid,
        **charges,
    }


def create_meeting(date: str = None, notes: str = "", created_by: int = None,
                     allow_backdate: bool = False) -> int:
    conn = get_connection()
    date = resolve_entry_date(date, allow_backdate)
    meeting_num = _next_meeting_number()
    with conn:
        cur = conn.execute(
            """INSERT INTO meetings (meeting_number, date, notes, created_by)
               VALUES (?, ?, ?, ?)""",
            (meeting_num, date, notes, created_by),
        )
        return cur.lastrowid


def record_attendance(meeting_id: int, member_db_id: int, status: str = "Present",
                      recorded_by: int = None):
    conn = get_connection()
    with conn:
        conn.execute(
            """INSERT OR REPLACE INTO attendance
               (meeting_id, member_id, status, recorded_by)
               VALUES (?, ?, ?, ?)""",
            (meeting_id, member_db_id, status, recorded_by),
        )


def _create_charge(conn, member_db_id: int, charge_type: str, amount: float,
                   meeting_id: int = None, description: str = "",
                   entered_by: int = None) -> str:
    """Create a member charge (fine/levy/other). Idempotent per meeting+type."""
    if meeting_id is not None:
        cur = conn.execute(
            """SELECT id FROM member_charges
               WHERE member_id = ? AND meeting_id = ? AND charge_type = ?""",
            (member_db_id, meeting_id, charge_type),
        )
        if cur.fetchone():
            return ""
    charge_id = generate_id("CH")
    conn.execute(
        """INSERT INTO member_charges
           (charge_id, member_id, meeting_id, charge_type, description,
            amount, amount_paid, status, created_by)
           VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?)""",
        (charge_id, member_db_id, meeting_id, charge_type, description,
         amount, CHARGE_STATUS_OWED, entered_by),
    )
    return charge_id


def apply_absence_fines(meeting_id: int, amount: float,
                        entered_by: int = None) -> int:
    """Charge the absence fine to every member marked Absent for a meeting.

    Returns the number of new charges created (0 if already applied).
    """
    if amount <= 0:
        return 0
    conn = get_connection()
    count = 0
    with conn:
        rows = conn.execute(
            "SELECT member_id FROM attendance WHERE meeting_id = ? AND status = 'Absent'",
            (meeting_id,),
        ).fetchall()
        for r in rows:
            cid = _create_charge(
                conn, r["member_id"], CHARGE_ABSENTISM, amount,
                meeting_id=meeting_id,
                description=f"Absentism fine for meeting #{meeting_id}",
                entered_by=entered_by,
            )
            if cid:
                count += 1
                conn.execute(
                    """INSERT INTO absentism_fines
                       (member_id, meeting_id, amount, status, entered_by)
                       VALUES (?, ?, ?, 'Owed', ?)""",
                    (r["member_id"], meeting_id, amount, entered_by),
                )
    return count


def apply_minutes_levy(meeting_id: int, amount: float,
                       entered_by: int = None) -> int:
    """Apply the compulsory minutes levy as carried-over debt to absent members.

    Present members are expected to pay cash at the meeting; absent members
    carry it as debt. Returns the number of new charges created.
    """
    if amount <= 0:
        return 0
    conn = get_connection()
    count = 0
    with conn:
        rows = conn.execute(
            "SELECT member_id FROM attendance WHERE meeting_id = ? AND status = 'Absent'",
            (meeting_id,),
        ).fetchall()
        for r in rows:
            cid = _create_charge(
                conn, r["member_id"], CHARGE_MINUTES_LEVY, amount,
                meeting_id=meeting_id,
                description=f"Minutes levy (carried over) for meeting #{meeting_id}",
                entered_by=entered_by,
            )
            if cid:
                count += 1
    return count


def reverse_absence_charges(member_db_id: int, meeting_id: int,
                            conn=None) -> int:
    """Reverse Absence Fine and Minutes Levy charges for a member at a meeting.

    If the charge is fully unpaid (amount_paid == 0), it is deleted.
    If partially paid, the outstanding portion is zeroed out.
    Also cleans up the absentism_fines audit log.
    Returns the number of charges affected.
    """
    own_conn = conn is None
    if own_conn:
        conn = get_connection()
    count = 0
    rows = conn.execute(
        """SELECT id, amount, amount_paid FROM member_charges
           WHERE member_id = ? AND meeting_id = ?
             AND charge_type IN (?, ?, ?)""",
        (member_db_id, meeting_id, CHARGE_ABSENCE_FINE, CHARGE_ABSENTISM, CHARGE_MINUTES_LEVY),
    ).fetchall()
    for r in rows:
        paid = r["amount_paid"] or 0
        if paid < 1e-9:
            conn.execute("DELETE FROM member_charges WHERE id = ?", (r["id"],))
        else:
            conn.execute(
                "UPDATE member_charges SET amount = ?, status = ? WHERE id = ?",
                (paid, CHARGE_STATUS_PAID, r["id"]),
            )
        count += 1
    # Clean up absentism_fines audit records for this meeting
    conn.execute(
        "DELETE FROM absentism_fines WHERE member_id = ? AND meeting_id = ? AND amount_paid < 1e-9",
        (member_db_id, meeting_id),
    )
    if own_conn:
        conn.commit()
    return count


def _log_attendance(conn, member_db_id: int, meeting_id: int,
                    old_status: str, new_status: str, user_id: int = None):
    """Log an attendance change to the audit log."""
    row = conn.execute(
        "SELECT full_name, member_id FROM members WHERE id = ?",
        (member_db_id,),
    ).fetchone()
    name = row["full_name"] if row else "Unknown"
    mid = row["member_id"] if row else "?"
    old_label = old_status or "Unset"
    new_label = new_status or "Unset"
    conn.execute(
        """INSERT INTO audit_logs (user_id, action, details)
           VALUES (?, ?, ?)""",
        (user_id, "Attendance Changed",
         f"{name} ({mid}): Meeting #{meeting_id}: {old_label} -> {new_label}"),
    )


def delete_meeting(meeting_id: int, entered_by: int = None) -> bool:
    """Delete a meeting and all its attendance + associated charges.

    Returns True if the meeting was found and deleted.
    """
    conn = get_connection()
    with conn:
        mtg = conn.execute("SELECT id, date, meeting_number FROM meetings WHERE id = ?",
                           (meeting_id,)).fetchone()
        if not mtg:
            return False
        conn.execute("DELETE FROM attendance WHERE meeting_id = ?", (meeting_id,))
        conn.execute("DELETE FROM member_charges WHERE meeting_id = ?", (meeting_id,))
        conn.execute("DELETE FROM absentism_fines WHERE meeting_id = ?", (meeting_id,))
        conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
        user_label = ""
        if entered_by:
            u = conn.execute("SELECT username FROM users WHERE id = ?",
                             (entered_by,)).fetchone()
            user_label = u["username"] if u else str(entered_by)
        conn.execute(
            """INSERT INTO audit_logs (user_id, action, details)
               VALUES (?, ?, ?)""",
            (entered_by, "Meeting Deleted",
             f"Meeting #{mtg['meeting_number']} ({mtg['date']}) deleted by {user_label}"),
        )
    return True


def create_other_charge(member_db_id: int, amount: float, description: str = "",
                        meeting_id: int = None, entered_by: int = None) -> str:
    """Create a tagged 'Other' charge for a member."""
    conn = get_connection()
    with conn:
        return _create_charge(
            conn, member_db_id, CHARGE_OTHER, amount,
            meeting_id=meeting_id, description=description or "Other charge",
            entered_by=entered_by,
        )


def get_member_charges(member_db_id: int, only_owed: bool = False) -> list:
    """List a member's charges, oldest first."""
    conn = get_connection()
    sql = "SELECT * FROM member_charges WHERE member_id = ?"
    if only_owed:
        sql += " AND status != 'Paid'"
    sql += " ORDER BY created_at ASC, id ASC"
    return conn.execute(sql, (member_db_id,)).fetchall()


def record_charge_payment(member_db_id: int, amount: float, category: str,
                          meeting_id: int = None, payment_method: str = "Cash",
                          entered_by: int = None, date: str = None,
                          description: str = "", allow_backdate: bool = False) -> str:
    """Record payment against a member's charges (oldest first within category).

    Category is one of 'Minutes', 'Fines', 'Other'. Raises ValueError if the
    amount exceeds what is owed in that category.
    """
    category_map = {
        "Minutes": CHARGE_MINUTES_LEVY,
        "Fines": CHARGE_ABSENCE_FINE,
        "ICT": CHARGE_ICT,
        "AGM": CHARGE_AGM,
        "Lateness": CHARGE_LATENESS,
        "Absentism": CHARGE_ABSENTISM,
        "Other": CHARGE_OTHER,
    }
    charge_type = category_map.get(category, CHARGE_OTHER)
    conn = get_connection()
    date = resolve_entry_date(date, allow_backdate)
    with conn:
        rows = conn.execute(
            """SELECT * FROM member_charges
               WHERE member_id = ? AND charge_type = ? AND status != 'Paid'
               ORDER BY created_at ASC, id ASC""",
            (member_db_id, charge_type),
        ).fetchall()
        owed = sum((r["amount"] or 0) - (r["amount_paid"] or 0) for r in rows)
        if amount > owed + 1e-9:
            raise ValueError(
                f"Amount {amount:,.0f} exceeds {category} owed ({owed:,.0f}).")
        remaining = amount
        for r in rows:
            if remaining <= 0:
                break
            due = (r["amount"] or 0) - (r["amount_paid"] or 0)
            if due <= 0:
                continue
            pay = min(due, remaining)
            new_paid = (r["amount_paid"] or 0) + pay
            status = CHARGE_STATUS_PAID if new_paid >= (r["amount"] or 0) - 1e-9 else CHARGE_STATUS_PARTIAL
            conn.execute(
                "UPDATE member_charges SET amount_paid = ?, status = ? WHERE id = ?",
                (new_paid, status, r["id"]),
            )
            conn.execute(
                """INSERT INTO charge_payment_applications
                   (txn_id, charge_id, amount_applied) VALUES (?, ?, ?)""",
                ("__pending__", r["charge_id"], pay),
            )
            # Sync absentism_fines audit table for Absentism payments
            if charge_type == CHARGE_ABSENTISM and r["meeting_id"]:
                af = conn.execute(
                    """SELECT id, amount, amount_paid FROM absentism_fines
                       WHERE member_id = ? AND meeting_id = ? AND status != 'Paid'
                       ORDER BY created_at ASC, id ASC LIMIT 1""",
                    (member_db_id, r["meeting_id"]),
                ).fetchone()
                if af:
                    af_new_paid = (af["amount_paid"] or 0) + pay
                    af_status = "Paid" if af_new_paid >= (af["amount"] or 0) - 1e-9 else "Partial"
                    conn.execute(
                        "UPDATE absentism_fines SET amount_paid = ?, status = ? WHERE id = ?",
                        (af_new_paid, af_status, af["id"]),
                    )
            remaining -= pay
        txn_id = record_transaction(
            conn, member_db_id, TXN_CHARGE_PAYMENT, amount, meeting_id,
            payment_method,
            description=description or f"{category} payment",
            entered_by=entered_by, date=date,
        )
        conn.execute(
            "UPDATE charge_payment_applications SET txn_id = ? WHERE txn_id = ?",
            (txn_id, "__pending__"),
        )
    return txn_id


def record_other_payment(member_db_id: int, amount: float, tag: str = "",
                         meeting_id: int = None, payment_method: str = "Cash",
                         entered_by: int = None, date: str = None,
                         allow_backdate: bool = False) -> str:
    """Record a tagged 'Other' payment.

    If the member owes 'Other' charges, the payment is applied to them
    (oldest first); any remainder — or the full amount when nothing is
    owed — is recorded as a tagged Other transaction so the money is tracked.
    """
    conn = get_connection()
    date = resolve_entry_date(date, allow_backdate)
    with conn:
        rows = conn.execute(
            """SELECT * FROM member_charges
               WHERE member_id = ? AND charge_type = ? AND status != 'Paid'
               ORDER BY created_at ASC, id ASC""",
            (member_db_id, CHARGE_OTHER),
        ).fetchall()
        remaining = amount
        for r in rows:
            if remaining <= 0:
                break
            due = (r["amount"] or 0) - (r["amount_paid"] or 0)
            if due <= 0:
                continue
            pay = min(due, remaining)
            new_paid = (r["amount_paid"] or 0) + pay
            status = CHARGE_STATUS_PAID if new_paid >= (r["amount"] or 0) - 1e-9 else CHARGE_STATUS_PARTIAL
            conn.execute(
                "UPDATE member_charges SET amount_paid = ?, status = ? WHERE id = ?",
                (new_paid, status, r["id"]),
            )
            remaining -= pay
        txn_id = record_transaction(
            conn, member_db_id, TXN_OTHER, amount, meeting_id,
            payment_method, description=f"Other payment ({tag})" if tag else "Other payment",
            entered_by=entered_by, date=date,
        )
    return txn_id


def record_payment_split(member_db_id: int, amount: float,
                         meeting_id: int = None, payment_method: str = "Cash",
                         entered_by: int = None, date: str = None,
                         share_price: float = 0,
                         allow_backdate: bool = False) -> dict:
    raise ValueError("Payment split is discontinued. Use record_savings directly.")


def record_withdrawal(member_db_id: int, amount: float,
                      meeting_id: int = None, payment_method: str = "Cash",
                      entered_by: int = None, date: str = None,
                      description: str = "",
                      allow_backdate: bool = False) -> str:
    """Record a savings withdrawal (straight deduction, never split).

    Raises ValueError when the amount exceeds the member's savings balance.
    The negative savings leg keeps every summary and the passbook in sync.
    """
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    date = resolve_entry_date(date, allow_backdate)
    balance = (get_member_financial_summary(member_db_id)["total_savings"]
               if member_db_id else 0)
    if amount > balance + 1e-9:
        raise ValueError(
            f"Amount {amount:,.0f} exceeds savings balance ({balance:,.0f}).")
    conn = get_connection()
    with conn:
        txn_id = record_transaction(
            conn, member_db_id, TXN_WITHDRAWAL, amount, meeting_id,
            payment_method,
            description=description or "Savings withdrawal",
            entered_by=entered_by, date=date,
        )
        conn.execute(
            """INSERT INTO savings (member_id, transaction_id, type, amount, balance_after)
               SELECT ?, ?, 'Savings', ?,
                      COALESCE((SELECT SUM(amount) FROM savings WHERE member_id = ?), 0) - ?""",
            (member_db_id, txn_id, -amount, member_db_id, amount),
        )
    return txn_id


def get_member_passbook(member_db_id: int) -> list:
    """Build the member passbook: one row per date, ordered by date.

    All values come from transactions (Money-In model). Category columns
    (Minutes, ICT, etc.) are populated from Charge Payment transactions
    whose description starts with the category name.
    """
    conn = get_connection()

    cur = conn.execute(
        """SELECT t.transaction_id, t.date, t.transaction_type, t.amount,
                  t.description, t.payment_method
           FROM transactions t
           WHERE t.member_id = ? AND t.status = 'Posted'
           ORDER BY t.date ASC, t.id ASC""",
        (member_db_id,),
    )
    txns = cur.fetchall()

    repay_info = {}
    for r in conn.execute(
            """SELECT lr.transaction_id, lr.principal_portion,
                      lr.balance_after FROM loan_repayments lr
               JOIN loans l ON lr.loan_id = l.id
               WHERE l.member_id = ?""", (member_db_id,)).fetchall():
        repay_info[r["transaction_id"]] = r

    fee_map = {k: v for k, v, _ in PASSBOOK_FEE_COLUMNS}

    rows = []
    running_outstanding = 0.0
    for t in txns:
        tid = t["transaction_id"]
        ttype = t["transaction_type"]
        amt = t["amount"] or 0
        desc = (t["description"] or "")

        r = {"date": t["date"], "savings": 0,
             "loan_repayment": 0, "loan_collected": 0,
             "loan_outstanding": "", "other": 0,
             "method": t["payment_method"] or "",
             "description": desc}
        for col_key, _label, _ctype in PASSBOOK_FEE_COLUMNS:
            r[col_key] = 0

        if ttype == TXN_SAVINGS:
            r["savings"] = amt
        elif ttype == TXN_WITHDRAWAL:
            r["savings"] = -abs(amt)
            if not desc.strip():
                r["description"] = "Savings withdrawal"
        elif ttype == TXN_LOAN_REPAYMENT:
            r["loan_repayment"] = amt
            info = repay_info.get(tid)
            if info:
                running_outstanding = max(0.0, (info["balance_after"] or 0))
                r["loan_outstanding"] = running_outstanding
        elif ttype == TXN_LOAN_DISBURSEMENT:
            r["loan_collected"] = amt
            running_outstanding += amt
            r["loan_outstanding"] = running_outstanding
        elif ttype == TXN_CHARGE_PAYMENT:
            matched = False
            for col_key, label, _ctype in PASSBOOK_FEE_COLUMNS:
                if desc.startswith(label):
                    r[col_key] = amt
                    matched = True
                    break
            if not matched:
                r["other"] = amt
        elif ttype in (TXN_OTHER, TXN_ENTRANCE_FEE):
            if desc.startswith("Loan Processing") or desc.startswith("Other Loan"):
                r["other"] = amt
            else:
                r["other"] = amt
        rows.append(r)

    merged = {}
    for row in rows:
        d = row["date"]
        if d not in merged:
            merged[d] = row
        else:
            m = merged[d]
            for key in ("savings", "loan_repayment", "loan_collected", "other"):
                m[key] += row[key]
            for col_key, _, _ in PASSBOOK_FEE_COLUMNS:
                m[col_key] += row.get(col_key, 0)
            if row["loan_outstanding"] != "":
                m["loan_outstanding"] = row["loan_outstanding"]
            if row["description"] and not m["description"]:
                m["description"] = row["description"]
            if row["method"] and not m["method"]:
                m["method"] = row["method"]

    return sorted(merged.values(), key=lambda x: x["date"])


def save_passbook_input(member_db_id: int, date_str: str, categories: dict,
                        payment_method: str = "Cash",
                        entered_by: int = None,
                        allow_backdate: bool = False) -> bool:
    """Save passbook category inputs as Money-In transactions.

    categories: {category_key: amount} e.g. {"minutes": 2000, "ict": 1000}
    category_key must be a key from PASSBOOK_FEE_COLUMNS or a custom key.

    For each category:
      - amount > 0 and no existing txn  -> insert new TXN_CHARGE_PAYMENT
      - amount > 0 and existing txn differs -> reverse old, insert new
      - amount 0/empty and existing txn -> reverse it
    Returns True if any changes were made.
    """
    conn = get_connection()
    date_str = resolve_entry_date(date_str, allow_backdate)
    changed = False

    col_to_label = {k: v for k, v, _ in PASSBOOK_FEE_COLUMNS}

    with conn:
        meeting = conn.execute(
            "SELECT id FROM meetings WHERE date = ?", (date_str,)
        ).fetchone()
        if not meeting:
            meeting_id = create_meeting(
                date=date_str, notes="",
                created_by=entered_by, allow_backdate=True)
        else:
            meeting_id = meeting["id"]

        for col_key, raw_val in categories.items():
            if col_key in ("date", "method", "desc", "savings", "loan_repayment",
                           "loan_collected", "outstanding", "other"):
                continue
            label = col_to_label.get(col_key, col_key.replace("_", " ").title())
            try:
                amt = float(str(raw_val).replace(",", "").replace("₦", ""))
            except (ValueError, TypeError):
                amt = 0

            existing = conn.execute(
                """SELECT t.transaction_id, t.amount
                   FROM transactions t
                   WHERE t.member_id = ? AND t.transaction_type = 'Charge Payment'
                     AND t.description = ? AND t.date = ? AND t.status = 'Posted'
                   LIMIT 1""",
                (member_db_id, f"{label} input", date_str),
            ).fetchone()

            if amt > 0:
                if existing:
                    if abs((existing["amount"] or 0) - amt) > 0.01:
                        reverse_transaction(
                            existing["transaction_id"],
                            "Passbook input update",
                            entered_by or 0, conn=conn)
                        record_transaction(
                            conn, member_db_id, TXN_CHARGE_PAYMENT, amt,
                            meeting_id, payment_method,
                            description=f"{label} input",
                            entered_by=entered_by, date=date_str)
                        changed = True
                else:
                    record_transaction(
                        conn, member_db_id, TXN_CHARGE_PAYMENT, amt,
                        meeting_id, payment_method,
                        description=f"{label} input",
                        entered_by=entered_by, date=date_str)
                    changed = True
            else:
                if existing:
                    reverse_transaction(
                        existing["transaction_id"],
                        "Passbook input removed",
                        entered_by or 0, conn=conn)
                    changed = True

    return changed


def add_loan_document(loan_db_id: int, member_db_id: int, doc_name: str,
                       src_path: str, uploaded_by: int = None) -> int:
    """Store an uploaded physical loan document (named + datetime stamped)."""
    import os
    import shutil
    from database.connection import DB_DIR
    loan, conn = _resolve_loan(loan_db_id)
    if not os.path.exists(src_path):
        raise ValueError("Selected file not found.")
    docs_dir = DB_DIR / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c for c in (doc_name or "document").strip() or "document"
                        if c.isalnum() or c in " _-")[:60]
    ext = os.path.splitext(src_path)[1] or ".pdf"
    dest = docs_dir / f"{stamp}_{safe_name}{ext}"
    shutil.copy2(src_path, dest)
    with conn:
        cur = conn.execute(
            """INSERT INTO loan_documents
               (loan_id, member_id, doc_name, file_path, uploaded_by)
               VALUES (?, ?, ?, ?, ?)""",
            (loan["id"], member_db_id, f"{stamp} — {safe_name}",
             str(dest), uploaded_by),
        )
        return cur.lastrowid


def list_loan_documents(loan_db_id: int) -> list:
    loan, conn = _resolve_loan(loan_db_id)
    return conn.execute(
        "SELECT * FROM loan_documents WHERE loan_id = ? ORDER BY uploaded_at DESC",
        (loan["id"],),
    ).fetchall()


def get_loan_totals_by_period() -> list:
    """Collate loan totals grouped by year then month of application."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT substr(application_date, 1, 7) as ym,
                  COUNT(*) as count,
                  COALESCE(SUM(principal_amount), 0) as principal,
                  COALESCE(SUM(interest_amount), 0) as interest,
                  COALESCE(SUM(total_repayable), 0) as repayable,
                  COALESCE(SUM(outstanding_principal), 0) as out_principal,
                  COALESCE(SUM(outstanding_interest), 0) as out_interest
           FROM loans GROUP BY ym ORDER BY ym DESC"""
    ).fetchall()
    out = []
    for r in rows:
        ym = r["ym"] or "Undated"
        repaid = conn.execute(
            """SELECT COALESCE(SUM(lr.amount), 0) as t FROM loan_repayments lr
               JOIN loans l ON lr.loan_id = l.id
               WHERE substr(l.application_date, 1, 7) = ?
                  OR (l.application_date IS NULL AND ? = 'Undated')""",
            (r["ym"], ym)).fetchone()["t"] if r["ym"] else 0
        out.append({
            "period": ym,
            "count": r["count"],
            "principal": r["principal"],
            "interest": r["interest"],
            "repayable": r["repayable"],
            "repaid": repaid,
            "outstanding": (r["out_principal"] or 0) + (r["out_interest"] or 0),
        })
    # year subtotals
    totals = {}
    for g in out:
        yr = g["period"][:4] if len(g["period"]) >= 4 else "????"
        t = totals.setdefault(yr, {"period": yr, "count": 0, "principal": 0,
                                   "interest": 0, "repayable": 0, "repaid": 0,
                                   "outstanding": 0, "is_year": True})
        for k in ("count", "principal", "interest", "repayable", "repaid", "outstanding"):
            t[k] += g[k] or 0
    flat = []
    for g in out:
        flat.append(g)
    for yr in sorted(totals):
        flat.append(totals[yr])
    return flat


def record_remittance(date: str, amount: float, period_covered: str = "",
                      destination: str = "Headquarters", payment_method: str = "Cash",
                      reference_number: str = "", prepared_by: int = None,
                      approved_by: int = None, notes: str = "",
                      allow_backdate: bool = False) -> str:
    conn = get_connection()
    date = resolve_entry_date(date, allow_backdate)
    rem_id = generate_id("RM")
    with conn:
        conn.execute(
            """INSERT INTO headquarters_remittances
               (remittance_id, date, period_covered, amount, destination,
                payment_method, reference_number, prepared_by, approved_by, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (rem_id, date, period_covered, amount, destination,
             payment_method, reference_number, prepared_by, approved_by, notes),
        )
    return rem_id


def record_hq_funding(amount: float, date: str = "", description: str = "",
                      payment_method: str = "Cash", entered_by: int = None,
                      allow_backdate: bool = False) -> str:
    """Record money received from headquarters (IN)."""
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    date = resolve_entry_date(date, allow_backdate)
    conn = get_connection()
    with conn:
        txn_id = record_transaction(
            conn, None, "Headquarters Funding", amount,
            payment_method=payment_method,
            description=description or "Funding from HQ",
            entered_by=entered_by, date=date,
        )
        _log_finance_entry(conn, entered_by, "HQ Funding",
                           f"Received {amount:,.0f} from HQ",
                           date, amount)
    return txn_id


@require_permission(PERM_SETTINGS_EDIT)
def record_expense(amount: float, date: str = "", category: str = "",
                   description: str = "", payment_method: str = "Cash",
                   entered_by: int = None,
                   allow_backdate: bool = False) -> str:
    """Record an expense (OUT). Writes to both transactions and expenses."""
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    date = resolve_entry_date(date, allow_backdate)
    conn = get_connection()
    with conn:
        txn_id = record_transaction(
            conn, None, "Expense", amount,
            payment_method=payment_method,
            description=description or category or "Expense",
            entered_by=entered_by, date=date,
        )
        conn.execute(
            """INSERT INTO expenses (transaction_id, category, description,
               amount, approved_by) VALUES (?, ?, ?, ?, ?)""",
            (txn_id, category, description, amount, entered_by),
        )
        _log_finance_entry(conn, entered_by, "Expense",
                           f"{category}: {description}" if category else description,
                           date, amount)
    return txn_id


def _log_finance_entry(conn, user_id, action, details, date, amount):
    """Log non-member finance entries to audit_logs."""
    conn.execute(
        "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
        (user_id, action, f"[{date}] {details} ({amount:,.0f})"),
    )


def get_monthly_summary(year: int, month: int) -> dict:
    conn = get_connection()
    month_str = f"{year}-{month:02d}"

    categories_in = ["Savings", "Loan Repayment",
                       "Charge Payment", "Entrance Fee", "Other"]
    placeholders = ",".join(["?"] * len(categories_in))

    cur = conn.execute(
        f"""SELECT COALESCE(SUM(amount), 0) as total FROM transactions
            WHERE transaction_type IN ({placeholders})
            AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
        (*categories_in, month_str),
    )
    money_in = cur.fetchone()["total"]

    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE transaction_type = 'Loan Disbursement'
           AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
        (month_str,),
    )
    loans_out = cur.fetchone()["total"]

    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE transaction_type = 'Withdrawal'
           AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
        (month_str,),
    )
    withdrawals = cur.fetchone()["total"]

    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE transaction_type = 'Expense'
           AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
        (month_str,),
    )
    expenses = cur.fetchone()["total"]

    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM headquarters_remittances
           WHERE strftime('%Y-%m', date) = ?""",
        (month_str,),
    )
    remittance = cur.fetchone()["total"]

    return {
        "money_in": money_in,
        "loans_disbursed": loans_out,
        "withdrawals": withdrawals,
        "expenses": expenses,
        "remittance": remittance,
        "money_out": loans_out + withdrawals + expenses + remittance,
        "net": money_in - (loans_out + withdrawals + expenses + remittance),
    }


def get_monthly_financial_statement(year: int, month: int) -> dict:
    """Compute the monthly financial statement (IN vs OUT model).

    IN: Savings, Minutes, Absentism, Lateness, Others, HQ Funding
    OUT: Expenses, Loans Disbursed, HQ Remittance
    NET: IN - OUT
    """
    conn = get_connection()
    month_str = f"{year}-{month:02d}"

    # ── IN ──
    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE transaction_type = 'Savings'
           AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
        (month_str,))
    in_savings = cur.fetchone()["total"]

    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE transaction_type = 'Charge Payment'
           AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
        (month_str,))
    total_charges = cur.fetchone()["total"]

    # Break down charge payments by description prefix
    in_minutes = 0
    in_absentism = 0
    in_lateness = 0
    in_others = total_charges
    for desc_prefix, field in [
        ("Minutes", "in_minutes"), ("Absentism", "in_absentism"),
        ("Lateness", "in_lateness"),
    ]:
        cur = conn.execute(
            """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
               WHERE transaction_type = 'Charge Payment'
               AND description LIKE ?
               AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
            (f"{desc_prefix}%", month_str))
        val = cur.fetchone()["total"]
        if field == "in_minutes":
            in_minutes = val
        elif field == "in_absentism":
            in_absentism = val
        elif field == "in_lateness":
            in_lateness = val
        in_others -= val

    # Add Entrance Fee and Other to Others
    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE transaction_type IN ('Entrance Fee', 'Other')
           AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
        (month_str,))
    in_others += cur.fetchone()["total"]

    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE transaction_type = 'Headquarters Funding'
           AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
        (month_str,))
    in_hq = cur.fetchone()["total"]

    amount_in = in_savings + in_minutes + in_absentism + in_lateness + in_others + in_hq

    # ── OUT ──
    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE transaction_type = 'Expense'
           AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
        (month_str,))
    out_expenses = cur.fetchone()["total"]

    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM transactions
           WHERE transaction_type = 'Loan Disbursement'
           AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
        (month_str,))
    out_loans = cur.fetchone()["total"]

    cur = conn.execute(
        """SELECT COALESCE(SUM(amount), 0) as total FROM headquarters_remittances
           WHERE strftime('%Y-%m', date) = ?""",
        (month_str,))
    out_hq = cur.fetchone()["total"]

    amount_out = out_expenses + out_loans + out_hq

    return {
        "in_savings": in_savings,
        "in_minutes": in_minutes,
        "in_absentism": in_absentism,
        "in_lateness": in_lateness,
        "in_others": in_others,
        "in_hq": in_hq,
        "amount_in": amount_in,
        "out_expenses": out_expenses,
        "out_loans": out_loans,
        "out_hq": out_hq,
        "amount_out": amount_out,
        "net": amount_in - amount_out,
    }
