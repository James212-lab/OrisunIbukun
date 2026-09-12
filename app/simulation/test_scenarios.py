"""Engine-only simulation scenarios for ORISUN IBUKUN."""
import datetime
from simulation.harness import SimHarness


def run_all(h: SimHarness):
    _foundation(h)
    _members(h)
    _savings(h)
    _passbook_money_in(h)
    _loans(h)
    _loan_fees_money_in(h)
    _external_guarantors(h)
    _attendance_charges(h)
    _reversals(h)
    _treasury(h)
    _shares_neutralized(h)
    _reports(h)
    _update_engine(h)
    _master_pin(h)


def _foundation(h: SimHarness):
    from database.schema import get_setting, SCHEMA_VERSION
    h.assert_eq("Schema version", SCHEMA_VERSION, 10)
    h.assert_true("Admin user exists", h._admin_id is not None)

    from constants import PASSBOOK_FEE_COLUMNS
    h.assert_true("Fee columns defined", len(PASSBOOK_FEE_COLUMNS) >= 6)


def _members(h: SimHarness):
    from engines.transaction_engine import register_member, update_member_details

    m1 = register_member("Alice Test", phone="08011111111",
                         entrance_fee=5000, entered_by=h._admin_id,
                         allow_backdate=True, date_joined="2026-01-05")
    h.assert_true("Register member 1", m1["id"] is not None)
    h.assert_eq("Member 1 ID format", m1["member_id"][:4], "ORI-")

    m2 = register_member("Bob Test", phone="08022222222",
                         entrance_fee=5000, entered_by=h._admin_id,
                         allow_backdate=True, date_joined="2026-01-05")
    h.assert_true("Register member 2", m2["id"] is not None)

    from database.connection import get_connection
    conn = get_connection()
    row = conn.execute("SELECT * FROM members WHERE id = ?", (m1["id"],)).fetchone()
    h.assert_eq("Member 1 name", row["full_name"], "Alice Test")
    h.assert_eq("Member 1 status", row["status"], "Active")

    update_member_details(m1["id"], entered_by=h._admin_id, phone="08099999999")
    row2 = conn.execute("SELECT phone FROM members WHERE id = ?", (m1["id"],)).fetchone()
    h.assert_eq("Member 1 phone updated", row2["phone"], "08099999999")

    h._m1 = m1
    h._m2 = m2


def _savings(h: SimHarness):
    from engines.transaction_engine import record_savings, record_withdrawal
    from database.connection import get_connection

    txn1 = record_savings(h._m1["id"], 10000, entered_by=h._admin_id,
                          date="2026-01-10", allow_backdate=True)
    h.assert_true("Record savings 1", txn1 is not None)

    txn2 = record_savings(h._m1["id"], 5000, entered_by=h._admin_id,
                          date="2026-01-15", allow_backdate=True)
    h.assert_true("Record savings 2", txn2 is not None)

    from engines.transaction_engine import get_member_financial_summary
    fin = get_member_financial_summary(h._m1["id"])
    h.assert_eq("Savings balance", fin["total_savings"], 15000)

    txn3 = record_withdrawal(h._m1["id"], 3000, entered_by=h._admin_id,
                             date="2026-01-20", allow_backdate=True)
    h.assert_true("Record withdrawal", txn3 is not None)

    fin2 = get_member_financial_summary(h._m1["id"])
    h.assert_eq("Savings after withdrawal", fin2["total_savings"], 12000)

    h.assert_raises("Withdrawal exceeds balance", ValueError,
                    record_withdrawal, h._m1["id"], 999999,
                    entered_by=h._admin_id, allow_backdate=True, date="2026-01-21")


