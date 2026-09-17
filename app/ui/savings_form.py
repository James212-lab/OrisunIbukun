import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from database.connection import get_connection
from database.schema import get_setting
from engines.transaction_engine import (
    record_savings, record_charge_payment,
    record_other_payment, record_withdrawal,
    record_hq_funding, record_expense,
    get_member_financial_summary, get_member_passbook,
    save_passbook_input, reverse_transaction,
)
from utils.validators import validate_amount
from utils.helpers import format_currency, PaginationHelper
from utils.date_picker import pick_date
from errors import handle_error, safe_execute, ValidationError
from constants import PASSBOOK_FEE_COLUMNS
from permissions import has_permission, PERM_REVERSE_TXN
from ui.reverse_dialog import open_reverse_dialog


BLUE = "#1565C0"
WHITE = "#FFFFFF"
LIGHT_BLUE = "#E3F2FD"
DARK_BLUE = "#0D47A1"
GREY = "#F5F5F5"
GREEN = "#2E7D32"
LIGHT_GREEN = "#E8F5E9"


class SavingsForm(tk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, bg=WHITE)
        self.current_user = current_user
        self.selected_member_db_id = None
        self._search_query = ""
        self._search_after_id = None
        self._pagination = PaginationHelper(page_size=50)
        self._edit_entry = None
        self._edit_col_keys = []
        self._custom_fee_cols = []

        self.pack(fill="both", expand=True)
        self.list_frame = tk.Frame(self, bg=WHITE)
        self.detail_frame = tk.Frame(self, bg=WHITE)
        self.edit_frame = tk.Frame(self, bg=WHITE)
        self._build_list()
        self._build_detail()
        self._build_edit()
        self.list_frame.pack(fill="both", expand=True)

    def _show_list(self):
        self.detail_frame.pack_forget()
        self.edit_frame.pack_forget()
        self.list_frame.pack(fill="both", expand=True)
        self._load_members_page(self._search_query)

    def _show_detail(self, db_id):
        self.selected_member_db_id = db_id
        self.list_frame.pack_forget()
        self.edit_frame.pack_forget()
        self.detail_frame.pack(fill="both", expand=True)
        self._load_member_passbook(db_id)

    def _show_edit_view(self):
        if not self.selected_member_db_id:
            return
        self.detail_frame.pack_forget()
        self.list_frame.pack_forget()
        self.edit_frame.pack(fill="both", expand=True)
        self._populate_edit_grid()

    def _hide_edit_view(self):
        self.edit_frame.pack_forget()
        self.detail_frame.pack(fill="both", expand=True)
        self._load_member_passbook(self.selected_member_db_id)

    # ── LIST VIEW ──────────────────────────────────────────────────

    def _build_list(self):
        top_bar = tk.Frame(self.list_frame, bg=WHITE)
        top_bar.pack(fill="x", padx=15, pady=(12, 8))

        tk.Label(top_bar, text="PAYMENTS", font=("Segoe UI", 16, "bold"),
                 fg=BLUE, bg=WHITE).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._schedule_filter())
        tk.Entry(top_bar, textvariable=self.search_var, font=("Segoe UI", 11),
                 width=30, relief="solid", bd=1).pack(side="right")
        tk.Button(top_bar, text="Search", font=("Segoe UI", 10, "bold"),
                  bg=BLUE, fg=WHITE, relief="flat", padx=8, pady=3,
                  command=self._filter_members).pack(side="right", padx=(6, 0))
        tk.Button(top_bar, text="Record In / Out", font=("Segoe UI", 10, "bold"),
                  bg=GREEN, fg=WHITE, relief="flat", padx=10, pady=3,
                  command=self._open_finance_dialog).pack(side="right", padx=(6, 0))

        self.status_var = tk.StringVar(value="")
        tk.Label(self.list_frame, textvariable=self.status_var, font=("Segoe UI", 9),
                 fg="#666666", bg=WHITE, anchor="w").pack(fill="x", padx=15)

        pag_frame = tk.Frame(self.list_frame, bg=WHITE, padx=15)
        pag_frame.pack(fill="x", pady=(8, 12), side="bottom")
        self.prev_btn = tk.Button(pag_frame, text="< Previous", font=("Segoe UI", 9),
                                  bg=LIGHT_BLUE, fg=BLUE, relief="flat", padx=8, pady=3,
                                  state="disabled", command=self._prev_page)
        self.prev_btn.pack(side="left")
        self.page_info_var = tk.StringVar(value="Page 1 of 1")
        tk.Label(pag_frame, textvariable=self.page_info_var, font=("Segoe UI", 9),
                 fg="#666666", bg=WHITE).pack(side="left", padx=12)
        self.next_btn = tk.Button(pag_frame, text="Next >", font=("Segoe UI", 9),
                                  bg=LIGHT_BLUE, fg=BLUE, relief="flat", padx=8, pady=3,
                                  state="disabled", command=self._next_page)
        self.next_btn.pack(side="left")

        cols_frame = tk.Frame(self.list_frame, bg=WHITE, padx=15)
        cols_frame.pack(fill="both", expand=True)

        cols = ("member_id", "full_name", "savings", "active_loan", "outstanding",
                "minutes_owed", "fines_owed")
        self.tree = ttk.Treeview(cols_frame, columns=cols, show="headings", height=22)
        self.tree.heading("member_id", text="Member ID")
        self.tree.heading("full_name", text="Full Name")
        self.tree.heading("savings", text="Savings")
        self.tree.heading("active_loan", text="Active Loan")
        self.tree.heading("outstanding", text="Outstanding")
        self.tree.heading("minutes_owed", text="Minutes Owed")
        self.tree.heading("fines_owed", text="Fines Owed")
        self.tree.column("member_id", width=110, anchor="center")
        self.tree.column("full_name", width=200)
        self.tree.column("savings", width=120, anchor="e")
        self.tree.column("active_loan", width=120, anchor="e")
        self.tree.column("outstanding", width=120, anchor="e")
        self.tree.column("minutes_owed", width=110, anchor="e")
        self.tree.column("fines_owed", width=110, anchor="e")

        tree_scroll = ttk.Scrollbar(cols_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI Symbol", 10), rowheight=30)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.tree.bind("<Double-1>", lambda e: self._on_tree_select())

        self._load_all_members()

    def _on_tree_select(self):
        sel = self.tree.selection()
        if not sel:
            return
        db_id = int(sel[0])
        self._show_detail(db_id)

    def _open_finance_dialog(self):
        """Open Toplevel dialog for recording non-member IN/OUT entries."""
        dlg = tk.Toplevel(self)
        dlg.title("Record In / Out Entry")
        dlg.geometry("450x420")
        dlg.resizable(False, False)
        dlg.configure(bg=WHITE)

        tk.Label(dlg, text="Record In / Out Entry", font=("Segoe UI", 14, "bold"),
                 fg=BLUE, bg=WHITE).pack(pady=(15, 10))

        # Entry type
        tk.Label(dlg, text="Entry Type", font=("Segoe UI", 10), bg=WHITE).pack(anchor=tk.W, padx=20)
        entry_type_var = tk.StringVar(value="HQ Funding")
        type_frame = tk.Frame(dlg, bg=WHITE)
        type_frame.pack(fill="x", padx=20, pady=(0, 8))
        for val in ["HQ Funding", "Expense", "HQ Remittance"]:
            tk.Radiobutton(type_frame, text=val, variable=entry_type_var, value=val,
                           font=("Segoe UI", 10), bg=WHITE).pack(side="left", padx=(0, 10))

        # Amount
        tk.Label(dlg, text="Amount", font=("Segoe UI", 10), bg=WHITE).pack(anchor=tk.W, padx=20)
        amount_var = tk.StringVar()
        tk.Entry(dlg, textvariable=amount_var, font=("Segoe UI", 11),
                 relief="solid", bd=1).pack(fill="x", padx=20, pady=(0, 8))

        # Date
        tk.Label(dlg, text="Date", font=("Segoe UI", 10), bg=WHITE).pack(anchor=tk.W, padx=20)
        date_frame = tk.Frame(dlg, bg=WHITE)
        date_frame.pack(fill="x", padx=20, pady=(0, 8))
        date_var = tk.StringVar(value=datetime.date.today().strftime("%Y-%m-%d"))
        tk.Entry(date_frame, textvariable=date_var, font=("Segoe UI", 11),
                 relief="solid", bd=1, width=16).pack(side="left")
        tk.Button(date_frame, text="Pick", font=("Segoe UI", 9), bg=LIGHT_BLUE, fg=BLUE,
                  relief="flat", command=lambda: pick_date(dlg, date_var)).pack(side="left", padx=6)

        # Description
        tk.Label(dlg, text="Description", font=("Segoe UI", 10), bg=WHITE).pack(anchor=tk.W, padx=20)
        desc_var = tk.StringVar()
        tk.Entry(dlg, textvariable=desc_var, font=("Segoe UI", 11),
                 relief="solid", bd=1).pack(fill="x", padx=20, pady=(0, 8))

        # Category (only for Expense)
        cat_label = tk.Label(dlg, text="Category", font=("Segoe UI", 10), bg=WHITE)
        cat_label.pack(anchor=tk.W, padx=20)
        cat_var = tk.StringVar(value="General")
        cat_entry = tk.Entry(dlg, textvariable=cat_var, font=("Segoe UI", 11),
                             relief="solid", bd=1)
        cat_entry.pack(fill="x", padx=20, pady=(0, 8))

        def _on_type_change(*_args):
            t = entry_type_var.get()
            if t == "Expense":
                cat_label.pack(anchor=tk.W, padx=20)
                cat_entry.pack(fill="x", padx=20, pady=(0, 8))
            else:
                cat_label.pack_forget()
                cat_entry.pack_forget()

        entry_type_var.trace_add("write", _on_type_change)
        _on_type_change()

        def _submit():
            etype = entry_type_var.get()
            try:
                amt = validate_amount(amount_var.get())
            except Exception as e:
                messagebox.showerror("Invalid", str(e), parent=dlg)
                return
            if amt <= 0:
                messagebox.showerror("Invalid", "Amount must be > 0", parent=dlg)
                return
            date_val = date_var.get().strip()
            desc = desc_var.get().strip()
            try:
                if etype == "HQ Funding":
                    record_hq_funding(amt, date=date_val, description=desc,
                                      entered_by=self.current_user["id"])
                elif etype == "Expense":
                    record_expense(amt, date=date_val, category=cat_var.get().strip(),
                                   description=desc, entered_by=self.current_user["id"])
                elif etype == "HQ Remittance":
                    from engines.transaction_engine import record_remittance
                    record_remittance(amt, date=date_val, description=desc,
                                      entered_by=self.current_user["id"])
                messagebox.showinfo("Recorded", f"{etype} of {format_currency(amt)} recorded.", parent=dlg)
                dlg.destroy()
                self._load_members_page()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)

        tk.Button(dlg, text="Save", font=("Segoe UI", 11, "bold"), bg=GREEN, fg=WHITE,
                  relief="flat", padx=20, pady=6, command=_submit).pack(pady=15)

    def _load_all_members(self):
        self._pagination = PaginationHelper(page_size=50)
        self._load_members_page()

    def _load_members_page(self, query: str = ""):
        for item in self.tree.get_children():
            self.tree.delete(item)

        conn = get_connection()
        base_sql = """SELECT m.id, m.member_id, m.full_name,
                             COALESCE(s.total_savings, 0) as savings,
                             COALESCE(l.active_loan, 0) as active_loan,
                             COALESCE(l.outstanding, 0) as outstanding,
                             COALESCE(c.minutes_owed, 0) as minutes_owed,
                             COALESCE(f.fines_owed, 0) as fines_owed
                      FROM members m
                      LEFT JOIN (SELECT sv.member_id, SUM(sv.amount) as total_savings
                                 FROM savings sv
                                 JOIN transactions t ON sv.transaction_id = t.transaction_id
                                 WHERE t.status = 'Posted'
                                 GROUP BY sv.member_id) s
                        ON s.member_id = m.id
                      LEFT JOIN (SELECT member_id,
                                 SUM(CASE WHEN status IN ('Disbursed','Active','Overdue')
                                     THEN principal_amount ELSE 0 END) as active_loan,
                                 SUM(CASE WHEN status IN ('Disbursed','Active','Overdue')
                                     THEN outstanding_principal + outstanding_interest ELSE 0 END) as outstanding
                                 FROM loans GROUP BY member_id) l
                        ON l.member_id = m.id
                      LEFT JOIN (SELECT member_id,
                                 SUM(amount - amount_paid) as minutes_owed
                                 FROM member_charges
                                 WHERE charge_type = 'Minutes Levy' AND status != 'Paid'
                                 GROUP BY member_id) c
                        ON c.member_id = m.id
                      LEFT JOIN (SELECT member_id,
                                 SUM(amount - amount_paid) as fines_owed
                                 FROM member_charges
                                 WHERE charge_type = 'Absence Fine' AND status != 'Paid'
                                 GROUP BY member_id) f
                        ON f.member_id = m.id
                      WHERE m.status = 'Active'"""
        params = []

        if query:
            escaped = (query.replace("\\", "\\\\").replace("%", "\\%")
                            .replace("_", "\\_"))
            like = f"%{escaped}%"
            base_sql += """ AND (LOWER(m.full_name) LIKE ? ESCAPE '\\'
                            OR LOWER(m.member_id) LIKE ? ESCAPE '\\'
                            OR LOWER(m.phone) LIKE ? ESCAPE '\\')"""
            params.extend([like, like, like])

        count_sql = f"SELECT COUNT(*) as cnt FROM ({base_sql})"
        total = conn.execute(count_sql, params).fetchone()["cnt"]

        base_sql += " ORDER BY m.full_name LIMIT ? OFFSET ?"
        params.extend([self._pagination.get_limit(), self._pagination.get_offset()])

        rows = conn.execute(base_sql, params).fetchall()
        for row in rows:
            self.tree.insert("", "end", iid=str(row["id"]),
                             values=(row["member_id"], row["full_name"],
                                     format_currency(row["savings"]),
                                     format_currency(row["active_loan"]),
                                     format_currency(row["outstanding"]),
                                     format_currency(row["minutes_owed"]),
                                     format_currency(row["fines_owed"])))

        self._pagination.set_total_items(total)
        info = self._pagination.get_page_info()
        self.status_var.set(f"Showing {info['start_item']}-{info['end_item']} of {info['total_items']}")
        self.page_info_var.set(f"Page {info['current_page']} of {info['total_pages']}")
        self.prev_btn.config(state="normal" if info["has_prev"] else "disabled")
        self.next_btn.config(state="normal" if info["has_next"] else "disabled")

    def _prev_page(self):
        if self._pagination.prev_page():
            self._load_members_page(self._search_query)

    def _next_page(self):
        if self._pagination.next_page():
            self._load_members_page(self._search_query)

    def _schedule_filter(self):
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(300, self._filter_members)

    def _filter_members(self):
        self._search_after_id = None
        try:
            query = self.search_var.get().strip().lower()
        except Exception:
            return
        self._search_query = query
        try:
            self._pagination.current_page = 1
        except Exception:
            pass
        self._load_members_page(query)

    # ── DETAIL VIEW ────────────────────────────────────────────────

    def _build_detail(self):
        _canvas = tk.Canvas(self.detail_frame, bg=WHITE, highlightthickness=0)
        _scroll = ttk.Scrollbar(self.detail_frame, orient="vertical", command=_canvas.yview)
        _canvas.configure(yscrollcommand=_scroll.set)
        _canvas.pack(side="left", fill="both", expand=True)
        _scroll.pack(side="right", fill="y")
        self._detail_container = tk.Frame(_canvas, bg=WHITE, padx=15, pady=10)
        _win = _canvas.create_window((0, 0), window=self._detail_container, anchor="nw")
        self._detail_container.bind(
            "<Configure>",
            lambda e: _canvas.configure(scrollregion=_canvas.bbox("all"))
            if _canvas.bbox("all") else None)
        _canvas.bind("<Configure>",
                     lambda e: _canvas.itemconfig(_win, width=e.width))
        _canvas.bind("<Enter>", lambda e: _canvas.bind_all(
            "<MouseWheel>", lambda ev: _canvas.yview_scroll(
                int(-1 * (ev.delta / 120)), "units")))
        _canvas.bind("<Leave>", lambda e: _canvas.unbind_all("<MouseWheel>"))

        c = self._detail_container

        navbar = tk.Frame(c, bg=WHITE)
        navbar.pack(fill="x", pady=(0, 8))
        tk.Button(navbar, text="< Back to Payments", font=("Segoe UI", 10, "bold"),
                  bg=LIGHT_BLUE, fg=BLUE, relief="flat", padx=10, pady=4,
                  command=self._show_list).pack(side="left")
        self.detail_title = tk.Label(navbar, text="", font=("Segoe UI", 12, "bold"),
                                     fg=BLUE, bg=WHITE)
        self.detail_title.pack(side="left", padx=(15, 0))
        self.edit_btn = tk.Button(navbar, text="EDIT PASSBOOK", font=("Segoe UI", 10, "bold"),
                                  bg=GREEN, fg=WHITE, relief="flat", padx=12, pady=4,
                                  command=self._show_edit_view)
        self.edit_btn.pack(side="right")
        if has_permission(self.current_user.get("role", ""), PERM_REVERSE_TXN):
            tk.Button(navbar, text="REVERSE", font=("Segoe UI", 10, "bold"),
                      bg="#D32F2F", fg=WHITE, relief="flat", padx=12, pady=4,
                      command=self._reverse_transaction_dialog).pack(side="right", padx=(0, 8))

        info_frame = tk.Frame(c, bg=LIGHT_BLUE, padx=12, pady=8)
        info_frame.pack(fill="x", pady=(0, 8))
        self.info_labels = {}

        row1 = tk.Frame(info_frame, bg=LIGHT_BLUE)
        row1.pack(fill="x", pady=(0, 4))
        for key, label in [("savings", "Savings"),
                           ("active_loan", "Active Loan"), ("outstanding", "Outstanding")]:
            f = tk.Frame(row1, bg=LIGHT_BLUE)
            f.pack(side="left", padx=(0, 18))
            tk.Label(f, text=f"{label}:", font=("Segoe UI", 9, "bold"),
                     fg=BLUE, bg=LIGHT_BLUE).pack(side="left")
            val = tk.Label(f, text="--", font=("Segoe UI", 9, "bold"),
                           fg="#333333", bg=LIGHT_BLUE)
            val.pack(side="left", padx=(4, 0))
            self.info_labels[key] = val

        row2 = tk.Frame(info_frame, bg=LIGHT_BLUE)
        row2.pack(fill="x", pady=(0, 4))
        for key, label in [("minutes_billed", "Min Billed"), ("minutes_paid", "Min Paid"),
                           ("minutes_owed", "Min Outst."),
                           ("absentism_billed", "Abs Billed"), ("absentism_paid", "Abs Paid"),
                           ("absentism_owed", "Abs Outst."),
                           ("fines_billed", "Fine Billed"), ("fines_paid", "Fine Paid"),
                           ("fines_owed", "Fine Outst.")]:
            f = tk.Frame(row2, bg=LIGHT_BLUE)
            f.pack(side="left", padx=(0, 10))
            tk.Label(f, text=f"{label}:", font=("Segoe UI", 9, "bold"),
                     fg=BLUE, bg=LIGHT_BLUE).pack(side="left")
            val = tk.Label(f, text="--", font=("Segoe UI", 9),
                           fg="#333333", bg=LIGHT_BLUE)
            val.pack(side="left", padx=(4, 0))
            self.info_labels[key] = val

        tk.Label(c, text="Passbook", font=("Segoe UI", 13, "bold"),
                 fg=BLUE, bg=WHITE).pack(anchor="w", pady=(8, 4))

        book_frame = tk.Frame(c, bg=WHITE)
        book_frame.pack(fill="both", expand=True)

        self._passbook_cols = ["date", "savings", "loan_repayment"]
        for col_key, label, _ctype in PASSBOOK_FEE_COLUMNS:
            self._passbook_cols.append(col_key)
        self._passbook_cols.extend(["loan_collected", "outstanding", "other", "desc"])

        self.book_tree = ttk.Treeview(book_frame, columns=self._passbook_cols,
                                      show="headings", height=10)
        col_widths = {"date": 85, "savings": 90, "loan_repayment": 90,
                      "loan_collected": 90, "outstanding": 95, "other": 80,
                      "desc": 130}
        for col_key, label, _ctype in PASSBOOK_FEE_COLUMNS:
            col_widths[col_key] = 80

        for col in self._passbook_cols:
            if col == "date":
                txt = "Date"
            elif col == "savings":
                txt = "Savings"
            elif col == "loan_repayment":
                txt = "Loan Repay"
            elif col == "loan_collected":
                txt = "Loan Coll."
            elif col == "outstanding":
                txt = "Loan Outst."
            elif col == "other":
                txt = "Other"
            elif col == "desc":
                txt = "Details"
            else:
                txt = {k: v for k, v, _ in PASSBOOK_FEE_COLUMNS}.get(col, col).title()
            w = col_widths.get(col, 80)
            self.book_tree.heading(col, text=txt)
            self.book_tree.column(col, width=w,
                                  anchor="center" if col not in ("date", "desc") else "w")

        vscroll = ttk.Scrollbar(book_frame, orient="vertical", command=self.book_tree.yview)
        hscroll = ttk.Scrollbar(book_frame, orient="horizontal", command=self.book_tree.xview)
        self.book_tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)
        self.book_tree.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")
        hscroll.pack(side="bottom", fill="x")

    def _load_member_passbook(self, db_id):
        conn = get_connection()
        row = conn.execute("SELECT id, member_id, full_name FROM members WHERE id = ?",
                           (db_id,)).fetchone()
        if not row:
            return

        self.detail_title.config(text=f"{row['full_name']}  ({row['member_id']})")

        summary = get_member_financial_summary(db_id)
        self.info_labels["savings"].config(text=format_currency(summary["total_savings"]))
        self.info_labels["active_loan"].config(text=format_currency(summary["active_loan"]))
        self.info_labels["outstanding"].config(text=format_currency(summary["outstanding"]))

        for item in self.book_tree.get_children():
            self.book_tree.delete(item)

        rows = get_member_passbook(db_id)

        fee_totals = {col_key: 0 for col_key, _, _ in PASSBOOK_FEE_COLUMNS}
        total_savings = 0
        total_loan_repay = 0
        total_loan_collected = 0
        total_other = 0
        last_outstanding = 0

        for r in rows:
            total_savings += r.get("savings", 0) or 0
            total_loan_repay += r.get("loan_repayment", 0) or 0
            total_loan_collected += r.get("loan_collected", 0) or 0
            total_other += r.get("other", 0) or 0
            if r.get("loan_outstanding", "") != "":
                last_outstanding = r["loan_outstanding"] or 0
            for col_key, _, _ in PASSBOOK_FEE_COLUMNS:
                fee_totals[col_key] += r.get(col_key, 0) or 0

            vals = [r["date"],
                    format_currency(r["savings"]) if r["savings"] else "--",
                    format_currency(r["loan_repayment"]) if r["loan_repayment"] else "--"]
            for col_key, _label, _ctype in PASSBOOK_FEE_COLUMNS:
                v = r.get(col_key, 0)
                vals.append(format_currency(v) if v else "--")
            vals.extend([
                format_currency(r["loan_collected"]) if r["loan_collected"] else "--",
                format_currency(r["loan_outstanding"]) if r["loan_outstanding"] != "" else "--",
                format_currency(r["other"]) if r["other"] else "--",
                (r["description"] or "")[:30],
            ])
            self.book_tree.insert("", "end", values=vals)

        self.info_labels["minutes_billed"].config(text=format_currency(summary["minutes_billed"]))
        self.info_labels["minutes_paid"].config(text=format_currency(summary["minutes_paid"]))
        self.info_labels["minutes_owed"].config(text=format_currency(summary["minutes_owed"]))
        self.info_labels["absentism_billed"].config(text=format_currency(summary["absentism_billed"]))
        self.info_labels["absentism_paid"].config(text=format_currency(summary["absentism_paid"]))
        self.info_labels["absentism_owed"].config(text=format_currency(summary["absentism_owed"]))
        self.info_labels["fines_billed"].config(text=format_currency(summary["fines_billed"]))
        self.info_labels["fines_paid"].config(text=format_currency(summary["fines_paid"]))
        self.info_labels["fines_owed"].config(text=format_currency(summary["fines_owed"]))

        if rows:
            totals_vals = ["TOTALS",
                           format_currency(total_savings) if total_savings else "--",
                           format_currency(total_loan_repay) if total_loan_repay else "--"]
            for col_key, _, _ in PASSBOOK_FEE_COLUMNS:
                v = fee_totals[col_key]
                totals_vals.append(format_currency(v) if v else "--")
            totals_vals.extend([
                format_currency(total_loan_collected) if total_loan_collected else "--",
                format_currency(last_outstanding) if last_outstanding else "--",
                format_currency(total_other) if total_other else "--",
                "",
            ])
            self.book_tree.insert("", "end", values=totals_vals, tags=("totals",))
            self.book_tree.tag_configure("totals", font=("Segoe UI", 10, "bold"),
                                         background="#E8F5E9")
        else:
            self.book_tree.insert("", "end", values=("--",) * len(self._passbook_cols))

    # ── EDIT VIEW ──────────────────────────────────────────────────

    def _build_edit(self):
        navbar = tk.Frame(self.edit_frame, bg=WHITE)
        navbar.pack(fill="x", padx=15, pady=(10, 5))
        tk.Button(navbar, text="< Back to Passbook", font=("Segoe UI", 10, "bold"),
                  bg=LIGHT_BLUE, fg=BLUE, relief="flat", padx=10, pady=4,
                  command=self._hide_edit_view).pack(side="left")
        self.edit_title = tk.Label(navbar, text="EDIT PASSBOOK", font=("Segoe UI", 13, "bold"),
                                   fg=BLUE, bg=WHITE)
        self.edit_title.pack(side="left", padx=(15, 0))

        add_frame = tk.Frame(self.edit_frame, bg=WHITE)
        add_frame.pack(fill="x", padx=15, pady=(0, 5))
        tk.Label(add_frame, text="Add Fee Column:", font=("Segoe UI", 10, "bold"),
                 fg=BLUE, bg=WHITE).pack(side="left")
        self._custom_fee_var = tk.StringVar()
        tk.Entry(add_frame, textvariable=self._custom_fee_var, font=("Segoe UI", 10),
                 width=20, relief="solid", bd=1).pack(side="left", padx=(6, 0))
        tk.Button(add_frame, text="Add", font=("Segoe UI", 9, "bold"),
                  bg=BLUE, fg=WHITE, relief="flat", padx=6, pady=2,
                  command=self._add_custom_fee_column).pack(side="left", padx=(6, 0))

        scroll_nav = tk.Frame(self.edit_frame, bg=GREY, padx=15, pady=4)
        scroll_nav.pack(fill="x")
        tk.Button(scroll_nav, text="< Scroll Left", font=("Segoe UI", 9),
                  bg=WHITE, fg=BLUE, relief="flat", padx=6, pady=2,
                  command=lambda: self._scroll_edit_tree(-200)).pack(side="left")
        tk.Button(scroll_nav, text="Scroll Right >", font=("Segoe UI", 9),
                  bg=WHITE, fg=BLUE, relief="flat", padx=6, pady=2,
                  command=lambda: self._scroll_edit_tree(200)).pack(side="left", padx=(6, 0))
        tk.Button(scroll_nav, text="+ NEW PAYMENT", font=("Segoe UI", 9, "bold"),
                  bg=GREEN, fg=WHITE, relief="flat", padx=8, pady=2,
                  command=self._add_new_payment).pack(side="left", padx=(12, 0))
        self._scroll_pos_label = tk.Label(scroll_nav, text="", font=("Segoe UI", 9),
                                          fg="#666666", bg=GREY)
        self._scroll_pos_label.pack(side="right")
        tk.Label(scroll_nav, text="Tip: Double-click any cell to edit. Date cell opens calendar.",
                 font=("Segoe UI", 9, "italic"), fg="#888888", bg=GREY).pack(side="right", padx=(0, 12))

        # BOTTOM: Save button bar — packed FIRST so it always has space
        btn_frame = tk.Frame(self.edit_frame, bg=LIGHT_GREEN, padx=15, pady=10)
        btn_frame.pack(fill="x", side="bottom")
        tk.Button(btn_frame, text="SAVE PASSBOOK", font=("Segoe UI", 13, "bold"),
                  bg=GREEN, fg=WHITE, relief="flat", padx=20, pady=6,
                  command=self._save_passbook).pack(side="right")
        tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 11),
                  bg=WHITE, fg=BLUE, relief="flat", padx=12, pady=4,
                  command=self._hide_edit_view).pack(side="right", padx=(0, 10))

        # TREE: fills remaining space above the button bar
        tree_frame = tk.Frame(self.edit_frame, bg=WHITE, padx=15)
        tree_frame.pack(fill="both", expand=True)

        self.edit_cols = ["date", "savings", "loan_repayment"]
        for col_key, label, _ctype in PASSBOOK_FEE_COLUMNS:
            self.edit_cols.append(col_key)
        self.edit_cols.extend(["loan_collected", "outstanding", "other", "desc"])
        self._edit_col_keys = list(self.edit_cols)

        self.edit_tree = ttk.Treeview(tree_frame, columns=self.edit_cols,
                                      show="headings", height=18)
        self._configure_edit_columns()

        vscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.edit_tree.yview)
        self._hscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.edit_tree.xview)
        self.edit_tree.configure(yscrollcommand=vscroll.set, xscrollcommand=self._hscroll.set)
        self.edit_tree.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")
        self._hscroll.pack(side="bottom", fill="x")

        self.edit_tree.bind("<Double-1>", self._on_edit_cell_click)

    def _configure_edit_columns(self):
        self.edit_tree["columns"] = tuple(self.edit_cols)
        fee_map = {k: v for k, v, _ in PASSBOOK_FEE_COLUMNS}
        for col in self.edit_cols:
            if col == "date":
                self.edit_tree.heading(col, text="Date")
                self.edit_tree.column(col, width=90, anchor="center")
            elif col == "savings":
                self.edit_tree.heading(col, text="Savings")
                self.edit_tree.column(col, width=90, anchor="e")
            elif col == "loan_repayment":
                self.edit_tree.heading(col, text="Loan Repay")
                self.edit_tree.column(col, width=90, anchor="e")
            elif col == "loan_collected":
                self.edit_tree.heading(col, text="Loan Coll.")
                self.edit_tree.column(col, width=90, anchor="e")
            elif col == "outstanding":
                self.edit_tree.heading(col, text="Loan Outst.")
                self.edit_tree.column(col, width=90, anchor="e")
            elif col == "other":
                self.edit_tree.heading(col, text="Other")
                self.edit_tree.column(col, width=80, anchor="e")
            elif col == "desc":
                self.edit_tree.heading(col, text="Details")
                self.edit_tree.column(col, width=130, anchor="w")
            else:
                label = fee_map.get(col, col.replace("_", " ").title())
                self.edit_tree.heading(col, text=label)
                self.edit_tree.column(col, width=85, anchor="center")

    def _add_custom_fee_column(self):
        name = self._custom_fee_var.get().strip()
        if not name:
            return
        col_id = f"custom_{name.lower().replace(' ', '_')}"
        if col_id in self.edit_cols:
            return
        self.edit_cols.insert(-1, col_id)
        self._edit_col_keys.append(col_id)
        self._custom_fee_cols.append((col_id, name))
        self._configure_edit_columns()
        self._custom_fee_var.set("")

    def _add_new_payment(self):
        """Open calendar picker and insert a new empty row for a new meeting date."""
        date_var = tk.StringVar(value=datetime.date.today().isoformat())

        def on_choose():
            new_date = date_var.get()
            if not new_date:
                return
            # Check if a row with this date already exists
            for item in self.edit_tree.get_children():
                vals = self.edit_tree.item(item, "values")
                if vals[0] == new_date:
                    messagebox.showinfo("Duplicate Date",
                                        f"A row for {new_date} already exists.\n"
                                        "Edit that row instead.")
                    try:
                        win.destroy()
                    except Exception:
                        pass
                    return
            # Insert new empty row
            empty_vals = [""] * len(self.edit_cols)
            empty_vals[0] = new_date
            new_item = self.edit_tree.insert("", "end", values=empty_vals)
            # Scroll to the new row
            self.edit_tree.see(new_item)
            self.edit_tree.selection_set(new_item)
            self._update_scroll_pos()
            try:
                win.destroy()
            except Exception:
                pass

        try:
            win = tk.Toplevel(self.edit_frame)
            win.title("New Payment — Select Meeting Date")
            win.resizable(False, False)
            win.transient(self.edit_frame)
            win.grab_set()

            from tkcalendar import Calendar
            today = datetime.date.today()
            cal = Calendar(win, selectmode="day", year=today.year,
                           month=today.month, day=today.day,
                           date_pattern="yyyy-mm-dd")
            cal.pack(padx=15, pady=15)

            def pick_and_close():
                date_var.set(cal.get_date())
                on_choose()

            tk.Button(win, text="Add Row for This Date", font=("Segoe UI", 11, "bold"),
                      bg=GREEN, fg=WHITE, command=pick_and_close).pack(pady=(0, 12))
        except ImportError:
            # Fallback: manual date entry
            date_str = tk.simpledialog.askstring(
                "New Payment",
                "Enter meeting date (YYYY-MM-DD):",
                parent=self.edit_frame)
            if date_str:
                date_var.set(date_str.strip())
                on_choose()
        except Exception:
            pass

    def _populate_edit_grid(self):
        for item in self.edit_tree.get_children():
            self.edit_tree.delete(item)

        conn = get_connection()
        row = conn.execute("SELECT member_id, full_name FROM members WHERE id = ?",
                           (self.selected_member_db_id,)).fetchone()
        if row:
            self.edit_title.config(
                text=f"EDIT PASSBOOK — {row['full_name']} ({row['member_id']})")

        rows = get_member_passbook(self.selected_member_db_id)
        for r in rows:
            vals = [r["date"],
                    str(int(r["savings"])) if r.get("savings") else "",
                    str(int(r["loan_repayment"])) if r.get("loan_repayment") else ""]
            for col_key, _label, _ctype in PASSBOOK_FEE_COLUMNS:
                v = r.get(col_key, 0)
                vals.append(str(int(v)) if v else "")
            vals.extend([
                str(int(r["loan_collected"])) if r.get("loan_collected") else "",
                str(int(r["loan_outstanding"])) if r.get("loan_outstanding") != "" else "",
                str(int(r["other"])) if r.get("other") else "",
                r.get("description", "")[:30],
            ])
            self.edit_tree.insert("", "end", values=vals)

        self._update_scroll_pos()

    def _scroll_edit_tree(self, amount):
        self.edit_tree.xview_scroll(amount, "units")
        self.after(50, self._update_scroll_pos)

    def _update_scroll_pos(self):
        try:
            first, last = self.edit_tree.xview()
            total_cols = len(self.edit_cols)
            left_col = int(first * total_cols)
            right_col = int(last * total_cols)
            self._scroll_pos_label.config(
                text=f"Columns {left_col + 1}–{min(right_col, total_cols)} of {total_cols}")
        except Exception:
            self._scroll_pos_label.config(text="")

    def _on_edit_cell_click(self, event):
        region = self.edit_tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        col_id = self.edit_tree.identify_column(event.x)
        row_id = self.edit_tree.identify_row(event.y)
        if not col_id or not row_id:
            return

        col_index = int(col_id.replace("#", "")) - 1
        cols = list(self.edit_tree["columns"])
        if col_index >= len(cols):
            return
        clicked_col = cols[col_index]

        if clicked_col == "date":
            self._open_date_picker(row_id, col_index)
            return

        if clicked_col == "desc":
            return

        if self._edit_entry:
            self._commit_edit()

        item = self.edit_tree.item(row_id)
        current_val = item["values"][col_index]

        bbox = self.edit_tree.bbox(row_id, col_id)
        if not bbox:
            return
        x, y, w, h = bbox

        self._edit_entry = tk.Entry(self.edit_tree, font=("Segoe UI", 10),
                                    width=w // 8, relief="solid", bd=2)
        self._edit_entry.place(x=x, y=y, width=w, height=h)
        self._edit_entry.insert(0, str(current_val) if current_val and current_val != "--" else "")
        self._edit_entry.select_range(0, tk.END)
        self._edit_entry.focus_set()

        self._edit_row_id = row_id
        self._edit_col_index = col_index

        self._edit_entry.bind("<Return>", lambda e: self._commit_edit())
        self._edit_entry.bind("<Escape>", lambda e: self._cancel_edit())
        self._edit_entry.bind("<FocusOut>", lambda e: self._commit_edit())

    def _open_date_picker(self, row_id, col_index):
        item = self.edit_tree.item(row_id)
        current_date = item["values"][col_index]

        date_var = tk.StringVar(value=str(current_date) if current_date else "")

        def on_date_selected():
            new_date = date_var.get()
            if new_date:
                vals = list(self.edit_tree.item(row_id, "values"))
                vals[col_index] = new_date
                self.edit_tree.item(row_id, values=vals)

        try:
            win = tk.Toplevel(self.edit_frame)
            win.title("Select Date")
            win.resizable(False, False)
            win.transient(self.edit_frame)
            win.grab_set()

            try:
                initial = datetime.date.fromisoformat(str(current_date))
            except (ValueError, TypeError):
                initial = datetime.date.today()

            from tkcalendar import Calendar
            cal = Calendar(win, selectmode="day", year=initial.year,
                           month=initial.month, day=initial.day,
                           date_pattern="yyyy-mm-dd")
            cal.pack(padx=15, pady=15)

            def choose():
                date_var.set(cal.get_date())
                on_date_selected()
                try:
                    win.destroy()
                except Exception:
                    pass

            tk.Button(win, text="Use This Date", font=("Segoe UI", 11, "bold"),
                      bg=BLUE, fg=WHITE, command=choose).pack(pady=(0, 12))
        except ImportError:
            messagebox.showinfo(
                "Calendar Unavailable",
                "Type the date as YYYY-MM-DD.\nInstall 'tkcalendar' for a picker.")
        except Exception:
            pass

    def _commit_edit(self):
        if not self._edit_entry:
            return
        new_val = self._edit_entry.get().strip()
        self._edit_entry.destroy()
        self._edit_entry = None

        vals = list(self.edit_tree.item(self._edit_row_id, "values"))
        vals[self._edit_col_index] = new_val
        self.edit_tree.item(self._edit_row_id, values=vals)

    def _cancel_edit(self):
        if self._edit_entry:
            self._edit_entry.destroy()
            self._edit_entry = None

    def _save_passbook(self):
        if not self.selected_member_db_id:
            return

        self._commit_edit()

        conn = get_connection()
        row = conn.execute("SELECT full_name FROM members WHERE id = ?",
                           (self.selected_member_db_id,)).fetchone()
        member_name = row["full_name"] if row else "Member"

        changed = False
        for item in self.edit_tree.get_children():
            vals = self.edit_tree.item(item, "values")
            date_str = vals[0]
            if not date_str or date_str == "--":
                continue

            # Save charge-type categories (Minutes, ICT, AGM, etc.)
            categories = {}
            for col_key in self._edit_col_keys:
                if col_key in ("date", "desc", "savings", "loan_repayment",
                               "loan_collected", "outstanding", "other"):
                    continue
                idx = self.edit_cols.index(col_key)
                val = vals[idx] if idx < len(vals) else ""
                categories[col_key] = val if val and val != "--" else ""

            ok = save_passbook_input(
                self.selected_member_db_id, date_str, categories,
                payment_method="Cash",
                entered_by=self.current_user.get("id"),
                allow_backdate=True)
            if ok:
                changed = True

            # Handle Savings column
            savings_idx = self.edit_cols.index("savings") if "savings" in self.edit_cols else -1
            if savings_idx >= 0 and savings_idx < len(vals):
                raw_sav = vals[savings_idx]
                try:
                    sav_amt = float(str(raw_sav).replace(",", "").replace("₦", ""))
                except (ValueError, TypeError):
                    sav_amt = 0
                self._sync_passbook_txn(date_str, sav_amt, "Savings")

            # Handle Other column
            other_idx = self.edit_cols.index("other") if "other" in self.edit_cols else -1
            if other_idx >= 0 and other_idx < len(vals):
                raw_oth = vals[other_idx]
                try:
                    oth_amt = float(str(raw_oth).replace(",", "").replace("₦", ""))
                except (ValueError, TypeError):
                    oth_amt = 0
                self._sync_passbook_txn(date_str, oth_amt, "Other")

        if changed:
            messagebox.showinfo("Saved",
                                f"Passbook updated for {member_name}.\n"
                                "You can continue editing or add new payments.")
        else:
            messagebox.showinfo("No Changes", "No amounts were changed.")

        # Stay in edit view — refresh the grid so admin can continue working
        self._populate_edit_grid()

    def _sync_passbook_txn(self, date_str, new_amt, txn_type):
        """Sync a savings/other passbook column with the transactions table.

        Finds existing transaction on this date for this member+type.
        If amount differs: reverse old, create new.
        If amount is 0 and old exists: reverse old.
        """
        from engines.transaction_engine import (
            record_savings, record_other_payment, reverse_transaction,
        )
        member_id = self.selected_member_db_id
        conn = get_connection()

        # Find existing transaction on this date for this type
        existing = conn.execute(
            """SELECT t.transaction_id, t.amount
               FROM transactions t
               WHERE t.member_id = ? AND t.transaction_type = ?
                 AND t.date = ? AND t.status = 'Posted'
               LIMIT 1""",
            (member_id, txn_type, date_str),
        ).fetchone()

        old_amt = existing["amount"] if existing else 0
        if abs(old_amt - new_amt) < 0.01:
            return  # No change

        # Reverse old transaction if it exists
        if existing:
            try:
                reverse_transaction(
                    existing["transaction_id"],
                    reason="Passbook edit",
                    reversed_by=self.current_user.get("id"),
                )
            except Exception:
                pass

        # Create new transaction if amount > 0
        if new_amt > 0:
            if txn_type == "Savings":
                record_savings(
                    member_id, new_amt,
                    entered_by=self.current_user.get("id"),
                    date=date_str, allow_backdate=True,
                )
            elif txn_type == "Other":
                record_other_payment(
                    member_id, new_amt,
                    entered_by=self.current_user.get("id"),
                    date=date_str, allow_backdate=True,
                )

    def _reverse_transaction_dialog(self):
        if not self.selected_member_db_id:
            return
        open_reverse_dialog(
            parent=self.detail_frame,
            member_id=self.selected_member_db_id,
            current_user=self.current_user,
            on_success=lambda: self._show_detail(self.selected_member_db_id),
        )

    # ── PUBLIC API ─────────────────────────────────────────────────

    def load_member(self, member_db_id: int) -> bool:
        """Load a member's passbook (used by View Booklet from Members tab)."""
        conn = get_connection()
        row = conn.execute(
            "SELECT id, member_id, full_name FROM members WHERE id = ?",
            (member_db_id,)).fetchone()
        if not row:
            return False
        self._show_detail(row["id"])
        return True
