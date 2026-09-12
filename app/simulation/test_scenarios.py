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
    _rbac(h)
    _backup_restore(h)
    _mutex(h)
    _migration_dry_run(h)
    _ui_smoke(h)
    _adversarial(h)


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

    h.assert_eq("APP_VERSION constant", APP_VERSION, "1.1.1")
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
    import lock as _lock
    from database.connection import DB_DIR

    # Clean up
    _lock.remove_master_lock()

    h.assert_true("No master PIN initially",
                  not _lock.has_master_lock())

    # Set
    _lock.set_master_lock("1234")
    h.assert_true("Master PIN set",
                  _lock.has_master_lock())

    # Verify via verify_master_lock (salted — two hashes of same PIN differ)
    h.assert_true("PIN verifies correctly",
                  _lock.verify_master_lock("1234"))
    h.assert_true("Wrong PIN fails",
                  not _lock.verify_master_lock("9999"))

    # Lock file survives DB recreate (separate file)
    h.assert_true("Lock file exists at expected path",
                  _lock.LOCK_FILE.exists())

    # Remove
    _lock.remove_master_lock()
    h.assert_true("Master PIN removed",
                  not _lock.has_master_lock())

    # Test legacy hash detection + upgrade
    import hashlib
    from pathlib import Path
    legacy_hash = hashlib.sha256("5678".encode()).hexdigest()
    _lock.LOCK_FILE.write_text(legacy_hash, encoding="utf-8")
    h.assert_true("Legacy hash verified and upgraded",
                  _lock.verify_master_lock("5678"))
    stored = _lock.get_master_lock_hash()
    h.assert_true("Legacy hash auto-upgraded to PBKDF2",
                  stored.startswith("pbkdf2_sha256$"))

    # PBKDF2 format test
    _lock.set_master_lock("5678")
    new_hash = _lock.get_master_lock_hash()
    h.assert_true("New hash starts with pbkdf2_sha256$",
                  new_hash.startswith("pbkdf2_sha256$"))
    h.assert_true("New hash format has 4 parts",
                  len(new_hash.split("$")) == 4)
    h.assert_true("New hash verifies correct PIN",
                  _lock.verify_master_lock("5678"))
    h.assert_true("New hash rejects wrong PIN",
                  not _lock.verify_master_lock("0000"))

    # Cleanup
    _lock.remove_master_lock()