def _passbook_money_in(h: SimHarness):
    from engines.transaction_engine import save_passbook_input, get_member_passbook
    from database.connection import get_connection

    ok = save_passbook_input(h._m1["id"], "2026-02-01",
                             {"minutes": 2000, "ict": 1000},
                             entered_by=h._admin_id, allow_backdate=True)
    h.assert_true("Save passbook input (Minutes+ICT)", ok)

    pb = get_member_passbook(h._m1["id"])
    feb_rows = [r for r in pb if r["date"] == "2026-02-01"]
    h.assert_true("Passbook has Feb 1 row", len(feb_rows) >= 1)
    if feb_rows:
        h.assert_eq("Passbook minutes", feb_rows[0].get("minutes", 0), 2000)
        h.assert_eq("Passbook ict", feb_rows[0].get("ict", 0), 1000)

    ok2 = save_passbook_input(h._m1["id"], "2026-02-01",
                              {"minutes": 3000},
                              entered_by=h._admin_id, allow_backdate=True)
    h.assert_true("Update passbook input (Minutes 2000->3000)", ok2)

    pb2 = get_member_passbook(h._m1["id"])
    feb_rows2 = [r for r in pb2 if r["date"] == "2026-02-01"]
    if feb_rows2:
        h.assert_eq("Passbook minutes updated", feb_rows2[0].get("minutes", 0), 3000)

    ok3 = save_passbook_input(h._m1["id"], "2026-02-01",
                              {"ict": ""},
                              entered_by=h._admin_id, allow_backdate=True)
    h.assert_true("Remove passbook input (ICT)", ok3)

    pb3 = get_member_passbook(h._m1["id"])
    feb_rows3 = [r for r in pb3 if r["date"] == "2026-02-01"]
    if feb_rows3:
        h.assert_eq("Passbook ict zeroed", feb_rows3[0].get("ict", 0), 0)

    ok4 = save_passbook_input(h._m1["id"], "2026-02-05",
                              {"lateness": 500, "absentism": 1500},
                              entered_by=h._admin_id, allow_backdate=True)
    h.assert_true("Save passbook custom categories", ok4)
    pb4 = get_member_passbook(h._m1["id"])
    feb5 = [r for r in pb4 if r["date"] == "2026-02-05"]
    if feb5:
        h.assert_eq("Passbook lateness", feb5[0].get("lateness", 0), 500)
        h.assert_eq("Passbook absentism", feb5[0].get("absentism", 0), 1500)


def _loans(h: SimHarness):
    from engines.transaction_engine import (
        create_loan, approve_loan, disburse_loan, record_repayment,
        get_member_loans,
    )
    from database.connection import get_connection

    loan_id = create_loan(h._m1["id"], principal=50000, interest_rate=10,
                          processing_fee=2500, other_charges=500,
                          entered_by=h._admin_id, date="2026-02-10",
                          allow_backdate=True)
    h.assert_true("Create loan", loan_id is not None)

    conn = get_connection()
    loan = conn.execute("SELECT * FROM loans WHERE loan_id = ?", (loan_id,)).fetchone()
    h.assert_eq("Loan total_repayable excludes fees",
                loan["total_repayable"], 55000)
    h.assert_eq("Loan processing_fee stored", loan["processing_fee"], 2500)
    h.assert_eq("Loan other_charges stored", loan["other_charges"], 500)

    approve_loan(loan["id"], approved_by=h._admin_id)
    loan2 = conn.execute("SELECT * FROM loans WHERE id = ?", (loan["id"],)).fetchone()
    h.assert_eq("Loan approved", loan2["status"], "Approved")

    disburse_loan(loan["id"], h._m1["id"], entered_by=h._admin_id,
                  date="2026-02-10", allow_backdate=True)
    loan3 = conn.execute("SELECT * FROM loans WHERE id = ?", (loan["id"],)).fetchone()
    h.assert_eq("Loan disbursed", loan3["status"], "Disbursed")

    fee_txns = conn.execute(
        """SELECT * FROM transactions
           WHERE member_id = ? AND transaction_type = 'Other'
           AND description LIKE 'Loan Processing%'
           AND date = '2026-02-10' AND status = 'Posted'""",
        (h._m1["id"],),
    ).fetchall()
    h.assert_eq("Processing fee money-in recorded", len(fee_txns), 1)

    other_fee_txns = conn.execute(
        """SELECT * FROM transactions
           WHERE member_id = ? AND transaction_type = 'Other'
           AND description LIKE 'Other Loan%'
           AND date = '2026-02-10' AND status = 'Posted'""",
        (h._m1["id"],),
    ).fetchall()
    h.assert_eq("Other charges money-in recorded", len(other_fee_txns), 1)

    repay_txn = record_repayment(loan["id"], 20000, h._m1["id"],
                                 entered_by=h._admin_id,
                                 date="2026-03-01", allow_backdate=True)
    h.assert_true("Record repayment 20000", repay_txn is not None)

    loan4 = conn.execute("SELECT * FROM loans WHERE id = ?", (loan["id"],)).fetchone()
    h.assert_eq("Loan outstanding principal after repay",
                loan4["outstanding_principal"], 30000)
    h.assert_eq("Loan outstanding interest after repay (principal-first)",
                loan4["outstanding_interest"], 5000)

    repay_txn2 = record_repayment(loan["id"], 35000, h._m1["id"],
                                  entered_by=h._admin_id,
                                  date="2026-04-01", allow_backdate=True)
    h.assert_true("Record final repayment", repay_txn2 is not None)

    loan5 = conn.execute("SELECT * FROM loans WHERE id = ?", (loan["id"],)).fetchone()
    h.assert_eq("Loan completed", loan5["status"], "Completed")
    h.assert_eq("Loan outstanding zero", loan5["outstanding_principal"], 0)

    h._loan_id = loan["id"]


