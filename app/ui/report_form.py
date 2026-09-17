import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import datetime
from database.connection import get_connection
from engines.transaction_engine import (
    get_monthly_summary, get_member_financial_summary,
    get_monthly_financial_statement,
)
from utils.helpers import format_currency, PaginationHelper
from utils.date_picker import pick_date
from database.schema import get_setting


BLUE = "#1565C0"
WHITE = "#FFFFFF"
LIGHT_BLUE = "#E3F2FD"
DARK_BLUE = "#0D47A1"
GREY = "#F5F5F5"
GREEN = "#2E7D32"
LIGHT_GREEN = "#E8F5E9"

REPORT_TYPES = [
    "Total Members (Detailed)",
    "Total Payments (Detailed)",
    "Total Fines (Detailed)",
    "Total Loans (Detailed)",
    "Withdrawn Members (Detailed)",
    "Monthly Money In/Out",
    "Monthly Financial Statement",
    "Member Savings Statement",
    "Member Loan Statement",
    "Outstanding Loans Report",
    "Outstanding Charges Report",
    "Attendance Report",
    "Headquarters Remittance Report",
    "Audit Log Report",
]


class ReportForm(tk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, bg=WHITE)
        self.current_user = current_user
        self.selected_report = None
        self.selected_member_db_id = None
        self._current_columns = ()
        self._current_headings = {}
        self._search_after_id = None

        self.pack(fill="both", expand=True)
        self._build_ui()

        # Auto-select first report
        try:
            self.report_listbox.selection_set(0)
            self.selected_report = REPORT_TYPES[0]
            self._on_report_select(None)
        except Exception:
            pass

    def _build_ui(self):
        header = tk.Frame(self, bg=BLUE)
        header.pack(fill="x")
        tk.Label(header, text="REPORTS & STATEMENTS", font=("Segoe UI", 16, "bold"),
                 fg=WHITE, bg=BLUE).pack(pady=8)

        # Date range bar
        self._build_date_range_bar()

        # Main content: left listbox + right results
        content = tk.Frame(self, bg=WHITE)
        content.pack(fill="both", expand=True, padx=15, pady=(8, 0))

        self._build_left_panel(content)
        self._build_right_panel(content)

    def _build_date_range_bar(self):
        bar = tk.Frame(self, bg=LIGHT_BLUE, padx=15, pady=6)
        bar.pack(fill="x")

        tk.Label(bar, text="Date Range:", font=("Segoe UI", 10, "bold"),
                 fg=BLUE, bg=LIGHT_BLUE).pack(side="left")

        self.date_from_var = tk.StringVar(
            value=datetime.date.today().replace(month=1, day=1).isoformat())
        self.date_to_var = tk.StringVar(value=datetime.date.today().isoformat())

        tk.Label(bar, text="From:", font=("Segoe UI", 10),
                 fg="#333333", bg=LIGHT_BLUE).pack(side="left", padx=(10, 2))
        self.date_from_entry = tk.Entry(bar, textvariable=self.date_from_var,
                                        font=("Segoe UI", 10), width=12,
                                        relief="solid", bd=1)
        self.date_from_entry.pack(side="left", padx=(0, 2))
        tk.Button(bar, text="...", font=("Segoe UI", 8),
                  bg=WHITE, fg=BLUE, relief="flat", padx=2,
                  command=lambda: pick_date(bar, self.date_from_var)).pack(side="left", padx=(0, 8))

        tk.Label(bar, text="To:", font=("Segoe UI", 10),
                 fg="#333333", bg=LIGHT_BLUE).pack(side="left", padx=(0, 2))
        self.date_to_entry = tk.Entry(bar, textvariable=self.date_to_var,
                                      font=("Segoe UI", 10), width=12,
                                      relief="solid", bd=1)
        self.date_to_entry.pack(side="left", padx=(0, 2))
        tk.Button(bar, text="...", font=("Segoe UI", 8),
                  bg=WHITE, fg=BLUE, relief="flat", padx=2,
                  command=lambda: pick_date(bar, self.date_to_var)).pack(side="left", padx=(0, 8))

        now = datetime.date.today()
        for text, fd, td in [
            ("This Month", now.replace(day=1), now),
            ("This Quarter", self._quarter_start(now), now),
            ("This Year", now.replace(month=1, day=1), now),
            ("All Time", datetime.date(2000, 1, 1), datetime.date(2099, 12, 31)),
        ]:
            tk.Button(bar, text=text, font=("Segoe UI", 9),
                      bg=WHITE, fg=BLUE, relief="flat", padx=6, pady=1,
                      command=lambda f=fd, t=td: self._set_date_range(f, t)
                      ).pack(side="left", padx=(4, 0))

    def _quarter_start(self, d):
        q = (d.month - 1) // 3
        return d.replace(month=q * 3 + 1, day=1)

    def _set_date_range(self, fd, td):
        self.date_from_var.set(fd.isoformat())
        self.date_to_var.set(td.isoformat())

    def _get_date_range(self):
        return self.date_from_var.get().strip(), self.date_to_var.get().strip()

    def _build_left_panel(self, parent):
        left = tk.Frame(parent, bg=WHITE, width=240)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        tk.Label(left, text="Choose Report", font=("Segoe UI", 11, "bold"),
                 fg=BLUE, bg=WHITE, anchor="w").pack(anchor="w", pady=(0, 6))

        list_frame = tk.Frame(left, bg=WHITE)
        list_frame.pack(fill="both", expand=True)
        self.report_listbox = tk.Listbox(
            list_frame, font=("Segoe UI", 10), bg=GREY, relief="flat",
            height=len(REPORT_TYPES), selectbackground=BLUE, selectforeground=WHITE,
            activestyle="none", exportselection=False
        )
        list_scroll = ttk.Scrollbar(list_frame, orient="vertical",
                                    command=self.report_listbox.yview)
        self.report_listbox.configure(yscrollcommand=list_scroll.set)
        self.report_listbox.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")
        for rt in REPORT_TYPES:
            self.report_listbox.insert("end", rt)
        self.report_listbox.bind("<<ListboxSelect>>", self._on_report_select)

    def _build_right_panel(self, parent):
        right = tk.Frame(parent, bg=WHITE)
        right.pack(side="left", fill="both", expand=True)

        # Extra params (member search, status filter — shown per report)
        self.param_frame = tk.Frame(right, bg=LIGHT_BLUE, padx=10, pady=6)
        self.param_frame.pack(fill="x", pady=(0, 6))

        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="All")
        self.extra_widgets = {}

        # Bottom buttons — packed FIRST to reserve space
        btn_frame = tk.Frame(right, bg=WHITE, pady=6)
        btn_frame.pack(fill="x", side="bottom")

        tk.Button(btn_frame, text="Generate Report", font=("Segoe UI", 11, "bold"),
                  bg=BLUE, fg=WHITE, relief="flat", padx=14, pady=4,
                  command=self._generate_report).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="Print", font=("Segoe UI", 11, "bold"),
                  bg=GREEN, fg=WHITE, relief="flat", padx=14, pady=4,
                  command=self._print_report).pack(side="left", padx=(0, 8))
        tk.Button(btn_frame, text="Export CSV", font=("Segoe UI", 11, "bold"),
                  bg="#E65100", fg=WHITE, relief="flat", padx=14, pady=4,
                  command=self._export_csv).pack(side="left")

        # Results tree — fills remaining space
        results_frame = tk.Frame(right, bg=WHITE)
        results_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(results_frame, show="headings", height=10)
        tree_scroll_y = ttk.Scrollbar(results_frame, orient="vertical", command=self.tree.yview)
        tree_scroll_x = ttk.Scrollbar(results_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x.pack(side="bottom", fill="x")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI Symbol", 9), rowheight=26)
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    def _on_report_select(self, event):
        sel = self.report_listbox.curselection()
        if not sel:
            return
        self.selected_report = REPORT_TYPES[sel[0]]
        self._show_params(self.selected_report)

    def _show_params(self, report_type):
        # Clear old extra widgets
        for w in self.param_frame.winfo_children():
            w.destroy()
        self.extra_widgets = {}
        self.selected_member_db_id = None

        if report_type in ("Member Savings Statement", "Member Loan Statement"):
            tk.Label(self.param_frame, text="Search Member:", font=("Segoe UI", 10),
                     fg=BLUE, bg=LIGHT_BLUE).pack(side="left", padx=(0, 4))
            self.search_var.set("")
            entry = tk.Entry(self.param_frame, textvariable=self.search_var,
                             font=("Segoe UI", 10), width=25, relief="solid", bd=1)
            entry.pack(side="left", padx=(0, 4))
            entry.bind("<KeyRelease>", lambda e: self._schedule_member_search())
            tk.Button(self.param_frame, text="Search", font=("Segoe UI", 9, "bold"),
                      bg=BLUE, fg=WHITE, relief="flat", padx=6,
                      command=self._search_member).pack(side="left", padx=(0, 4))
            self.result_label = tk.Label(self.param_frame, text="",
                                         font=("Segoe UI", 10, "bold"),
                                         fg=GREEN, bg=LIGHT_BLUE)
            self.result_label.pack(side="left", padx=(8, 0))

        elif report_type in ("Total Members (Detailed)", "Total Loans (Detailed)"):
            tk.Label(self.param_frame, text="Status:", font=("Segoe UI", 10),
                     fg=BLUE, bg=LIGHT_BLUE).pack(side="left", padx=(0, 4))
            statuses = ["All", "Active", "Withdrawn"] if "Members" in report_type else \
                       ["All", "Applied", "Approved", "Disbursed", "Active", "Overdue", "Completed"]
            combo = ttk.Combobox(self.param_frame, textvariable=self.status_var,
                                 width=12, state="readonly", values=statuses)
            combo.set("All")
            combo.pack(side="left")

        elif report_type in ("Monthly Money In/Out", "Monthly Financial Statement", "Attendance Report"):
            tk.Label(self.param_frame, text="Note: Using date range above.",
                     font=("Segoe UI", 10, "italic"), fg="#666666",
                     bg=LIGHT_BLUE).pack(side="left")

    def _schedule_member_search(self):
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(400, self._search_member)

    def _search_member(self):
        self._search_after_id = None
        query = self.search_var.get().strip()
        if not query:
            return
        conn = get_connection()
        row = conn.execute(
            """SELECT id, member_id, full_name FROM members
               WHERE (full_name LIKE ? OR member_id LIKE ? OR phone LIKE ?)
               AND status = 'Active' LIMIT 1""",
            (f"%{query}%", f"%{query}%", f"%{query}%")).fetchone()
        if row:
            self.selected_member_db_id = row["id"]
            if hasattr(self, "result_label"):
                self.result_label.config(text=f"Selected: {row['full_name']} ({row['member_id']})")
        else:
            self.selected_member_db_id = None
            if hasattr(self, "result_label"):
                self.result_label.config(text="Not found", fg="#D32F2F")

    def _configure_tree(self, columns, headings):
        self._current_columns = columns
        self._current_headings = headings
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=headings[col])
            w = headings.get(f"_{col}_width", 120)
            self.tree.column(col, width=w, anchor="center")

    def _clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _generate_report(self):
        if not self.selected_report:
            messagebox.showwarning("No Report", "Select a report from the list.")
            return
        self._clear_tree()
        handlers = {
            "Total Members (Detailed)": self._report_total_members,
            "Total Payments (Detailed)": self._report_total_payments,
            "Total Fines (Detailed)": self._report_total_fines,
            "Total Loans (Detailed)": self._report_total_loans,
            "Withdrawn Members (Detailed)": self._report_withdrawn_members,
            "Monthly Money In/Out": self._report_monthly_money,
            "Monthly Financial Statement": self._report_monthly_financial,
            "Member Savings Statement": self._report_savings_statement,
            "Member Loan Statement": self._report_loan_statement,
            "Outstanding Loans Report": self._report_outstanding_loans,
            "Outstanding Charges Report": self._report_outstanding_charges,
            "Attendance Report": self._report_attendance,
            "Headquarters Remittance Report": self._report_remittance,
            "Audit Log Report": self._report_audit_log,
        }
        handler = handlers.get(self.selected_report)
        if handler:
            try:
                handler()
            except Exception as e:
                messagebox.showerror("Error", f"Failed:\n{e}")

    # ── REPORT HANDLERS ───────────────────────────────────────────

    def _report_total_members(self):
        date_from, date_to = self._get_date_range()
        status_filter = self.status_var.get() if hasattr(self, "status_var") else "All"
        columns = ("member_id", "name", "status", "savings",
                   "loan_out", "owed", "joined")
        headings = {"member_id": "Member ID", "name": "Name", "status": "Category",
                    "savings": "Savings",
                    "loan_out": "Loan Outstanding", "owed": "Charges Owed",
                    "joined": "Date Joined"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = "SELECT id, member_id, full_name, status, date_joined FROM members"
        params = []
        wheres = []
        if status_filter and status_filter != "All":
            wheres.append("status = ?")
            params.append(status_filter)
        if date_from:
            wheres.append("date_joined >= ?")
            params.append(date_from)
        if date_to:
            wheres.append("date_joined <= ?")
            params.append(date_to)
        if wheres:
            sql += " WHERE " + " AND ".join(wheres)
        sql += " ORDER BY full_name"
        rows = conn.execute(sql, params).fetchall()

        t_sav = t_out = t_owed = 0
        for row in rows:
            s = get_member_financial_summary(row["id"])
            owed = s.get("total_owed", 0)
            t_sav += s["total_savings"]
            t_out += s["outstanding"]
            t_owed += owed
            self.tree.insert("", "end", values=(
                row["member_id"], row["full_name"], row["status"],
                format_currency(s["total_savings"]),
                format_currency(s["outstanding"]), format_currency(owed),
                row["date_joined"] or "—"))
        self.tree.insert("", "end", values=(
            f"TOTAL ({len(rows)})", "", "", format_currency(t_sav),
            format_currency(t_out),
            format_currency(t_owed), ""))

    def _report_total_payments(self):
        date_from, date_to = self._get_date_range()
        columns = ("date", "member", "type", "amount", "method", "desc")
        headings = {"date": "Date", "member": "Member", "type": "Payment Type",
                    "amount": "Amount", "method": "Method", "desc": "Description"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = """SELECT t.date, t.transaction_type, t.amount, t.payment_method,
                        t.description, m.full_name
                 FROM transactions t LEFT JOIN members m ON t.member_id = m.id
                 WHERE t.status = 'Posted'
                   AND t.transaction_type IN ('Savings',
                       'Loan Repayment','Charge Payment','Other','Entrance Fee')"""
        params = []
        if date_from:
            sql += " AND t.date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND t.date <= ?"
            params.append(date_to)
        sql += " ORDER BY t.date ASC"
        rows = conn.execute(sql, params).fetchall()

        total = 0
        for row in rows:
            total += row["amount"] or 0
            self.tree.insert("", "end", values=(
                row["date"], row["full_name"] or "—", row["transaction_type"],
                format_currency(row["amount"]), row["payment_method"] or "—",
                (row["description"] or "")[:45]))
        self.tree.insert("", "end", values=(
            "", f"TOTAL ({len(rows)} payments)", "", format_currency(total), "", ""))

    def _report_total_fines(self):
        date_from, date_to = self._get_date_range()
        columns = ("member", "meeting", "amount", "paid", "owed", "status", "date")
        headings = {"member": "Member", "meeting": "Meeting #", "amount": "Fined",
                    "paid": "Paid", "owed": "Owed", "status": "Status", "date": "Date"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = """SELECT c.amount, c.amount_paid, c.status, c.created_at,
                        m.full_name, mt.meeting_number, mt.date as mdate
                 FROM member_charges c
                 JOIN members m ON c.member_id = m.id
                 LEFT JOIN meetings mt ON c.meeting_id = mt.id
                 WHERE c.charge_type = 'Absence Fine'"""
        params = []
        if date_from:
            sql += " AND mt.date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND mt.date <= ?"
            params.append(date_to)
        sql += " ORDER BY mt.date ASC"
        rows = conn.execute(sql, params).fetchall()

        t_billed = t_paid = 0
        for row in rows:
            t_billed += row["amount"] or 0
            t_paid += row["amount_paid"] or 0
            self.tree.insert("", "end", values=(
                row["full_name"], row["meeting_number"] or "—",
                format_currency(row["amount"]), format_currency(row["amount_paid"]),
                format_currency((row["amount"] or 0) - (row["amount_paid"] or 0)),
                row["status"], row["mdate"] or "—"))
        self.tree.insert("", "end", values=(
            f"TOTAL ({len(rows)})", "", format_currency(t_billed),
            format_currency(t_paid), format_currency(t_billed - t_paid), "", ""))

    def _report_total_loans(self):
        date_from, date_to = self._get_date_range()
        status_filter = self.status_var.get() if hasattr(self, "status_var") else "All"
        columns = ("loan_id", "member", "principal", "interest", "repayable",
                   "repaid", "outstanding", "status", "applied")
        headings = {"loan_id": "Loan ID", "member": "Member", "principal": "Principal",
                    "interest": "Interest", "repayable": "Repayable",
                    "repaid": "Repaid", "outstanding": "Outstanding",
                    "status": "Status", "applied": "Applied"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = """SELECT l.loan_id, l.principal_amount, l.interest_amount,
                        l.total_repayable, l.outstanding_principal,
                        l.outstanding_interest, l.status, l.application_date,
                        m.full_name,
                        (SELECT COALESCE(SUM(amount), 0) FROM loan_repayments
                         WHERE loan_id = l.id) as repaid
                 FROM loans l JOIN members m ON l.member_id = m.id"""
        params = []
        wheres = []
        if status_filter and status_filter != "All":
            wheres.append("l.status = ?")
            params.append(status_filter)
        if date_from:
            wheres.append("l.application_date >= ?")
            params.append(date_from)
        if date_to:
            wheres.append("l.application_date <= ?")
            params.append(date_to)
        if wheres:
            sql += " WHERE " + " AND ".join(wheres)
        sql += " ORDER BY l.application_date ASC"
        rows = conn.execute(sql, params).fetchall()

        t = {"n": 0, "p": 0, "i": 0, "r": 0, "pd": 0, "o": 0}
        for row in rows:
            out = (row["outstanding_principal"] or 0) + (row["outstanding_interest"] or 0)
            t["n"] += 1
            t["p"] += row["principal_amount"] or 0
            t["i"] += row["interest_amount"] or 0
            t["r"] += row["total_repayable"] or 0
            t["pd"] += row["repaid"] or 0
            t["o"] += out
            self.tree.insert("", "end", values=(
                row["loan_id"], row["full_name"],
                format_currency(row["principal_amount"]),
                format_currency(row["interest_amount"]),
                format_currency(row["total_repayable"]),
                format_currency(row["repaid"]), format_currency(out),
                row["status"], row["application_date"] or "—"))
        self.tree.insert("", "end", values=(
            f"TOTAL ({t['n']})", "", format_currency(t["p"]), format_currency(t["i"]),
            format_currency(t["r"]), format_currency(t["pd"]),
            format_currency(t["o"]), "", ""))

    def _report_withdrawn_members(self):
        date_from, date_to = self._get_date_range()
        columns = ("member_id", "name", "status", "exited", "reason",
                   "savings", "loan_out", "owed", "joined")
        headings = {"member_id": "Member ID", "name": "Name", "status": "Category",
                    "exited": "Date Exited", "reason": "Exit Reason",
                    "savings": "Savings Balance",
                    "loan_out": "Loan Outstanding", "owed": "Charges Owed",
                    "joined": "Date Joined"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = """SELECT m.id, m.member_id, m.full_name, m.status,
                        m.date_ended, m.exit_reason, m.date_joined
                 FROM members m
                 WHERE m.status = 'Exited'"""
        params = []
        if date_from:
            sql += " AND m.date_ended >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND m.date_ended <= ?"
            params.append(date_to)
        sql += " ORDER BY m.date_ended ASC, m.full_name"
        rows = conn.execute(sql, params).fetchall()

        t_sav = t_out = t_owed = 0
        for row in rows:
            s = get_member_financial_summary(row["id"])
            owed = s.get("total_owed", 0)
            t_sav += s["total_savings"]
            t_out += s["outstanding"]
            t_owed += owed
            reason = row["exit_reason"] or "—"
            if len(reason) > 45:
                reason = reason[:45] + "…"
            self.tree.insert("", "end", values=(
                row["member_id"], row["full_name"], row["status"],
                row["date_ended"] or "—", reason,
                format_currency(s["total_savings"]),
                format_currency(s["outstanding"]),
                format_currency(owed), row["date_joined"] or "—"))
        if rows:
            self.tree.insert("", "end", values=(
                f"TOTAL ({len(rows)})", "", "", "", "",
                format_currency(t_sav),
                format_currency(t_out), format_currency(t_owed), ""))

    def _report_monthly_money(self):
        date_from, date_to = self._get_date_range()
        # Use date range to compute monthly breakdown
        columns = ("month", "money_in", "loans_out", "withdrawals", "expenses",
                   "remittance", "money_out", "net")
        headings = {"month": "Month", "money_in": "Money In",
                    "loans_out": "Loans Disbursed", "withdrawals": "Withdrawals",
                    "expenses": "Expenses", "remittance": "Remittance",
                    "money_out": "Money Out", "net": "Net"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = """SELECT substr(date, 1, 7) as ym FROM transactions
                 WHERE status = 'Posted'"""
        params = []
        if date_from:
            sql += " AND date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND date <= ?"
            params.append(date_to)
        sql += " GROUP BY ym ORDER BY ym ASC"
        months = [r["ym"] for r in conn.execute(sql, params).fetchall()]

        t_in = t_out = t_net = 0
        for ym in months:
            if not ym:
                continue
            year, month = int(ym[:4]), int(ym[5:7])
            s = get_monthly_summary(year, month)
            t_in += s["money_in"]
            t_out += s["money_out"]
            t_net += s["net"]
            self.tree.insert("", "end", values=(
                ym, format_currency(s["money_in"]),
                format_currency(s["loans_disbursed"]),
                format_currency(s["withdrawals"]),
                format_currency(s["expenses"]),
                format_currency(s["remittance"]),
                format_currency(s["money_out"]),
                format_currency(s["net"])))
        self.tree.insert("", "end", values=(
            "TOTAL", format_currency(t_in), "", "", "", "",
            format_currency(t_out), format_currency(t_net)))

    def _report_monthly_financial(self):
        date_from, date_to = self._get_date_range()
        columns = ("month", "in_savings", "in_minutes", "in_absentism",
                   "in_others", "in_hq", "amount_in",
                   "out_expenses", "out_loans", "out_hq", "amount_out", "net")
        headings = {
            "month": "Month", "in_savings": "Savings", "in_minutes": "Minutes",
            "in_absentism": "Absentism",
            "in_others": "Others", "in_hq": "HQ Funding",
            "amount_in": "Amount In", "out_expenses": "Expenses",
            "out_loans": "Loans Disbursed", "out_hq": "HQ Remittance",
            "amount_out": "Amount Out", "net": "Net Retained",
        }
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = """SELECT substr(date, 1, 7) as ym FROM transactions
                 WHERE status = 'Posted'"""
        params = []
        if date_from:
            sql += " AND date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND date <= ?"
            params.append(date_to)
        sql += " GROUP BY ym ORDER BY ym ASC"
        months = [r["ym"] for r in conn.execute(sql, params).fetchall()]

        t_ins = {k: 0 for k in ["in_savings", "in_minutes", "in_absentism",
                                  "in_others", "in_hq", "amount_in"]}
        t_outs = {k: 0 for k in ["out_expenses", "out_loans", "out_hq", "amount_out"]}
        t_net = 0
        for ym in months:
            if not ym:
                continue
            year, month = int(ym[:4]), int(ym[5:7])
            stmt = get_monthly_financial_statement(year, month)
            for k in t_ins:
                t_ins[k] += stmt[k]
            for k in t_outs:
                t_outs[k] += stmt[k]
            t_net += stmt["net"]
            self.tree.insert("", "end", values=(
                ym, format_currency(stmt["in_savings"]),
                format_currency(stmt["in_minutes"]),
                format_currency(stmt["in_absentism"]),
                format_currency(stmt["in_others"]),
                format_currency(stmt["in_hq"]),
                format_currency(stmt["amount_in"]),
                format_currency(stmt["out_expenses"]),
                format_currency(stmt["out_loans"]),
                format_currency(stmt["out_hq"]),
                format_currency(stmt["amount_out"]),
                format_currency(stmt["net"]),
            ))
        self.tree.insert("", "end", values=(
            "TOTAL", format_currency(t_ins["in_savings"]),
            format_currency(t_ins["in_minutes"]),
            format_currency(t_ins["in_absentism"]),
            format_currency(t_ins["in_others"]),
            format_currency(t_ins["in_hq"]),
            format_currency(t_ins["amount_in"]),
            format_currency(t_outs["out_expenses"]),
            format_currency(t_outs["out_loans"]),
            format_currency(t_outs["out_hq"]),
            format_currency(t_outs["amount_out"]),
            format_currency(t_net),
        ))

    def _report_savings_statement(self):
        if not self.selected_member_db_id:
            messagebox.showwarning("No Member", "Search and select a member first.")
            return
        date_from, date_to = self._get_date_range()
        columns = ("date", "minutes", "type", "amount", "balance")
        headings = {"date": "Date", "minutes": "Meeting #", "type": "Type",
                    "amount": "Amount", "balance": "Balance After"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = """SELECT s.amount, s.balance_after, s.type, s.created_at,
                        t.date, t.meeting_id
                 FROM savings s
                 JOIN transactions t ON s.transaction_id = t.transaction_id
                 WHERE s.member_id = ?"""
        params = [self.selected_member_db_id]
        if date_from:
            sql += " AND t.date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND t.date <= ?"
            params.append(date_to)
        sql += " ORDER BY s.created_at ASC"
        rows = conn.execute(sql, params).fetchall()

        for row in rows:
            minutes = ""
            if row["meeting_id"]:
                mrow = conn.execute("SELECT meeting_number FROM meetings WHERE id = ?",
                                    (row["meeting_id"],)).fetchone()
                if mrow:
                    minutes = str(mrow["meeting_number"])
            self.tree.insert("", "end", values=(
                row["date"], minutes, row["type"],
                format_currency(row["amount"]),
                format_currency(row["balance_after"])))
        if not rows:
            self.tree.insert("", "end", values=("—", "—", "No transactions", "—", "—"))

    def _report_loan_statement(self):
        if not self.selected_member_db_id:
            messagebox.showwarning("No Member", "Search and select a member first.")
            return
        date_from, date_to = self._get_date_range()
        columns = ("date", "amount", "principal", "interest", "balance")
        headings = {"date": "Date", "amount": "Amount Paid",
                    "principal": "Principal", "interest": "Interest",
                    "balance": "Balance After"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = """SELECT lr.amount, lr.principal_portion, lr.interest_portion,
                        lr.balance_after, lr.created_at
                 FROM loan_repayments lr
                 JOIN loans l ON lr.loan_id = l.id
                 WHERE l.member_id = ?"""
        params = [self.selected_member_db_id]
        if date_from:
            sql += " AND lr.created_at >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND lr.created_at <= ?"
            params.append(date_to + " 23:59:59")
        sql += " ORDER BY lr.created_at ASC"
        rows = conn.execute(sql, params).fetchall()

        for row in rows:
            self.tree.insert("", "end", values=(
                (row["created_at"] or "")[:10],
                format_currency(row["amount"]),
                format_currency(row["principal_portion"]),
                format_currency(row["interest_portion"]),
                format_currency(row["balance_after"])))
        if not rows:
            self.tree.insert("", "end", values=("—", "No repayments", "—", "—", "—"))

    def _report_outstanding_loans(self):
        columns = ("loan_id", "member", "principal", "outstanding", "status", "due")
        headings = {"loan_id": "Loan ID", "member": "Member",
                    "principal": "Principal", "outstanding": "Outstanding",
                    "status": "Status", "due": "Due Date"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        rows = conn.execute(
            """SELECT l.loan_id, l.principal_amount, l.outstanding_principal,
                      l.outstanding_interest, l.status, l.due_date, m.full_name
               FROM loans l JOIN members m ON l.member_id = m.id
               WHERE l.status IN ('Disbursed','Active','Overdue')
                 AND (l.outstanding_principal + l.outstanding_interest) > 0
               ORDER BY l.due_date ASC""").fetchall()

        t_p = t_o = 0
        for row in rows:
            out = (row["outstanding_principal"] or 0) + (row["outstanding_interest"] or 0)
            t_p += row["principal_amount"] or 0
            t_o += out
            self.tree.insert("", "end", values=(
                row["loan_id"], row["full_name"],
                format_currency(row["principal_amount"]),
                format_currency(out), row["status"],
                row["due_date"] or "N/A"))
        self.tree.insert("", "end", values=(
            f"TOTAL ({len(rows)})", "", format_currency(t_p),
            format_currency(t_o), "", ""))

    def _report_outstanding_charges(self):
        columns = ("member", "type", "desc", "billed", "paid", "owed", "status")
        headings = {"member": "Member", "type": "Charge Type", "desc": "Description",
                    "billed": "Billed", "paid": "Paid", "owed": "Owed",
                    "status": "Status"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        rows = conn.execute(
            """SELECT c.charge_type, c.description, c.amount, c.amount_paid,
                      c.status, m.full_name
               FROM member_charges c JOIN members m ON c.member_id = m.id
               WHERE c.amount > c.amount_paid
               ORDER BY m.full_name, c.created_at""").fetchall()

        t_b = t_p = 0
        for row in rows:
            owed = (row["amount"] or 0) - (row["amount_paid"] or 0)
            t_b += row["amount"] or 0
            t_p += row["amount_paid"] or 0
            self.tree.insert("", "end", values=(
                row["full_name"], row["charge_type"],
                row["description"] or "—",
                format_currency(row["amount"]),
                format_currency(row["amount_paid"]),
                format_currency(owed), row["status"]))
        self.tree.insert("", "end", values=(
            f"TOTAL ({len(rows)})", "", "", format_currency(t_b),
            format_currency(t_p), format_currency(t_b - t_p), ""))

    def _report_attendance(self):
        date_from, date_to = self._get_date_range()
        columns = ("meeting", "date", "member_id", "name", "status")
        headings = {"meeting": "Meeting #", "date": "Date",
                    "member_id": "Member ID", "name": "Name", "status": "Status"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = """SELECT a.status, a.meeting_id, m.meeting_number,
                        m.date as meeting_date, mb.member_id, mb.full_name
                 FROM attendance a
                 JOIN meetings m ON a.meeting_id = m.id
                 JOIN members mb ON a.member_id = mb.id
                 WHERE 1=1"""
        params = []
        if date_from:
            sql += " AND m.date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND m.date <= ?"
            params.append(date_to)
        sql += " ORDER BY m.meeting_number, mb.full_name"
        rows = conn.execute(sql, params).fetchall()

        for row in rows:
            self.tree.insert("", "end", values=(
                row["meeting_number"], row["meeting_date"],
                row["member_id"], row["full_name"], row["status"]))
        if not rows:
            self.tree.insert("", "end", values=("—", "No attendance records", "—", "—", "—"))

    def _report_remittance(self):
        date_from, date_to = self._get_date_range()
        columns = ("rem_id", "date", "period", "amount", "method", "ref", "notes")
        headings = {"rem_id": "Remittance ID", "date": "Date",
                    "period": "Period", "amount": "Amount",
                    "method": "Method", "ref": "Reference", "notes": "Notes"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = """SELECT remittance_id, date, period_covered, amount,
                        payment_method, reference_number, notes
                 FROM headquarters_remittances WHERE 1=1"""
        params = []
        if date_from:
            sql += " AND date >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND date <= ?"
            params.append(date_to)
        sql += " ORDER BY date DESC"
        rows = conn.execute(sql, params).fetchall()

        t = 0
        for row in rows:
            t += row["amount"] or 0
            self.tree.insert("", "end", values=(
                row["remittance_id"], row["date"],
                row["period_covered"] or "—",
                format_currency(row["amount"]),
                row["payment_method"] or "—",
                row["reference_number"] or "—",
                row["notes"] or "—"))
        self.tree.insert("", "end", values=(
            "", f"TOTAL ({len(rows)})", "", format_currency(t), "", "", ""))

    def _report_audit_log(self):
        date_from, date_to = self._get_date_range()
        columns = ("timestamp", "user", "action", "details", "ip")
        headings = {"timestamp": "Timestamp", "user": "User",
                    "action": "Action", "details": "Details", "ip": "IP Address"}
        self._configure_tree(columns, headings)

        conn = get_connection()
        sql = "SELECT created_at, user_id, action, details, ip_address FROM audit_logs WHERE 1=1"
        params = []
        if date_from:
            sql += " AND created_at >= ?"
            params.append(date_from)
        if date_to:
            sql += " AND created_at <= ?"
            params.append(date_to + " 23:59:59")
        sql += " ORDER BY created_at DESC"
        rows = conn.execute(sql, params).fetchall()

        for row in rows:
            self.tree.insert("", "end", values=(
                row["created_at"] or "—", row["user_id"] or "System",
                row["action"], row["details"] or "—",
                row["ip_address"] or "—"))
        if not rows:
            self.tree.insert("", "end", values=("—", "—", "No audit logs", "—", "—"))

    # ── PRINT & EXPORT ────────────────────────────────────────────

    def _print_report(self):
        if not self._current_columns:
            messagebox.showinfo("No Data", "Generate a report first.")
            return
        import html as _html
        import webbrowser
        from database.connection import DB_DIR

        date_from, date_to = self._get_date_range()
        headers = [self._current_headings[c] for c in self._current_columns]
        rows = []
        for item in self.tree.get_children():
            rows.append([self.tree.item(item, "values")[i]
                         for i in range(len(self._current_columns))])

        th = "".join(f"<th>{_html.escape(str(h))}</th>" for h in headers)
        trs = "".join(
            "<tr>" + "".join(f"<td>{_html.escape(str(v))}</td>" for v in row) + "</tr>"
            for row in rows)
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        who = (self.current_user or {}).get("username", "")
        period = f"From: {date_from}  To: {date_to}"

        page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{_html.escape(str(self.selected_report or 'Report'))} - ORISUN IBUKUN</title>
<style>body{{font-family:Segoe UI,Arial;margin:30px;color:#222}}
h1{{color:#1565C0;margin-bottom:2px}}.sub{{color:#555;margin:2px 0 14px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #999;
padding:6px 10px;text-align:left;font-size:13px}}th{{background:#1565C0;color:#fff}}
tr:nth-child(even) td{{background:#f2f7fd}}
tr:last-child td{{font-weight:bold;background:#e3f2fd}}
@media print{{.noprint{{display:none}}}}</style></head><body>
<h1>ORISUN IBUKUN (Owode Unit) -- {_html.escape(str(self.selected_report or ''))}</h1>
<p class="sub">{_html.escape(period)} &nbsp;|&nbsp; Generated: {_html.escape(stamp)}{" &nbsp;|&nbsp; By: " + _html.escape(str(who)) if who else ""}</p>
<table><tr>{th}</tr>{trs}</table>
<p class="noprint"><button onclick="window.print()">Print this report</button></p>
</body></html>"""
        out = DB_DIR / "report_print.html"
        out.write_text(page, encoding="utf-8")
        webbrowser.open("file:///" + str(out).replace("\\", "/"))
        messagebox.showinfo("Report Ready",
                            "Report opened in browser.\nUse Print button or Ctrl+P.")

    def _export_csv(self):
        if not self._current_columns:
            messagebox.showinfo("No Data", "Generate a report first.")
            return
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            title="Export Report")
        if not filepath:
            return
        headers = [self._current_headings[c] for c in self._current_columns]
        rows = []
        for item in self.tree.get_children():
            rows.append([self.tree.item(item, "values")[i]
                         for i in range(len(self._current_columns))])
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        messagebox.showinfo("Exported", f"Report exported to:\n{filepath}")