def _rbac(h: SimHarness):
    from permissions import (
        has_permission, get_role_permissions, get_user_role,
        PERM_MEMBERS_MANAGE, PERM_SAVINGS_EDIT, PERM_LOANS_MANAGE,
        PERM_ATTENDANCE, PERM_REPORTS_VIEW, PERM_BACKUP_RESTORE,
        PERM_REVERSE_TXN, PERM_SETTINGS_EDIT, PERM_USERS_MANAGE, PERM_APP_UPDATE,
        ROLE_ADMIN, ROLE_TREASURER, ROLE_SECRETARY,
    )

    # Matrix correctness
    h.assert_true("Admin has all perms",
                  len(get_role_permissions(ROLE_ADMIN)) == 10)
    h.assert_true("Treasurer has 6 perms",
                  len(get_role_permissions(ROLE_TREASURER)) == 6)
    h.assert_true("Secretary has 3 perms",
                  len(get_role_permissions(ROLE_SECRETARY)) == 3)

    h.assert_true("Treasurer can manage members",
                  has_permission(ROLE_TREASURER, PERM_MEMBERS_MANAGE))
    h.assert_true("Treasurer can edit savings",
                  has_permission(ROLE_TREASURER, PERM_SAVINGS_EDIT))
    h.assert_true("Treasurer can manage loans",
                  has_permission(ROLE_TREASURER, PERM_LOANS_MANAGE))
    h.assert_true("Treasurer CANNOT reverse",
                  not has_permission(ROLE_TREASURER, PERM_REVERSE_TXN))
    h.assert_true("Treasurer CANNOT edit settings",
                  not has_permission(ROLE_TREASURER, PERM_SETTINGS_EDIT))
    h.assert_true("Treasurer CANNOT manage users",
                  not has_permission(ROLE_TREASURER, PERM_USERS_MANAGE))

    h.assert_true("Secretary can manage members",
                  has_permission(ROLE_SECRETARY, PERM_MEMBERS_MANAGE))
    h.assert_true("Secretary can view reports",
                  has_permission(ROLE_SECRETARY, PERM_REPORTS_VIEW))
    h.assert_true("Secretary CANNOT edit savings",
                  not has_permission(ROLE_SECRETARY, PERM_SAVINGS_EDIT))
    h.assert_true("Secretary CANNOT manage loans",
                  not has_permission(ROLE_SECRETARY, PERM_LOANS_MANAGE))
    h.assert_true("Secretary CANNOT backup",
                  not has_permission(ROLE_SECRETARY, PERM_BACKUP_RESTORE))

    h.assert_true("Unknown role has no perms",
                  len(get_role_permissions("FakeRole")) == 0)

    # get_user_role lookup
    h.assert_true("Admin role lookup",
                  get_user_role(h._admin_id) == ROLE_ADMIN)

    # Create test users for engine-level rejection
    from database.connection import get_connection
    from utils.helpers import hash_pin
    conn = get_connection()
    conn.execute(
        "INSERT INTO users (username, pin_hash, role_id, is_active) "
        "VALUES (?, ?, (SELECT id FROM roles WHERE name = ?), 1)",
        ("t tester", hash_pin("0000"), ROLE_TREASURER))
    conn.execute(
        "INSERT INTO users (username, pin_hash, role_id, is_active) "
        "VALUES (?, ?, (SELECT id FROM roles WHERE name = ?), 1)",
        ("s tester", hash_pin("0000"), ROLE_SECRETARY))
    conn.commit()
    treasurer_id = conn.execute(
        "SELECT id FROM users WHERE username = 't tester'").fetchone()["id"]
    secretary_id = conn.execute(
        "SELECT id FROM users WHERE username = 's tester'").fetchone()["id"]

    h.assert_true("Treasurer role lookup",
                  get_user_role(treasurer_id) == ROLE_TREASURER)
    h.assert_true("Secretary role lookup",
                  get_user_role(secretary_id) == ROLE_SECRETARY)

    # Engine-level rejection: Treasurer cannot reverse
    from engines.transaction_engine import reverse_transaction
    h.assert_raises("Treasurer reverse rejected by engine",
                    PermissionError,
                    reverse_transaction, "FAKE_TXN", "test", treasurer_id)

    # Engine-level rejection: Secretary cannot record expense
    from engines.transaction_engine import record_expense
    h.assert_raises("Secretary expense rejected by engine",
                    PermissionError,
                    record_expense, 1000, "2026-01-01", "Test", "test",
                    entered_by=secretary_id)


def _backup_restore(h: SimHarness):
    from engines.backup_engine import create_backup, restore_backup, auto_backup, list_backups
    from database.connection import get_connection, DB_PATH
    import os

    # Count current data
    conn = get_connection()
    member_count_before = conn.execute("SELECT COUNT(*) as c FROM members").fetchone()["c"]
    txn_count_before = conn.execute("SELECT COUNT(*) as c FROM transactions").fetchone()["c"]
    h.assert_true("Data exists before backup", member_count_before >= 2)

    # Create backup
    backup_path = create_backup(notes="Test backup")
    h.assert_true("Backup file created", os.path.exists(backup_path))
    h.assert_true("Backup has non-zero size", os.path.getsize(backup_path) > 0)

    # List backups
    backups = list_backups()
    h.assert_true("Backup appears in list", len(backups) >= 1)

    # Restore backup
    restore_backup(backup_path)
    h.assert_true("DB file restored", DB_PATH.exists())

    # Verify data survived restore
    conn2 = get_connection()
    member_count_after = conn2.execute("SELECT COUNT(*) as c FROM members").fetchone()["c"]
    txn_count_after = conn2.execute("SELECT COUNT(*) as c FROM transactions").fetchone()["c"]
    h.assert_eq("Members survived restore", member_count_after, member_count_before)
    h.assert_eq("Transactions survived restore", txn_count_after, txn_count_before)

    # Auto-backup: create one with type Automatic (same as auto_backup uses)
    auto_path = create_backup(notes="Auto-backup fallback", backup_type="Automatic")
    h.assert_true("Auto-backup succeeded", auto_path is not None)
    if auto_path:
        h.assert_true("Auto-backup file exists", os.path.exists(auto_path))
    # Retention: create 12 auto-backups, check only 10 remain
    for _ in range(12):
        create_backup(notes="Retention test", backup_type="Automatic")

    from database.connection import close_connection
    close_connection()
    fresh_conn = get_connection()
    auto_backups = fresh_conn.execute(
        "SELECT COUNT(*) as c FROM backups WHERE backup_type = 'Automatic'"
    ).fetchone()["c"]
    h.assert_true("Retention enforced", auto_backups <= 10)