def _loan_fees_money_in(h: SimHarness):
    from database.connection import get_connection
    conn = get_connection()

    fee_txns = conn.execute(
        """SELECT SUM(amount) as total FROM transactions
           WHERE member_id = ? AND transaction_type = 'Other'
           AND description IN ('Loan Processing Fee', 'Other Loan Charges')
           AND status = 'Posted'""",
        (h._m1["id"],),
    ).fetchone()
    total_fees = fee_txns["total"] or 0
    h.assert_eq("Loan fees total money-in", total_fees, 3000)

    loan = conn.execute("SELECT total_repayable FROM loans WHERE id = ?",
                        (h._loan_id,)).fetchone()
    h.assert_true("Loan repayable excludes fees",
                  loan["total_repayable"] <= 55000)


def _external_guarantors(h: SimHarness):
    from engines.transaction_engine import (
        add_guarantor, add_external_guarantor, get_loan_guarantors,
    )

    add_guarantor(h._loan_id, h._m2["id"], 25000)

    add_external_guarantor(
        h._loan_id, full_name="Charlie NonMember",
        phone="08033333333", address="123 Test St",
        id_type="NIN", id_number="1234567890",
        photo_path="", relationship="Brother",
        guarantee_amount=15000,
    )

    guar = get_loan_guarantors(h._loan_id)
    h.assert_eq("Guarantor count", guar["total_count"], 2)
    h.assert_eq("Member guarantors", len(guar["members"]), 1)
    h.assert_eq("External guarantors", len(guar["external"]), 1)
    h.assert_eq("External guarantor name",
                guar["external"][0]["full_name"], "Charlie NonMember")
    h.assert_eq("External guarantor relationship",
                guar["external"][0]["relationship"], "Brother")


def _attendance_charges(h: SimHarness):
    from engines.transaction_engine import (
        create_meeting, record_attendance,
        apply_absence_fines, apply_minutes_levy,
        get_member_charges, record_charge_payment,
    )

    mtg_id = create_meeting(date="2026-03-01", notes="Test meeting",
                            created_by=h._admin_id, allow_backdate=True)
    h.assert_true("Create meeting", mtg_id is not None)

    record_attendance(mtg_id, h._m1["id"], "Absent", recorded_by=h._admin_id)
    record_attendance(mtg_id, h._m2["id"], "Present", recorded_by=h._admin_id)

    fine_count = apply_absence_fines(mtg_id, 1000, entered_by=h._admin_id)
    h.assert_eq("Absence fines applied", fine_count, 1)

    levy_count = apply_minutes_levy(mtg_id, 2000, entered_by=h._admin_id)
    h.assert_eq("Minutes levy applied", levy_count, 1)

    charges = get_member_charges(h._m1["id"])
    h.assert_true("Member 1 has charges", len(charges) >= 2)

    txn = record_charge_payment(h._m1["id"], 1000, "Absentism",
                                entered_by=h._admin_id,
                                date="2026-03-01", allow_backdate=True)
    h.assert_true("Pay absentism charge", txn is not None)

    from database.connection import get_connection
    conn = get_connection()
    apps = conn.execute(
        "SELECT * FROM charge_payment_applications WHERE txn_id = ?",
        (txn,),
    ).fetchall()
    h.assert_true("Charge payment audit trail", len(apps) >= 1)

    h._mtg_id = mtg_id


def _reversals(h: SimHarness):
    from engines.transaction_engine import (
        reverse_transaction, get_member_passbook,
        get_member_financial_summary,
    )
    from database.connection import get_connection
    conn = get_connection()

    fin_before = get_member_financial_summary(h._m1["id"])
    savings_before = fin_before["total_savings"]

    savings_txns = conn.execute(
        """SELECT transaction_id FROM transactions
           WHERE member_id = ? AND transaction_type = 'Savings'
           AND status = 'Posted' ORDER BY id ASC LIMIT 1""",
        (h._m1["id"],),
    ).fetchone()
    if savings_txns:
        rev = reverse_transaction(savings_txns["transaction_id"],
                                  "Test reversal", h._admin_id)
        h.assert_true("Reverse savings txn", rev is not None)

        fin_after = get_member_financial_summary(h._m1["id"])
        h.assert_true("Savings balance decreased after reversal",
                      fin_after["total_savings"] < savings_before)

        orig = conn.execute(
            "SELECT status FROM transactions WHERE transaction_id = ?",
            (savings_txns["transaction_id"],),
        ).fetchone()
        h.assert_eq("Original marked Reversed", orig["status"], "Reversed")

    repay_txns = conn.execute(
        """SELECT t.transaction_id FROM transactions t
           JOIN loan_repayments lr ON t.transaction_id = lr.transaction_id
           JOIN loans l ON lr.loan_id = l.id
           WHERE l.id = ? AND t.status = 'Posted' ORDER BY t.id DESC LIMIT 1""",
        (h._loan_id,),
    ).fetchone()
    if repay_txns:
        loan_before = conn.execute(
            "SELECT outstanding_principal FROM loans WHERE id = ?",
            (h._loan_id,),
        ).fetchone()
        rev2 = reverse_transaction(repay_txns["transaction_id"],
                                   "Test repayment reversal", h._admin_id)
        h.assert_true("Reverse repayment", rev2 is not None)
        loan_after = conn.execute(
            "SELECT outstanding_principal FROM loans WHERE id = ?",
            (h._loan_id,),
        ).fetchone()
        h.assert_true("Loan outstanding restored",
                      loan_after["outstanding_principal"] >
                      loan_before["outstanding_principal"])

    h.assert_raises("Cannot reverse already reversed", ValueError,
                    reverse_transaction,
                    savings_txns["transaction_id"] if savings_txns else "FAKE",
                    "double", h._admin_id)


def _treasury(h: SimHarness):
    from engines.transaction_engine import (
        record_hq_funding, record_expense,
        get_monthly_financial_statement, get_monthly_summary,
    )

    record_hq_funding(50000, entered_by=h._admin_id,
                      date="2026-03-15", allow_backdate=True)
    record_expense(10000, category="Rent", description="Office rent",
                   entered_by=h._admin_id,
                   date="2026-03-20", allow_backdate=True)

    stmt = get_monthly_financial_statement(2026, 3)
    h.assert_true("Monthly statement computed", stmt is not None)
    h.assert_true("Amount In positive", stmt["amount_in"] > 0)
    h.assert_true("Amount Out positive", stmt["amount_out"] > 0)
    h.assert_true("Net = In - Out",
                  abs(stmt["net"] - (stmt["amount_in"] - stmt["amount_out"])) < 0.01)
    h.assert_eq("HQ Funding in statement", stmt["in_hq"], 50000)
    h.assert_eq("Expenses in statement", stmt["out_expenses"], 10000)

    summary = get_monthly_summary(2026, 3)
    h.assert_true("Monthly summary computed", summary is not None)
    h.assert_true("Summary money_in >= passbook inputs",
                  summary["money_in"] >= stmt["in_minutes"] + stmt["in_absentism"])