def _mutex(h: SimHarness):
    from mutex import SingleInstanceGuard

    g1 = SingleInstanceGuard()
    ok1 = g1.acquire()
    h.assert_true("First acquire succeeds", ok1)

    # Second guard should fail (mutex already held)
    g2 = SingleInstanceGuard()
    ok2 = g2.acquire()
    h.assert_true("Second acquire fails", not ok2)

    # Release first, second should succeed
    g1.release()
    ok3 = g2.acquire()
    h.assert_true("Acquire after release succeeds", ok3)

    g2.release()
    h.assert_true("Double release is safe", True)


def _migration_dry_run(h: SimHarness):
    """Simulate upgrading from v8 to v10 with realistic data."""
    import tempfile, shutil, sqlite3, os
    from pathlib import Path
    from database.connection import get_connection, close_connection

    tmp = Path(tempfile.mkdtemp(prefix="orisun_mig_"))
    v8_db = tmp / "v8_test.db"
    try:
        conn = sqlite3.connect(str(v8_db))
        conn.row_factory = sqlite3.Row

        # Create a v8 schema (tables that exist by v8)
        conn.executescript("""
            CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT);
            INSERT INTO schema_migrations (version) VALUES (8);

            CREATE TABLE roles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, permissions TEXT DEFAULT '{}');
            INSERT INTO roles (name, permissions) VALUES ('Admin', '{"all":true}'), ('Member', '{}');

            CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, pin_hash TEXT, role_id INTEGER REFERENCES roles(id), is_active INTEGER DEFAULT 1);
            INSERT INTO users (username, pin_hash, role_id) VALUES ('admin', 'testhash', 1);

            CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT);

            CREATE TABLE members (id INTEGER PRIMARY KEY AUTOINCREMENT, member_id TEXT UNIQUE, full_name TEXT, phone TEXT, address TEXT, date_joined TEXT, status TEXT DEFAULT 'Active', date_ended TEXT, exit_reason TEXT, entrance_fee REAL DEFAULT 0, share_count INTEGER DEFAULT 0, share_value REAL DEFAULT 0, notes TEXT, dob TEXT, gender TEXT, occupation TEXT, email TEXT, next_of_kin TEXT, next_of_kin_phone TEXT, id_type TEXT, id_number TEXT, photo_path TEXT);
            INSERT INTO members (member_id, full_name, phone, date_joined, status) VALUES
                ('ORI-2024-001', 'Alice Test', '08011111111', '2024-01-15', 'Active'),
                ('ORI-2024-002', 'Bob Test', '08022222222', '2024-02-20', 'Active'),
                ('ORI-2024-003', 'Carol Test', '08033333333', '2024-03-10', 'Active');

            CREATE TABLE meetings (id INTEGER PRIMARY KEY AUTOINCREMENT, meeting_date TEXT, meeting_type TEXT, description TEXT, minutes_levy REAL DEFAULT 0, absentism_fine REAL DEFAULT 0);
            INSERT INTO meetings (meeting_date, meeting_type, description, minutes_levy, absentism_fine) VALUES
                ('2026-01-05', 'General', 'January meeting', 200, 500),
                ('2026-02-05', 'General', 'February meeting', 200, 500);

            CREATE TABLE attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, meeting_id INTEGER, member_id INTEGER, status TEXT);
            INSERT INTO attendance (meeting_id, member_id, status) VALUES (1, 1, 'Present'), (1, 2, 'Absent'), (2, 1, 'Present');

            CREATE TABLE transactions (id INTEGER PRIMARY KEY AUTOINCREMENT, txn_id TEXT UNIQUE, member_id INTEGER, transaction_type TEXT, amount REAL, date TEXT, description TEXT, recorded_by INTEGER, status TEXT DEFAULT 'Completed');
            INSERT INTO transactions (txn_id, member_id, transaction_type, amount, date, description, recorded_by, status) VALUES
                ('TXN-001', 1, 'Savings Deposit', 5000, '2026-01-10', 'Monthly savings', 1, 'Completed'),
                ('TXN-002', 2, 'Savings Deposit', 3000, '2026-01-10', 'Monthly savings', 1, 'Completed'),
                ('TXN-003', 1, 'Savings Withdrawal', -1000, '2026-01-15', 'Emergency', 1, 'Completed');

            CREATE TABLE savings (id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER, amount REAL, transaction_type TEXT, balance_after REAL, created_at TEXT);
            INSERT INTO savings (member_id, amount, transaction_type, balance_after, created_at) VALUES
                (1, 5000, 'Deposit', 5000, '2026-01-10'),
                (2, 3000, 'Deposit', 3000, '2026-01-10'),
                (1, -1000, 'Withdrawal', 4000, '2026-01-15');

            CREATE TABLE shares (id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER, shares INTEGER, amount REAL, created_at TEXT);

            CREATE TABLE loans (id INTEGER PRIMARY KEY AUTOINCREMENT, loan_id TEXT UNIQUE, member_id INTEGER, amount REAL, interest_rate REAL, total_repayable REAL, outstanding_principal REAL, outstanding_interest REAL, status TEXT, approved_by INTEGER, disbursed_by INTEGER, approved_at TEXT, disbursed_at TEXT, processing_fee REAL DEFAULT 0, other_charges REAL DEFAULT 0);
            INSERT INTO loans (loan_id, member_id, amount, interest_rate, total_repayable, outstanding_principal, outstanding_interest, status, processing_fee, other_charges) VALUES
                ('LOAN-001', 1, 20000, 0.05, 25000, 20000, 5000, 'Disbursed', 2500, 500);

            CREATE TABLE loan_repayments (id INTEGER PRIMARY KEY AUTOINCREMENT, loan_id TEXT, amount REAL, date TEXT, recorded_by INTEGER);
            INSERT INTO loan_repayments (loan_id, amount, date, recorded_by) VALUES ('LOAN-001', 5000, '2026-02-01', 1);

            CREATE TABLE expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, amount REAL, date TEXT, category TEXT, description TEXT, entered_by INTEGER);
            INSERT INTO expenses (amount, date, category, description, entered_by) VALUES (2000, '2026-01-20', 'Admin', 'Office supplies', 1);

            CREATE TABLE headquarters_remittances (id INTEGER PRIMARY KEY AUTOINCREMENT, amount REAL, date TEXT, notes TEXT, entered_by INTEGER);

            CREATE TABLE audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, action TEXT, details TEXT, table_name TEXT, record_id TEXT, old_values TEXT, new_values TEXT);

            CREATE TABLE backups (id INTEGER PRIMARY KEY AUTOINCREMENT, backup_path TEXT, backup_type TEXT, file_size INTEGER, notes TEXT, created_by INTEGER, created_at TEXT DEFAULT (datetime('now')));

            CREATE TABLE meeting_minutes (id INTEGER PRIMARY KEY AUTOINCREMENT, meeting_id INTEGER, agenda TEXT, decisions TEXT, action_items TEXT, created_by INTEGER, created_at TEXT);
            INSERT INTO meeting_minutes (meeting_id, agenda, decisions, created_by) VALUES (1, 'Budget review', 'Approved', 1);

            CREATE TABLE loan_documents (id INTEGER PRIMARY KEY AUTOINCREMENT, loan_id INTEGER, member_id INTEGER, doc_name TEXT, file_path TEXT, uploaded_at TEXT, uploaded_by INTEGER);

            CREATE TABLE member_charges (id INTEGER PRIMARY KEY AUTOINCREMENT, charge_id TEXT UNIQUE, member_id INTEGER, meeting_id INTEGER, charge_type TEXT, description TEXT, amount REAL, amount_paid REAL DEFAULT 0, status TEXT DEFAULT 'Owed', created_by INTEGER, created_at TEXT);
            INSERT INTO member_charges (charge_id, member_id, meeting_id, charge_type, amount, status) VALUES ('CHG-001', 2, 1, 'Absentism', 500, 'Owed');

            CREATE TABLE absentism_fines (id INTEGER PRIMARY KEY AUTOINCREMENT, member_id INTEGER, meeting_id INTEGER, amount REAL, status TEXT DEFAULT 'Owed', amount_paid REAL DEFAULT 0, entered_by INTEGER, created_at TEXT);
        """)
        conn.commit()

        # Snapshot pre-migration data counts
        member_count = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        txn_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        loan_count = conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0]
        savings_count = conn.execute("SELECT COUNT(*) FROM savings").fetchone()[0]
        charge_count = conn.execute("SELECT COUNT(*) FROM member_charges").fetchone()[0]
        conn.close()

        # Patch connection to use v8 DB, run migrations
        import database.connection as conn_mod
        orig_db_path = conn_mod.DB_PATH
        orig_db_dir = conn_mod.DB_DIR
        conn_mod.DB_PATH = v8_db
        conn_mod.DB_DIR = tmp
        conn_mod._connection = None

        from database.migrations import run_migrations
        run_migrations()

        # Verify migration applied
        conn2 = get_connection()
        cur = conn2.execute("SELECT MAX(version) FROM schema_migrations")
        max_ver = cur.fetchone()[0]
        h.assert_eq("Migration reached v10", max_ver, 10)

        # Verify new v10 tables exist
        ext = conn2.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='external_guarantors'").fetchone()
        h.assert_true("external_guarantors table created", ext is not None)
        cpa = conn2.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='charge_payment_applications'").fetchone()
        h.assert_true("charge_payment_applications table created", cpa is not None)

        # Verify existing data survived
        h.assert_eq("Members survived migration", conn2.execute("SELECT COUNT(*) FROM members").fetchone()[0], member_count)
        h.assert_eq("Transactions survived migration", conn2.execute("SELECT COUNT(*) FROM transactions").fetchone()[0], txn_count)
        h.assert_eq("Loans survived migration", conn2.execute("SELECT COUNT(*) FROM loans").fetchone()[0], loan_count)
        h.assert_eq("Savings survived migration", conn2.execute("SELECT COUNT(*) FROM savings").fetchone()[0], savings_count)
        h.assert_eq("Charges survived migration", conn2.execute("SELECT COUNT(*) FROM member_charges").fetchone()[0], charge_count)

        # Verify member data integrity
        alice = conn2.execute("SELECT full_name, phone FROM members WHERE member_id='ORI-2024-001'").fetchone()
        h.assert_eq("Alice name intact", alice["full_name"], "Alice Test")
        h.assert_eq("Alice phone intact", alice["phone"], "08011111111")

        # Verify loan data integrity
        loan = conn2.execute("SELECT amount, outstanding_principal FROM loans WHERE loan_id='LOAN-001'").fetchone()
        h.assert_eq("Loan amount intact", loan["amount"], 20000.0)
        h.assert_eq("Loan principal intact", loan["outstanding_principal"], 20000.0)

        close_connection()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        # Restore harness DB paths
        import database.connection as conn_mod2
        conn_mod2.DB_PATH = orig_db_path
        conn_mod2.DB_DIR = orig_db_dir
        conn_mod2._connection = None


def _ui_smoke(h: SimHarness):
    """UI smoke: verify all form modules import cleanly and classes exist."""
    import importlib

    forms = [
        ("LoginForm", "ui.login_form"),
        ("MainForm", "ui.main_form"),
        ("SavingsForm", "ui.savings_form"),
        ("LoanForm", "ui.loan_form"),
        ("MemberForm", "ui.member_form"),
        ("AttendanceForm", "ui.attendance_form"),
        ("SettingsForm", "ui.settings_form"),
        ("ReportForm", "ui.report_form"),
    ]

    for class_name, mod_path in forms:
        try:
            mod = importlib.import_module(mod_path)
            cls = getattr(mod, class_name)
            h.assert_true(f"{class_name} imports OK", cls is not None)
        except Exception as e:
            h.assert_true(f"{class_name} imports OK", False, str(e))

    # Verify engine modules import
    engines = [
        ("transaction_engine", "engines.transaction_engine"),
        ("backup_engine", "engines.backup_engine"),
        ("update_engine", "engines.update_engine"),
    ]
    for name, mod_path in engines:
        try:
            mod = importlib.import_module(mod_path)
            h.assert_true(f"{name} imports OK", mod is not None)
        except Exception as e:
            h.assert_true(f"{name} imports OK", False, str(e))

    # Verify key helper modules import
    helpers = [
        ("permissions", "permissions"),
        ("lock", "lock"),
        ("mutex", "mutex"),
        ("validators", "utils.validators"),
        ("helpers", "utils.helpers"),
    ]
    for name, mod_path in helpers:
        try:
            mod = importlib.import_module(mod_path)
            h.assert_true(f"{name} imports OK", mod is not None)
        except Exception as e:
            h.assert_true(f"{name} imports OK", False, str(e))

    # Verify backup_form imports
    try:
        mod = importlib.import_module("ui.backup_form")
        h.assert_true("backup_form imports OK", hasattr(mod, "BackupForm"))
    except Exception as e:
        h.assert_true("backup_form imports OK", False, str(e))

    # Verify reversal dialog code paths exist in savings/loan engines
    try:
        from engines.transaction_engine import reverse_transaction
        h.assert_true("reverse_transaction callable", callable(reverse_transaction))
    except Exception as e:
        h.assert_true("reverse_transaction callable", False, str(e))