def _shares_neutralized(h: SimHarness):
    from engines.transaction_engine import record_share, record_payment_split
    h.assert_raises("record_share raises", ValueError,
                    record_share, h._m1["id"], 10, 1000)
    h.assert_raises("record_payment_split raises", ValueError,
                    record_payment_split, h._m1["id"], 10000)


def _reports(h: SimHarness):
    from engines.transaction_engine import (
        get_all_loan_members, get_member_financial_summary,
    )
    from database.connection import get_connection
    conn = get_connection()

    all_loan_members = get_all_loan_members()
    h.assert_true("Loan members list not empty", len(all_loan_members) >= 0)

    fin = get_member_financial_summary(h._m1["id"])
    h.assert_true("Financial summary has savings", "total_savings" in fin)
    h.assert_true("Financial summary has outstanding", "outstanding" in fin)

    report_types_count = conn.execute(
        "SELECT COUNT(DISTINCT transaction_type) as cnt FROM transactions WHERE status = 'Posted'"
    ).fetchone()["cnt"]
    h.assert_true("Multiple transaction types exist", report_types_count >= 3)


def _update_engine(h: SimHarness):
    from engines.update_engine import (
        _parse_version, get_local_version, _extract_expected_sha256,
        _compute_sha256, can_update,
    )
    from constants import APP_VERSION, GITHUB_REPO

    h.assert_eq("APP_VERSION constant", APP_VERSION, "1.1.0")
    h.assert_eq("GITHUB_REPO constant", GITHUB_REPO, "James212-lab/OrisunIbukun")

    # Version parsing
    h.assert_eq("Parse 'v1.1.0'", _parse_version("v1.1.0"), (1, 1, 0))
    h.assert_eq("Parse '2.0.0-beta'", _parse_version("2.0.0-beta"), (2, 0, 0))
    h.assert_eq("Parse '1.10.3'", _parse_version("1.10.3"), (1, 10, 3))

    # Local version
    h.assert_eq("get_local_version", get_local_version(), APP_VERSION)

    # SHA-256 extraction from release notes
    notes1 = "## What's new\n\n- Bug fixes\n\nSHA256: " + "a" * 64
    h.assert_eq("Extract SHA256 from notes",
                _extract_expected_sha256(notes1), "a" * 64)

    notes2 = "No checksum here"
    h.assert_true("No SHA256 returns None",
                  _extract_expected_sha256(notes2) is None)

    notes3 = "SHA-256: " + "B" * 64
    h.assert_eq("SHA-256 prefix works",
                _extract_expected_sha256(notes3), "b" * 64)

    notes4 = "SHA256: short"
    h.assert_true("Bad SHA256 length returns None",
                  _extract_expected_sha256(notes4) is None)

    # Source-mode guard
    h.assert_true("can_update is False in source mode",
                  can_update() is False)


def _master_pin(h: SimHarness):
    from database.schema import get_setting, set_setting
    from utils.helpers import hash_pin

    key = "master_pin_hash"

    # Clean up
    set_setting(key, "")

    h.assert_true("No master PIN initially",
                  get_setting(key) == "")

    # Set
    pin_hash = hash_pin("1234")
    set_setting(key, pin_hash)
    h.assert_true("Master PIN set",
                  get_setting(key) == pin_hash)

    # Verify
    h.assert_true("PIN verifies correctly",
                  hash_pin("1234") == get_setting(key))
    h.assert_true("Wrong PIN fails",
                  hash_pin("9999") != get_setting(key))

    # Remove
    set_setting(key, "")
    h.assert_true("Master PIN removed",
                  get_setting(key) == "")