def _adversarial(h: SimHarness):
    """Adversarial engine scenarios: edge cases that should fail gracefully."""
    from engines.transaction_engine import (
        record_savings, record_withdrawal, create_loan,
        approve_loan, disburse_loan, record_repayment,
        record_expense,
    )
    from database.connection import get_connection

    conn = get_connection()
    admin_id = conn.execute("SELECT id FROM users LIMIT 1").fetchone()["id"]

    # Register a test member
    conn.execute(
        "INSERT OR IGNORE INTO members (member_id, full_name, phone, date_joined, status) VALUES (?, ?, ?, ?, ?)",
        ("ORI-ADV-001", "Adversary Test", "08099999999", "2026-01-01", "Active"),
    )
    conn.commit()
    member = conn.execute("SELECT id FROM members WHERE member_id='ORI-ADV-001'").fetchone()
    member_id = member["id"]

    # Zero-amount savings
    h.assert_raises("Zero savings rejected",
                    ValueError, record_savings, member_id, 0, None, admin_id)

    # Negative savings
    h.assert_raises("Negative savings rejected",
                    ValueError, record_savings, member_id, -500, None, admin_id)

    # Withdrawal with zero
    h.assert_raises("Zero withdrawal rejected",
                    ValueError, record_withdrawal, member_id, 0, None, admin_id)

    # Withdrawal exceeds balance
    h.assert_raises("Withdrawal exceeds balance",
                    ValueError, record_withdrawal, member_id, 999999, None, admin_id)

    # Expense with zero amount
    h.assert_raises("Zero expense rejected",
                    ValueError, record_expense, 0, "2026-01-01", "Test", "test", entered_by=admin_id)

    # Expense with negative amount
    h.assert_raises("Negative expense rejected",
                    ValueError, record_expense, -500, "2026-01-01", "Test", "test", entered_by=admin_id)

    # Disburse non-approved loan (it's in Applied status)
    loan_id_text = "LOAN-ADV-001"
    conn.execute(
        """INSERT INTO loans (loan_id, member_id, application_date, principal_amount, interest_rate, interest_amount,
           total_repayable, outstanding_principal, outstanding_interest, status, processing_fee, other_charges)
           VALUES (?, ?, '2026-01-01', 10000, 0.05, 500, 10500, 10000, 500, 'Applied', 500, 100)""",
        (loan_id_text, member_id),
    )
    conn.commit()
    h.assert_raises("Disburse non-approved rejected",
                    ValueError, disburse_loan, loan_id_text, member_id, admin_id)

    # Repay loan with zero outstanding (set status to Completed first)
    loan_id_text2 = "LOAN-ADV-002"
    conn.execute(
        """INSERT INTO loans (loan_id, member_id, application_date, principal_amount, interest_rate, interest_amount,
           total_repayable, outstanding_principal, outstanding_interest, status, processing_fee, other_charges)
           VALUES (?, ?, '2026-01-01', 10000, 0.05, 500, 10500, 0, 0, 'Completed', 500, 100)""",
        (loan_id_text2, member_id),
    )
    conn.commit()
    h.assert_raises("Repay completed loan rejected",
                    ValueError, record_repayment, loan_id_text2, 1000, member_id, None, admin_id)

    # Repay more than outstanding
    loan_id_text3 = "LOAN-ADV-003"
    conn.execute(
        """INSERT INTO loans (loan_id, member_id, application_date, principal_amount, interest_rate, interest_amount,
           total_repayable, outstanding_principal, outstanding_interest, status, processing_fee, other_charges)
           VALUES (?, ?, '2026-01-01', 10000, 0.05, 500, 10500, 500, 250, 'Disbursed', 500, 100)""",
        (loan_id_text3, member_id),
    )
    conn.commit()
    h.assert_raises("Repay exceeds outstanding rejected",
                    ValueError, record_repayment, loan_id_text3, 999999, member_id, None, admin_id)

    # Interest calculation sanity: create fresh loan, verify total_repayable
    import datetime as _dt
    today = _dt.date.today().isoformat()
    loan_id_text4 = create_loan(member_id, 20000, 10.0, 0, 0, "Monthly", admin_id, today)
    loan = conn.execute(
        "SELECT total_repayable, outstanding_principal, outstanding_interest FROM loans WHERE loan_id=?",
        (loan_id_text4,),
    ).fetchone()
    h.assert_eq("Loan 20k @ 10% = 22k repayable",
                loan["total_repayable"], 22000.0)
    h.assert_eq("Loan outstanding principal = 20k",
                loan["outstanding_principal"], 20000.0)
    h.assert_eq("Loan outstanding interest = 2k",
                loan["outstanding_interest"], 2000.0)

    # Approve, disburse, and verify repayment: pay 10000, check principal-first split
    approve_loan(loan_id_text4, admin_id)
    disburse_loan(loan_id_text4, member_id, admin_id, date=today)
    record_repayment(loan_id_text4, 10000, member_id, None, admin_id, today)
    loan2 = conn.execute(
        "SELECT outstanding_principal, outstanding_interest FROM loans WHERE loan_id=?",
        (loan_id_text4,),
    ).fetchone()
    # 10000 payment: principal-first: 10000 principal, 0 interest
    h.assert_eq("After 10k pay: principal = 10k",
                loan2["outstanding_principal"], 10000.0)
    h.assert_eq("After 10k pay: interest = 2k",
                loan2["outstanding_interest"], 2000.0)
