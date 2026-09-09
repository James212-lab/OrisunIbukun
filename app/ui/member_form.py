import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
import os
import shutil
from database.connection import get_connection, DB_DIR
from database.schema import get_setting
from engines.transaction_engine import (
    register_member, get_member_financial_summary, get_member_passbook,
    record_savings, record_repayment
)
from constants import PASSBOOK_FEE_COLUMNS
from utils.validators import validate_required, validate_amount, validate_name
from utils.helpers import format_currency, PaginationHelper
from errors import handle_error, safe_execute, ValidationError


class MemberForm(tk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, bg="#FFFFFF")
        self.current_user = current_user
        self.selected_member_db_id = None
        self._search_query = ""
        self._search_after_id = None
        self._grid_rows = []
        self._pagination = PaginationHelper(page_size=50)
        self._card_images = []
        self.pack(fill="both", expand=True)
        self._build_ui()

    def _build_ui(self):
        self.list_frame = tk.Frame(self, bg="#FFFFFF")
        self.detail_frame = tk.Frame(self, bg="#FFFFFF")
        self._build_list()
        self._build_detail()
        self.list_frame.pack(fill="both", expand=True)

    def _show_list(self):
        self.detail_frame.pack_forget()
        self.list_frame.pack(fill="both", expand=True)
        self._load_members_page(self._search_query)

    def _show_detail(self, db_id):
        self.selected_member_db_id = db_id
        self.list_frame.pack_forget()
        self.detail_frame.pack(fill="both", expand=True)
        self._load_member_profile(db_id)

    def _build_list(self):
        top_bar = tk.Frame(self.list_frame, bg="#FFFFFF")
        top_bar.pack(fill="x", padx=15, pady=(12, 8))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._schedule_filter())
        tk.Entry(top_bar, textvariable=self.search_var, font=("Segoe UI", 11),
                 width=35, relief="solid", bd=1).pack(side="left")
        tk.Button(top_bar, text="Search", font=("Segoe UI", 10, "bold"),
                  bg="#1565C0", fg="#FFFFFF", relief="flat", padx=10, pady=3,
                  command=self._filter_members).pack(side="left", padx=(6, 0))

        self.status_filter_var = tk.StringVar(value="All")
        ttk.Combobox(top_bar, textvariable=self.status_filter_var,
                     values=["All", "Active", "Suspended", "Absconded", "Exited"],
                     state="readonly", font=("Segoe UI", 10), width=12).pack(side="left", padx=(10, 0))
        self.status_filter_var.trace_add("write", lambda *a: self._filter_members())

        tk.Button(top_bar, text="+ Register New Member", font=("Segoe UI", 10, "bold"),
                  bg="#2E7D32", fg="#FFFFFF", relief="flat", padx=12, pady=4,
                  command=self._open_register_dialog).pack(side="right")
        tk.Button(top_bar, text="Categories", font=("Segoe UI", 10),
                  bg="#E3F2FD", fg="#1565C0", relief="flat", padx=10, pady=4,
                  command=self._open_categories_dialog).pack(side="right", padx=(0, 8))

        self.status_var = tk.StringVar(value="")
        tk.Label(self.list_frame, textvariable=self.status_var, font=("Segoe UI", 9),
                 fg="#666666", bg="#FFFFFF", anchor="w").pack(fill="x", padx=15)

        cols_frame = tk.Frame(self.list_frame, bg="#FFFFFF", padx=15)
        cols_frame.pack(fill="both", expand=True)

        cols = ("member_id", "full_name", "phone", "status", "date_joined")
        self.tree = ttk.Treeview(cols_frame, columns=cols, show="headings", height=22)
        self.tree.heading("member_id", text="Member ID")
        self.tree.heading("full_name", text="Full Name")
        self.tree.heading("phone", text="Phone")
        self.tree.heading("status", text="Status")
        self.tree.heading("date_joined", text="Date Joined")
        self.tree.column("member_id", width=110, anchor="center")
        self.tree.column("full_name", width=220)
        self.tree.column("phone", width=140, anchor="center")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("date_joined", width=110, anchor="center")

        tree_scroll = ttk.Scrollbar(cols_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=32)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.tree.tag_configure("Active", foreground="#2E7D32")
        self.tree.tag_configure("Suspended", foreground="#E65100")
        self.tree.tag_configure("Absconded", foreground="#C62828")
        self.tree.tag_configure("Exited", foreground="#757575")

        self.tree.bind("<Double-1>", lambda e: self._on_tree_select())

        pag_frame = tk.Frame(self.list_frame, bg="#FFFFFF", padx=15)
        pag_frame.pack(fill="x", pady=(8, 12))
        self.prev_btn = tk.Button(pag_frame, text="< Previous", font=("Segoe UI", 9),
                                  bg="#E3F2FD", fg="#1565C0", relief="flat", padx=10, pady=3,
                                  state="disabled", command=self._prev_page)
        self.prev_btn.pack(side="left")
        self.page_info_var = tk.StringVar(value="Page 1 of 1")
        tk.Label(pag_frame, textvariable=self.page_info_var, font=("Segoe UI", 9),
                 fg="#666666", bg="#FFFFFF").pack(side="left", padx=15)
        self.next_btn = tk.Button(pag_frame, text="Next >", font=("Segoe UI", 9),
                                  bg="#E3F2FD", fg="#1565C0", relief="flat", padx=10, pady=3,
                                  state="disabled", command=self._next_page)
        self.next_btn.pack(side="left")

        self._load_all_members()

    def _on_tree_select(self):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        db_id = iid if isinstance(iid, int) else int(iid)
        self._show_detail(db_id)

    def _build_detail(self):
        _canvas = tk.Canvas(self.detail_frame, bg="#FFFFFF", highlightthickness=0)
        _scroll = ttk.Scrollbar(self.detail_frame, orient="vertical", command=_canvas.yview)
        _canvas.configure(yscrollcommand=_scroll.set)
        _canvas.pack(side="left", fill="both", expand=True)
        _scroll.pack(side="right", fill="y")
        self._detail_container = tk.Frame(_canvas, bg="#FFFFFF", padx=20, pady=15)
        _win = _canvas.create_window((0, 0), window=self._detail_container, anchor="nw")
        self._detail_container.bind("<Configure>",
                                   lambda e: _canvas.configure(scrollregion=_canvas.bbox("all")))
        _canvas.bind("<Configure>",
                     lambda e: _canvas.itemconfig(_win, width=e.width))
        _canvas.bind("<Enter>", lambda e: _canvas.bind_all(
            "<MouseWheel>", lambda ev: _canvas.yview_scroll(
                int(-1 * (ev.delta / 120)), "units")))
        _canvas.bind("<Leave>", lambda e: _canvas.unbind_all("<MouseWheel>"))

        c = self._detail_container

        navbar = tk.Frame(c, bg="#FFFFFF")
        navbar.pack(fill="x", pady=(0, 8))
        tk.Button(navbar, text="< Back to Members", font=("Segoe UI", 10, "bold"),
                  bg="#E3F2FD", fg="#1565C0", relief="flat", padx=10, pady=4,
                  command=self._show_list).pack(side="left")
        tk.Button(navbar, text="< Prev Member", font=("Segoe UI", 10),
                  bg="#E3F2FD", fg="#1565C0", relief="flat", padx=10, pady=4,
                  command=lambda: self._step_member(-1)).pack(side="left", padx=(10, 0))
        tk.Button(navbar, text="Next Member >", font=("Segoe UI", 10),
                  bg="#E3F2FD", fg="#1565C0", relief="flat", padx=10, pady=4,
                  command=lambda: self._step_member(1)).pack(side="left", padx=(6, 0))

        top_row = tk.Frame(c, bg="#FFFFFF")
        top_row.pack(fill="x", pady=(0, 10))
        self.profile_photo_label = tk.Label(top_row, bg="#E3F2FD", width=28, height=16,
                                            text="No photo", font=("Segoe UI", 10),
                                            fg="#666666", relief="solid", bd=1)
        self.profile_photo_label.pack(side="left", padx=(0, 15))
        self._photo_img = None
        name_col = tk.Frame(top_row, bg="#FFFFFF")
        name_col.pack(side="left", fill="x", expand=True)
        self.profile_name_label = tk.Label(name_col, text="", font=("Segoe UI", 14, "bold"),
                                           fg="#333333", bg="#FFFFFF")
        self.profile_name_label.pack(anchor="w")
        self.profile_id_label = tk.Label(name_col, text="", font=("Segoe UI", 11),
                                         fg="#666666", bg="#FFFFFF")
        self.profile_id_label.pack(anchor="w")

        detail_frame = tk.Frame(c, bg="#FFFFFF")
        detail_frame.pack(fill="x")
        self.profile_details = {}
        for field in ["Phone", "Address", "Status", "Date Joined", "DOB",
                      "Gender", "Occupation", "Email", "Next of Kin",
                      "NOK Phone", "ID Type", "ID Number", "Photo"]:
            row = tk.Frame(detail_frame, bg="#FFFFFF")
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"{field}:", font=("Segoe UI", 10, "bold"),
                     fg="#1565C0", bg="#FFFFFF", width=14, anchor="w").pack(side="left")
            val = tk.Label(row, text="--", font=("Segoe UI", 10), fg="#333333",
                           bg="#FFFFFF", anchor="w")
            val.pack(side="left", padx=(4, 0))
            self.profile_details[field] = val

        tk.Frame(c, height=2, bg="#E3F2FD").pack(fill="x", pady=(12, 8))
        tk.Label(c, text="Financial Summary", font=("Segoe UI", 13, "bold"),
                 fg="#1565C0", bg="#FFFFFF").pack(anchor="w", pady=(0, 6))
        self.finance_frame = tk.Frame(c, bg="#FFFFFF")
        self.finance_frame.pack(fill="x")
        self.finance_labels = {}
        for display, key in [("Total Paid", "total_paid"), ("Savings", "total_savings"),
                              ("Shares", "total_shares"), ("Active Loan", "active_loan"),
                              ("Loan Paid", "loan_paid"), ("Outstanding", "outstanding"),
                              ("Minutes Owed", "minutes_owed"), ("Fines Owed", "fines_owed"),
                              ("Other Charges Owed", "other_owed"),
                              ("Charges Paid", "charges_paid")]:
            row = tk.Frame(self.finance_frame, bg="#FFFFFF")
            row.pack(fill="x", pady=1)
            tk.Label(row, text=f"{display}:", font=("Segoe UI", 10, "bold"),
                     fg="#1565C0", bg="#FFFFFF", width=16, anchor="w").pack(side="left")
            val = tk.Label(row, text=format_currency(0), font=("Segoe UI", 10),
                           fg="#333333", bg="#FFFFFF", anchor="w")
            val.pack(side="left", padx=(4, 0))
            self.finance_labels[key] = val

        btn_frame = tk.Frame(c, bg="#FFFFFF")
        btn_frame.pack(fill="x", pady=(12, 0))
        self.btn_view_booklet = tk.Button(btn_frame, text="View Booklet",
                                          font=("Segoe UI", 10), bg="#1565C0",
                                          fg="#FFFFFF", relief="flat", padx=10, pady=4,
                                          state="disabled", command=self._view_booklet)
        self.btn_view_booklet.pack(side="left")
        self.btn_record_savings = tk.Button(btn_frame, text="Record Savings",
                                            font=("Segoe UI", 10), bg="#1565C0",
                                            fg="#FFFFFF", relief="flat", padx=10, pady=4,
                                            state="disabled", command=self._record_savings)
        self.btn_record_savings.pack(side="left", padx=(8, 0))
        self.btn_record_repayment = tk.Button(btn_frame, text="Record Repayment",
                                              font=("Segoe UI", 10), bg="#1565C0",
                                              fg="#FFFFFF", relief="flat", padx=10, pady=4,
                                              state="disabled", command=self._record_repayment)
        self.btn_record_repayment.pack(side="left", padx=(8, 0))
        self.btn_record_payment = tk.Button(btn_frame, text="Record Payment",
                                            font=("Segoe UI", 10), bg="#E65100",
                                            fg="#FFFFFF", relief="flat", padx=10, pady=4,
                                            state="disabled", command=self._record_payment)
        self.btn_record_payment.pack(side="left", padx=(8, 0))
        self.btn_edit_details = tk.Button(btn_frame, text="Edit Details",
                                          font=("Segoe UI", 10), bg="#2E7D32",
                                          fg="#FFFFFF", relief="flat", padx=10, pady=4,
                                          state="disabled", command=self._edit_details)
        self.btn_edit_details.pack(side="left", padx=(8, 0))
        self.btn_print_card = tk.Button(btn_frame, text="Print Member Card",
                                         font=("Segoe UI", 10), bg="#FFFFFF",
                                         fg="#1565C0", relief="solid", bd=1, padx=10, pady=4,
                                         state="disabled", command=self._print_card)
        self.btn_print_card.pack(side="left", padx=(8, 0))
        self.btn_mark_exited = tk.Button(btn_frame, text="Mark as Exited",
                                          font=("Segoe UI", 10), bg="#C62828",
                                          fg="#FFFFFF", relief="flat", padx=10, pady=4,
                                          state="disabled", command=self._mark_as_exited)
        self.btn_mark_exited.pack(side="left", padx=(8, 0))

        cat_row = tk.Frame(c, bg="#FFFFFF")
        cat_row.pack(fill="x", pady=(8, 0))
        tk.Label(cat_row, text="Category:", font=("Segoe UI", 10, "bold"),
                 fg="#1565C0", bg="#FFFFFF").pack(side="left")
        self.quick_status_var = tk.StringVar()
        self.quick_status_combo = ttk.Combobox(cat_row, textvariable=self.quick_status_var,
                                              values=["Active", "Suspended", "Absconded"],
                                              state="disabled", font=("Segoe UI", 10), width=12)
        self.quick_status_combo.pack(side="left", padx=(6, 0))
        self.btn_apply_status = tk.Button(cat_row, text="Save Category",
                                          font=("Segoe UI", 10, "bold"),
                                          bg="#1565C0", fg="#FFFFFF", relief="flat",
                                          padx=8, pady=3, state="disabled",
                                          command=self._apply_quick_status)
        self.btn_apply_status.pack(side="left", padx=(6, 0))

        tk.Frame(c, height=2, bg="#E3F2FD").pack(fill="x", pady=(12, 8))

        info_frame = tk.Frame(c, bg="#E3F2FD", padx=12, pady=8)
        info_frame.pack(fill="x", pady=(0, 8))
        self.passbook_info_labels = {}

        info_row1 = tk.Frame(info_frame, bg="#E3F2FD")
        info_row1.pack(fill="x", pady=(0, 4))
        for key, label in [("savings", "Savings"), ("shares", "Shares"),
                           ("active_loan", "Active Loan"), ("outstanding", "Outstanding")]:
            f = tk.Frame(info_row1, bg="#E3F2FD")
            f.pack(side="left", padx=(0, 18))
            tk.Label(f, text=f"{label}:", font=("Segoe UI", 9, "bold"),
                     fg="#1565C0", bg="#E3F2FD").pack(side="left")
            val = tk.Label(f, text="--", font=("Segoe UI", 9, "bold"),
                           fg="#333333", bg="#E3F2FD")
            val.pack(side="left", padx=(4, 0))
            self.passbook_info_labels[key] = val

        info_row2 = tk.Frame(info_frame, bg="#E3F2FD")
        info_row2.pack(fill="x")
        for key, label in [("minutes_owed", "Minutes"), ("ict_owed", "ICT"),
                           ("agm_owed", "AGM"), ("lateness_owed", "Lateness"),
                           ("absentism_owed", "Absentism"), ("fines_owed", "Fines")]:
            f = tk.Frame(info_row2, bg="#E3F2FD")
            f.pack(side="left", padx=(0, 14))
            tk.Label(f, text=f"{label}:", font=("Segoe UI", 9, "bold"),
                     fg="#1565C0", bg="#E3F2FD").pack(side="left")
            val = tk.Label(f, text="--", font=("Segoe UI", 9),
                           fg="#333333", bg="#E3F2FD")
            val.pack(side="left", padx=(4, 0))
            self.passbook_info_labels[key] = val

        tk.Label(c, text="Passbook", font=("Segoe UI", 13, "bold"),
                 fg="#1565C0", bg="#FFFFFF").pack(anchor="w", pady=(8, 4))
        book_frame = tk.Frame(c, bg="#FFFFFF")
        book_frame.pack(fill="both", expand=True)

        self._passbook_cols = ["date", "savings", "loan_repayment"]
        for col_key, label, _ctype in PASSBOOK_FEE_COLUMNS:
            self._passbook_cols.append(col_key)
        self._passbook_cols.extend(["loan_collected", "outstanding", "other", "method", "desc"])

        self.book_tree = ttk.Treeview(book_frame, columns=self._passbook_cols,
                                      show="headings", height=10)
        col_widths = {"date": 85, "savings": 90, "loan_repayment": 90,
                      "loan_collected": 90, "outstanding": 95, "other": 80,
                      "method": 85, "desc": 130}
        for col_key, _label, _ctype in PASSBOOK_FEE_COLUMNS:
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
            elif col == "method":
                txt = "Method"
            elif col == "desc":
                txt = "Details"
            else:
                txt = {k: v for k, v, _ in PASSBOOK_FEE_COLUMNS}.get(col, col).title()
            w = col_widths.get(col, 80)
            self.book_tree.heading(col, text=txt)
            self.book_tree.column(col, width=w,
                                  anchor="center" if col not in ("date", "desc") else "w")

        book_scroll = ttk.Scrollbar(book_frame, orient="vertical",
                                    command=self.book_tree.yview)
        self.book_tree.configure(yscrollcommand=book_scroll.set)
        self.book_tree.pack(side="left", fill="both", expand=True)
        book_scroll.pack(side="right", fill="y")

    def _step_member(self, direction: int):
        if not self.selected_member_db_id:
            return
        try:
            children = self.tree.get_children()
            ids = [int(c) for c in children]
        except Exception:
            return
        try:
            i = ids.index(self.selected_member_db_id)
        except ValueError:
            return
        j = (i + direction) % len(ids)
        self._show_detail(ids[j])

    def _load_passbook(self, db_id: int):
        for item in self.book_tree.get_children():
            self.book_tree.delete(item)

        summary = get_member_financial_summary(db_id)
        self.passbook_info_labels["savings"].config(text=format_currency(summary["total_savings"]))
        self.passbook_info_labels["shares"].config(text=format_currency(summary["total_shares"]))
        self.passbook_info_labels["active_loan"].config(text=format_currency(summary["active_loan"]))
        self.passbook_info_labels["outstanding"].config(text=format_currency(summary["outstanding"]))

        try:
            rows = get_member_passbook(db_id)
        except Exception:
            rows = []

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
                r.get("method") or "--",
                (r["description"] or "")[:30],
            ])
            self.book_tree.insert("", "end", values=vals)

        self.passbook_info_labels["minutes_owed"].config(text=format_currency(fee_totals.get("minutes", 0)))
        self.passbook_info_labels["ict_owed"].config(text=format_currency(fee_totals.get("ict", 0)))
        self.passbook_info_labels["agm_owed"].config(text=format_currency(fee_totals.get("agm", 0)))
        self.passbook_info_labels["lateness_owed"].config(text=format_currency(fee_totals.get("lateness", 0)))
        self.passbook_info_labels["absentism_owed"].config(text=format_currency(fee_totals.get("absentism", 0)))
        self.passbook_info_labels["fines_owed"].config(text=format_currency(fee_totals.get("fines", 0)))

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
                "", "",
            ])
            self.book_tree.insert("", "end", values=totals_vals, tags=("totals",))
            self.book_tree.tag_configure("totals", font=("Segoe UI", 10, "bold"),
                                         background="#E8F5E9")
        else:
            self.book_tree.insert("", "end", values=("--",) * len(self._passbook_cols))

    def _load_all_members(self):
        self._pagination = PaginationHelper(page_size=50)
        self._load_members_page()

    def _load_members_page(self, query: str = ""):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._grid_rows = []

        conn = get_connection()
        status_filter = self.status_filter_var.get() if hasattr(self, "status_filter_var") else "All"
        base_sql = "SELECT id, member_id, full_name, phone, status, date_joined FROM members WHERE 1=1"
        count_sql = "SELECT COUNT(*) as cnt FROM members WHERE 1=1"
        params = []
        count_params = []

        if status_filter and status_filter != "All":
            base_sql += " AND status = ?"
            count_sql += " AND status = ?"
            params.append(status_filter)
            count_params.append(status_filter)

        if query:
            escaped = (query.replace("\\", "\\\\").replace("%", "\\%")
                            .replace("_", "\\_"))
            like = f"%{escaped}%"
            like_clause = ("(LOWER(full_name) LIKE ? ESCAPE '\\' "
                           "OR LOWER(member_id) LIKE ? ESCAPE '\\' "
                           "OR LOWER(phone) LIKE ? ESCAPE '\\')")
            base_sql += " AND " + like_clause
            count_sql += " AND " + like_clause
            params.extend([like, like, like])
            count_params.extend([like, like, like])

        base_sql += " ORDER BY full_name LIMIT ? OFFSET ?"
        params.extend([self._pagination.get_limit(), self._pagination.get_offset()])

        rows = conn.execute(base_sql, params).fetchall()
        for row in rows:
            self._grid_rows.append(row)
            self.tree.insert("", "end", iid=str(row["id"]),
                             values=(row["member_id"], row["full_name"],
                                     row["phone"] or "", row["status"] or "",
                                     row["date_joined"] or ""),
                             tags=(row["status"] or "",))

        total = conn.execute(count_sql, count_params).fetchone()["cnt"]
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
        try:
            self._load_members_page(query)
        except Exception as e:
            try:
                self.status_var.set(f"Search failed: {e}")
            except Exception:
                pass

    def _open_member(self, db_id: int):
        self._show_detail(db_id)

    def _load_member_profile(self, db_id):
        conn = get_connection()
        row = conn.execute("SELECT * FROM members WHERE id = ?", (db_id,)).fetchone()
        if not row:
            messagebox.showerror("Error", "Member not found")
            return

        self.profile_name_label.config(text=row["full_name"])
        self.profile_id_label.config(text=f"Member ID: {row['member_id']}")
        self.profile_details["Phone"].config(text=row["phone"] or "--")
        self.profile_details["Address"].config(text=row["address"] or "--")
        self.profile_details["Status"].config(text=row["status"] or "--")
        self.profile_details["Date Joined"].config(text=row["date_joined"] or "--")
        self.profile_details["DOB"].config(text=row["dob"] if "dob" in row.keys() and row["dob"] else "--")
        self.profile_details["Gender"].config(text=row["gender"] if "gender" in row.keys() and row["gender"] else "--")
        self.profile_details["Occupation"].config(text=row["occupation"] if "occupation" in row.keys() and row["occupation"] else "--")
        self.profile_details["Email"].config(text=row["email"] if "email" in row.keys() and row["email"] else "--")
        self.profile_details["Next of Kin"].config(text=row["next_of_kin"] if "next_of_kin" in row.keys() and row["next_of_kin"] else "--")
        self.profile_details["NOK Phone"].config(text=row["next_of_kin_phone"] if "next_of_kin_phone" in row.keys() and row["next_of_kin_phone"] else "--")
        self.profile_details["ID Type"].config(text=row["id_type"] if "id_type" in row.keys() and row["id_type"] else "--")
        self.profile_details["ID Number"].config(text=row["id_number"] if "id_number" in row.keys() and row["id_number"] else "--")
        photo = row["photo_path"] if "photo_path" in row.keys() and row["photo_path"] else ""
        self.profile_details["Photo"].config(text=os.path.basename(photo) if photo else "--")
        self._show_profile_photo(photo)

        summary = get_member_financial_summary(db_id)
        self.finance_labels["total_paid"].config(text=format_currency(summary["total_paid"]))
        self.finance_labels["total_savings"].config(text=format_currency(summary["total_savings"]))
        self.finance_labels["total_shares"].config(text=format_currency(summary["total_shares"]))
        self.finance_labels["active_loan"].config(text=format_currency(summary["active_loan"]))
        self.finance_labels["loan_paid"].config(text=format_currency(summary["loan_paid"]))
        self.finance_labels["outstanding"].config(text=format_currency(summary["outstanding"]))
        self.finance_labels["minutes_owed"].config(text=format_currency(summary.get("minutes_owed", 0)))
        self.finance_labels["fines_owed"].config(text=format_currency(summary.get("fines_owed", 0)))
        self.finance_labels["other_owed"].config(text=format_currency(summary.get("other_owed", 0)))
        self.finance_labels["charges_paid"].config(text=format_currency(summary.get("charges_paid", 0)))

        self.btn_view_booklet.config(state="normal")
        self.btn_record_savings.config(state="normal")
        self.btn_record_repayment.config(state="normal")
        self.btn_record_payment.config(state="normal")
        self.btn_edit_details.config(state="normal")
        self.btn_print_card.config(state="normal")
        if row["status"] == "Exited":
            self.btn_mark_exited.config(state="disabled")
        else:
            self.btn_mark_exited.config(state="normal")
        self.quick_status_var.set(row["status"] or "Active")
        self.quick_status_combo.config(state="readonly")
        self.btn_apply_status.config(state="normal")
        self._load_passbook(db_id)

    def _apply_quick_status(self):
        if not self.selected_member_db_id:
            return
        from engines.transaction_engine import update_member_details
        new_status = self.quick_status_var.get().strip()
        if new_status not in ("Active", "Suspended", "Absconded"):
            messagebox.showwarning("Invalid Category", "Choose Active, Suspended or Absconded.")
            return

        def do_it():
            update_member_details(self.selected_member_db_id,
                                  entered_by=self.current_user.get("id"),
                                  status=new_status)
            return True

        ok = safe_execute(do_it, context="quick_status", show_dialog=True,
                          parent=self, default_return=None)
        if ok:
            conn = get_connection()
            saved = conn.execute("SELECT status FROM members WHERE id = ?",
                                 (self.selected_member_db_id,)).fetchone()
            if not saved or saved["status"] != new_status:
                messagebox.showerror(
                    "Not Saved",
                    "The category change did not save. Please try again.")
                return
            try:
                self.status_filter_var.set("All")
            except Exception:
                pass
            self._load_member_profile(self.selected_member_db_id)
            self._load_all_members()
            try:
                self.profile_details["Status"].config(fg="#2E7D32")
                self.after(2500, lambda: self.profile_details["Status"].config(
                    fg="#333333"))
            except Exception:
                pass
            messagebox.showinfo(
                "Updated",
                f"Member category set to {new_status}.\n"
                f"Profile, list and Categories now show {new_status}.")

    def _mark_as_exited(self):
        if not self.selected_member_db_id:
            return
        from datetime import date as _date
        conn = get_connection()
        row = conn.execute("SELECT * FROM members WHERE id = ?",
                           (self.selected_member_db_id,)).fetchone()
        if not row:
            messagebox.showerror("Error", "Member not found")
            return
        if row["status"] == "Exited":
            messagebox.showinfo("Already Exited", "This member has already been marked as exited.")
            return

        summary = get_member_financial_summary(self.selected_member_db_id)

        active_loans = conn.execute(
            "SELECT COUNT(*) as cnt FROM loans WHERE member_id = ? AND status IN ('Disbursed','Active','Overdue')",
            (self.selected_member_db_id,)
        ).fetchone()["cnt"]
        outstanding_loan = summary.get("outstanding", 0)

        unpaid_charges = conn.execute(
            "SELECT COALESCE(SUM(amount - amount_paid), 0) as total FROM member_charges WHERE member_id = ? AND amount > amount_paid",
            (self.selected_member_db_id,)
        ).fetchone()["total"]
        savings_balance = summary.get("total_savings", 0)

        has_blocks = (active_loans > 0 or outstanding_loan > 0 or
                      unpaid_charges > 0 or savings_balance > 0)

        win = tk.Toplevel(self)
        win.title(f"Mark as Exited - {row['full_name']}")
        win.geometry("500x620")
        win.configure(bg="#FFFFFF")
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Member Exit Confirmation", font=("Segoe UI", 14, "bold"),
                 fg="#C62828", bg="#FFFFFF").pack(anchor="w", padx=20, pady=(15, 5))
        tk.Label(win, text=f"Member: {row['full_name']} ({row['member_id']})",
                 font=("Segoe UI", 11), fg="#333333", bg="#FFFFFF").pack(anchor="w", padx=20)

        tk.Frame(win, height=2, bg="#E3F2FD").pack(fill="x", padx=20, pady=(12, 8))

        tk.Label(win, text="Financial Status:", font=("Segoe UI", 11, "bold"),
                 fg="#1565C0", bg="#FFFFFF").pack(anchor="w", padx=20)

        items_frame = tk.Frame(win, bg="#FFFFFF")
        items_frame.pack(fill="x", padx=20)

        def add_item(label, value, is_warning=False):
            row_f = tk.Frame(items_frame, bg="#FFFFFF")
            row_f.pack(fill="x", pady=1)
            color = "#C62828" if is_warning else "#333333"
            tk.Label(row_f, text=label, font=("Segoe UI", 10),
                     fg=color, bg="#FFFFFF").pack(side="left")
            tk.Label(row_f, text=format_currency(value), font=("Segoe UI", 10, "bold"),
                     fg=color, bg="#FFFFFF").pack(side="right")

        add_item("Savings Balance:", savings_balance, savings_balance > 0)
        add_item("Outstanding Loan:", outstanding_loan, outstanding_loan > 0)
        add_item("Unpaid Charges:", unpaid_charges, unpaid_charges > 0)

        tk.Frame(win, height=2, bg="#E3F2FD").pack(fill="x", padx=20, pady=(12, 8))

        if has_blocks:
            warn_lines = []
            if active_loans > 0 or outstanding_loan > 0:
                warn_lines.append(f"• {active_loans} active loan(s) with {format_currency(outstanding_loan)} outstanding")
            if unpaid_charges > 0:
                warn_lines.append(f"• Unpaid charges of {format_currency(unpaid_charges)}")
            if savings_balance > 0:
                warn_lines.append(f"• Savings balance of {format_currency(savings_balance)} (will be forfeited)")

            tk.Label(win, text="Outstanding Balances Detected:", font=("Segoe UI", 11, "bold"),
                     fg="#C62828", bg="#FFFFFF").pack(anchor="w", padx=20)
            for line in warn_lines:
                tk.Label(win, text=line, font=("Segoe UI", 10),
                         fg="#C62828", bg="#FFFFFF", wraplength=440, justify="left").pack(anchor="w", padx=30)

            tk.Label(win, text="\nPlease settle all outstanding amounts before\nmarking this member as exited.",
                     font=("Segoe UI", 10), fg="#333333", bg="#FFFFFF",
                     wraplength=440, justify="left").pack(anchor="w", padx=20)
        else:
            tk.Label(win, text="No outstanding balances. Member can be exited.",
                     font=("Segoe UI", 10, "bold"), fg="#2E7D32", bg="#FFFFFF").pack(anchor="w", padx=20)

        tk.Frame(win, height=2, bg="#E3F2FD").pack(fill="x", padx=20, pady=(12, 8))

        tk.Label(win, text="Exit Reason:", font=("Segoe UI", 11, "bold"),
                 fg="#1565C0", bg="#FFFFFF").pack(anchor="w", padx=20)
        reason_var = tk.StringVar()
        reason_combo = ttk.Combobox(win, textvariable=reason_var,
                                    values=["Voluntary withdrawal", "Relocation",
                                            "Non-payment", "Death", "Other"],
                                    state="readonly", font=("Segoe UI", 10), width=35)
        reason_combo.pack(padx=20, pady=(4, 0))

        tk.Label(win, text="Additional Notes (optional):", font=("Segoe UI", 10),
                 fg="#333333", bg="#FFFFFF").pack(anchor="w", padx=20, pady=(8, 2))
        notes_text = tk.Text(win, height=2, width=50, font=("Segoe UI", 10),
                             relief="solid", bd=1)
        notes_text.pack(padx=20)

        btn_frame = tk.Frame(win, bg="#FFFFFF")
        btn_frame.pack(fill="x", padx=20, pady=(12, 15))

        def confirm_exit():
            reason = reason_var.get().strip()
            if not reason:
                messagebox.showwarning("Required", "Please select an exit reason.", parent=win)
                return
            if has_blocks:
                if not messagebox.askyesno(
                    "Confirm Exit with Outstanding Balances",
                    "This member has outstanding balances.\n\n"
                    "By proceeding:\n"
                    "• Active loans will be written off\n"
                    "• Unpaid charges will be written off\n"
                    "• Savings balance will be forfeited\n\n"
                    "Are you sure you want to continue?",
                    parent=win
                ):
                    return
            else:
                if not messagebox.askyesno(
                    "Confirm Exit",
                    f"Mark {row['full_name']} as Exited?\n\n"
                    "This action records the member's departure from the cooperative.",
                    parent=win
                ):
                    return

            notes = notes_text.get("1.0", "end").strip()
            exit_reason = reason
            if notes:
                exit_reason = f"{reason} — {notes}"

            try:
                conn.execute(
                    "UPDATE members SET status = 'Exited', date_ended = ?, exit_reason = ? WHERE id = ?",
                    (_date.today().isoformat(), exit_reason, self.selected_member_db_id)
                )
                conn.commit()
            except Exception as exc:
                messagebox.showerror("Error", f"Failed to update member status:\n{exc}", parent=win)
                return

            messagebox.showinfo("Member Exited",
                                f"{row['full_name']} has been marked as Exited.\n"
                                f"Date: {_date.today().isoformat()}\n"
                                f"Reason: {exit_reason}",
                                parent=win)
            win.destroy()
            self._load_member_profile(self.selected_member_db_id)
            self._load_all_members()

        tk.Button(btn_frame, text="Confirm Exit", font=("Segoe UI", 11, "bold"),
                  bg="#C62828", fg="#FFFFFF", relief="flat", padx=16, pady=5,
                  command=confirm_exit).pack(side="left")
        tk.Button(btn_frame, text="Cancel", font=("Segoe UI", 11),
                  bg="#E3F2FD", fg="#1565C0", relief="flat", padx=16, pady=5,
                  command=win.destroy).pack(side="left", padx=(8, 0))

    def _open_register_dialog(self):
        win = tk.Toplevel(self)
        win.title("Register New Member")
        win.geometry("520x680")
        win.configure(bg="#FFFFFF")
        win.transient(self)
        win.grab_set()

        canvas = tk.Canvas(win, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        body = tk.Frame(canvas, bg="#FFFFFF", padx=20, pady=15)
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        tk.Label(body, text="Register New Member (KYC)", font=("Segoe UI", 14, "bold"),
                 fg="#1565C0", bg="#FFFFFF").pack(anchor="w", pady=(0, 12))

        reg_name = tk.StringVar()
        reg_phone = tk.StringVar()
        reg_address = tk.StringVar()
        reg_fee = tk.StringVar(value=get_setting("entrance_fee", "5000"))
        reg_date = tk.StringVar(value=date.today().isoformat())
        reg_dob = tk.StringVar()
        reg_gender = tk.StringVar()
        reg_occupation = tk.StringVar()
        reg_email = tk.StringVar()
        reg_nok = tk.StringVar()
        reg_nok_phone = tk.StringVar()
        reg_id_type = tk.StringVar()
        reg_id_number = tk.StringVar()
        photo_src = {"path": None}
        reg_photo = tk.StringVar(value="No photo selected")

        grid = tk.Frame(body, bg="#FFFFFF")
        grid.pack(fill="x")
        text_fields = [
            ("Full Name *", reg_name), ("Phone", reg_phone), ("Address", reg_address),
            ("Date of Birth (YYYY-MM-DD)", reg_dob), ("Occupation", reg_occupation),
            ("Email", reg_email), ("Next of Kin", reg_nok),
            ("Next of Kin Phone", reg_nok_phone), ("ID Number", reg_id_number),
            ("Entrance Fee", reg_fee), ("Date Joined", reg_date),
        ]
        for i, (label, var) in enumerate(text_fields):
            tk.Label(grid, text=label, font=("Segoe UI", 10), fg="#333333",
                     bg="#FFFFFF").grid(row=i, column=0, sticky="w", pady=(4, 1))
            tk.Entry(grid, textvariable=var, font=("Segoe UI", 10), width=30,
                     relief="solid", bd=1).grid(row=i, column=1, sticky="w",
                                                 pady=(4, 1), padx=(8, 0))
        from utils.date_picker import pick_date as _pick
        tk.Button(grid, text="Cal", font=("Segoe UI", 9), bg="#E3F2FD", fg="#1565C0",
                  relief="flat", cursor="hand2", padx=4,
                  command=lambda: _pick(win, reg_dob, "Select Date of Birth")).grid(
                      row=3, column=2, sticky="w", padx=(4, 0))
        tk.Button(grid, text="Cal", font=("Segoe UI", 9), bg="#E3F2FD", fg="#1565C0",
                  relief="flat", cursor="hand2", padx=4,
                  command=lambda: _pick(win, reg_date, "Select Date Joined")).grid(
                      row=10, column=2, sticky="w", padx=(4, 0))

        r = len(text_fields)
        tk.Label(grid, text="Gender", font=("Segoe UI", 10), fg="#333333",
                 bg="#FFFFFF").grid(row=r, column=0, sticky="w", pady=(4, 1))
        ttk.Combobox(grid, textvariable=reg_gender, values=["", "Male", "Female"],
                     state="readonly", width=28).grid(row=r, column=1, sticky="w",
                                                       pady=(4, 1), padx=(8, 0))
        tk.Label(grid, text="ID Type", font=("Segoe UI", 10), fg="#333333",
                 bg="#FFFFFF").grid(row=r + 1, column=0, sticky="w", pady=(4, 1))
        ttk.Combobox(grid, textvariable=reg_id_type,
                     values=["", "NIN", "Voter's Card", "Driver's License", "Passport", "Other"],
                     state="readonly", width=28).grid(row=r + 1, column=1, sticky="w",
                                                       pady=(4, 1), padx=(8, 0))

        tk.Label(grid, text="Photograph", font=("Segoe UI", 10), fg="#333333",
                 bg="#FFFFFF").grid(row=r + 2, column=0, sticky="w", pady=(4, 1))
        photo_row = tk.Frame(grid, bg="#FFFFFF")
        photo_row.grid(row=r + 2, column=1, sticky="w", pady=(4, 1), padx=(8, 0))
        tk.Button(photo_row, text="Upload Photo", font=("Segoe UI", 9),
                  bg="#E3F2FD", fg="#1565C0", relief="flat", padx=8, pady=3,
                  command=lambda: self._select_dialog_photo(win, photo_src, reg_photo)).pack(side="left")
        tk.Label(photo_row, textvariable=reg_photo, font=("Segoe UI", 9),
                 fg="#666666", bg="#FFFFFF").pack(side="left", padx=(6, 0))

        btn_row = tk.Frame(body, bg="#FFFFFF")
        btn_row.pack(fill="x", pady=(14, 0))

        def submit():
            name = reg_name.get().strip()
            phone = reg_phone.get().strip()
            address = reg_address.get().strip()
            fee_str = reg_fee.get().strip()
            date_joined = reg_date.get().strip()
            dob = reg_dob.get().strip()
            gender = reg_gender.get().strip()
            occupation = reg_occupation.get().strip()
            email = reg_email.get().strip()
            nok = reg_nok.get().strip()
            nok_phone = reg_nok_phone.get().strip()
            id_type = reg_id_type.get().strip()
            id_number = reg_id_number.get().strip()

            def validate_and_register():
                validate_name(name, "Full Name")
                fee = validate_amount(fee_str) if fee_str else 0.0
                result = register_member(
                    full_name=name, phone=phone, address=address,
                    entrance_fee=fee, date_joined=date_joined,
                    entered_by=self.current_user.get("id"),
                    dob=dob, gender=gender, occupation=occupation, email=email,
                    next_of_kin=nok, next_of_kin_phone=nok_phone,
                    id_type=id_type, id_number=id_number,
                )
                if photo_src["path"] and os.path.exists(photo_src["path"]):
                    photos_dir = DB_DIR / "photos"
                    photos_dir.mkdir(parents=True, exist_ok=True)
                    ext = os.path.splitext(photo_src["path"])[1] or ".jpg"
                    dest = photos_dir / f"{result['member_id']}{ext}"
                    shutil.copy2(photo_src["path"], dest)
                    conn = get_connection()
                    conn.execute("UPDATE members SET photo_path = ? WHERE id = ?",
                                 (str(dest), result["id"]))
                    conn.commit()
                return result

            def on_success(result):
                messagebox.showinfo("Success",
                                    f"Member registered.\nID: {result['member_id']}\nName: {result['full_name']}",
                                    parent=win)
                win.destroy()
                self._load_all_members()

            result = safe_execute(validate_and_register, context="register_member",
                                  show_dialog=True, parent=win, default_return=None)
            if result:
                on_success(result)

        tk.Button(btn_row, text="Register", font=("Segoe UI", 11, "bold"),
                  bg="#1565C0", fg="#FFFFFF", activebackground="#0D47A1",
                  relief="flat", padx=16, pady=5, command=submit).pack(side="left")
        tk.Button(btn_row, text="Cancel", font=("Segoe UI", 11),
                  bg="#E3F2FD", fg="#1565C0", relief="flat", padx=16, pady=5,
                  command=win.destroy).pack(side="left", padx=(8, 0))

    def _select_dialog_photo(self, win, photo_src, photo_var):
        path = filedialog.askopenfilename(
            parent=win,
            title="Select Member Photograph",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.gif *.bmp"), ("All files", "*.*")],
        )
        if path:
            photo_src["path"] = path
            photo_var.set(os.path.basename(path))

    def _open_categories_dialog(self):
        win = tk.Toplevel(self)
        win.title("Members by Category")
        win.geometry("700x500")
        win.configure(bg="#FFFFFF")
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Members by Category", font=("Segoe UI", 14, "bold"),
                 fg="#1565C0", bg="#FFFFFF").pack(anchor="w", padx=15, pady=(12, 8))

        cat_trees = {}
        cols_frame = tk.Frame(win, bg="#FFFFFF", padx=15)
        cols_frame.pack(fill="both", expand=True)

        for i, status in enumerate(("Active", "Suspended", "Absconded", "Exited")):
            panel = tk.LabelFrame(cols_frame, text=f"  {status}  ",
                                  font=("Segoe UI", 11, "bold"),
                                  fg="#1565C0", bg="#FFFFFF", padx=6, pady=6)
            panel.grid(row=0, column=i, sticky="nsew", padx=4)
            cols_frame.columnconfigure(i, weight=1)
            tree = ttk.Treeview(panel, columns=("mid", "name"), show="headings", height=18)
            tree.heading("mid", text="Member ID")
            tree.heading("name", text="Name")
            tree.column("mid", width=90, anchor="center")
            tree.column("name", width=160)
            tree.pack(fill="both", expand=True)

            def on_double_click(event, t=tree):
                sel = t.selection()
                if sel:
                    win.destroy()
                    self._show_detail(int(sel[0]))

            tree.bind("<Double-1>", on_double_click)
            cat_trees[status] = tree

        conn = get_connection()
        for status, tree in cat_trees.items():
            for row in conn.execute(
                    "SELECT id, member_id, full_name FROM members WHERE status = ? ORDER BY full_name",
                    (status,)).fetchall():
                tree.insert("", "end", iid=str(row["id"]),
                            values=(row["member_id"], row["full_name"]))

    def _show_profile_photo(self, photo_path: str = "") -> None:
        try:
            if photo_path and os.path.exists(photo_path):
                from PIL import Image, ImageTk
                img = Image.open(photo_path).convert("RGB")
                img.thumbnail((200, 220))
                self._photo_img = ImageTk.PhotoImage(img)
                self.profile_photo_label.config(image=self._photo_img, text="")
                return
        except Exception:
            pass
        self._photo_img = None
        self.profile_photo_label.config(image="", text="No photo")

    def _edit_details(self):
        if not self.selected_member_db_id:
            return
        from engines.transaction_engine import update_member_details
        from constants import MEMBER_STATUSES
        conn = get_connection()
        row = conn.execute("SELECT * FROM members WHERE id = ?",
                           (self.selected_member_db_id,)).fetchone()
        if not row:
            messagebox.showerror("Error", "Member not found")
            return

        win = tk.Toplevel(self)
        win.title(f"Edit Details - {row['full_name']}")
        win.geometry("480x640")
        win.configure(bg="#FFFFFF")
        win.transient(self)
        win.grab_set()

        canvas = tk.Canvas(win, bg="#FFFFFF", highlightthickness=0)
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=canvas.yview)
        body = tk.Frame(canvas, bg="#FFFFFF", padx=20, pady=15)
        body.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=body, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def col(name, default=""):
            try:
                return row[name] or default
            except Exception:
                return default

        vars_map = {
            "full_name": tk.StringVar(value=col("full_name")),
            "phone": tk.StringVar(value=col("phone")),
            "address": tk.StringVar(value=col("address")),
            "dob": tk.StringVar(value=col("dob")),
            "gender": tk.StringVar(value=col("gender")),
            "occupation": tk.StringVar(value=col("occupation")),
            "email": tk.StringVar(value=col("email")),
            "next_of_kin": tk.StringVar(value=col("next_of_kin")),
            "next_of_kin_phone": tk.StringVar(value=col("next_of_kin_phone")),
            "id_type": tk.StringVar(value=col("id_type")),
            "id_number": tk.StringVar(value=col("id_number")),
            "status": tk.StringVar(value=col("status", "Active")),
            "notes": tk.StringVar(value=col("notes")),
        }
        text_rows = [
            ("Full Name *", "full_name"), ("Phone", "phone"),
            ("Address", "address"), ("Date of Birth", "dob"),
            ("Occupation", "occupation"), ("Email", "email"),
            ("Next of Kin", "next_of_kin"), ("NOK Phone", "next_of_kin_phone"),
            ("ID Number", "id_number"), ("Notes", "notes"),
        ]
        for i, (label, key) in enumerate(text_rows):
            tk.Label(body, text=label, font=("Segoe UI", 10),
                     bg="#FFFFFF", fg="#333333", anchor="w").grid(
                         row=i, column=0, sticky="w", pady=(4, 1))
            tk.Entry(body, textvariable=vars_map[key], font=("Segoe UI", 10),
                     width=28, relief="solid", bd=1).grid(
                         row=i, column=1, sticky="w", pady=(4, 1), padx=(8, 0))
        from utils.date_picker import pick_date as _pick3
        tk.Button(body, text="Cal", font=("Segoe UI", 9), bg="#E3F2FD", fg="#1565C0",
                  relief="flat", cursor="hand2", padx=4,
                  command=lambda: _pick3(win, vars_map["dob"],
                                         "Select Date of Birth")).grid(
                                             row=3, column=2, sticky="w", padx=(4, 0))

        r = len(text_rows)
        tk.Label(body, text="Gender", font=("Segoe UI", 10),
                 bg="#FFFFFF", fg="#333333", anchor="w").grid(
                     row=r, column=0, sticky="w", pady=(4, 1))
        ttk.Combobox(body, textvariable=vars_map["gender"],
                     values=["", "Male", "Female"], state="readonly",
                     width=26).grid(row=r, column=1, sticky="w", pady=(4, 1), padx=(8, 0))
        tk.Label(body, text="ID Type", font=("Segoe UI", 10),
                 bg="#FFFFFF", fg="#333333", anchor="w").grid(
                     row=r + 1, column=0, sticky="w", pady=(4, 1))
        ttk.Combobox(body, textvariable=vars_map["id_type"],
                     values=["", "NIN", "Voter's Card", "Driver's License", "Passport", "Other"],
                     state="readonly", width=26).grid(
                         row=r + 1, column=1, sticky="w", pady=(4, 1), padx=(8, 0))
        tk.Label(body, text="Category", font=("Segoe UI", 10, "bold"),
                 bg="#FFFFFF", fg="#1565C0", anchor="w").grid(
                     row=r + 2, column=0, sticky="w", pady=(4, 1))
        ttk.Combobox(body, textvariable=vars_map["status"],
                     values=list(MEMBER_STATUSES), state="readonly",
                     width=26).grid(row=r + 2, column=1, sticky="w", pady=(4, 1), padx=(8, 0))

        new_photo = {"src": None}
        photo_lbl = tk.StringVar(value="Keep existing photo")

        def change_photo():
            path = filedialog.askopenfilename(
                parent=win,
                title="Select New Photograph",
                filetypes=[("Images", "*.jpg *.jpeg *.png *.gif *.bmp"),
                           ("All files", "*.*")],
            )
            if path:
                new_photo["src"] = path
                photo_lbl.set(os.path.basename(path))

        tk.Label(body, text="Photograph", font=("Segoe UI", 10),
                 bg="#FFFFFF", fg="#333333", anchor="w").grid(
                     row=r + 3, column=0, sticky="w", pady=(4, 1))
        prow = tk.Frame(body, bg="#FFFFFF")
        prow.grid(row=r + 3, column=1, sticky="w", pady=(4, 1), padx=(8, 0))
        tk.Button(prow, text="Change Photo", font=("Segoe UI", 9),
                  bg="#E3F2FD", fg="#1565C0", relief="flat", padx=8, pady=3,
                  command=change_photo).pack(side="left")
        tk.Label(prow, textvariable=photo_lbl, font=("Segoe UI", 9),
                 fg="#666666", bg="#FFFFFF").pack(side="left", padx=(6, 0))

        def save():
            def do_save():
                data = {k: v.get().strip() for k, v in vars_map.items()}
                validate_name(data["full_name"], "Full Name")
                if new_photo["src"] and os.path.exists(new_photo["src"]):
                    photos_dir = DB_DIR / "photos"
                    photos_dir.mkdir(parents=True, exist_ok=True)
                    ext = os.path.splitext(new_photo["src"])[1] or ".jpg"
                    dest = photos_dir / f"{row['member_id']}{ext}"
                    shutil.copy2(new_photo["src"], dest)
                    data["photo_path"] = str(dest)
                update_member_details(
                    self.selected_member_db_id,
                    entered_by=self.current_user.get("id"), **data)
                return True

            ok = safe_execute(do_save, context="edit_member",
                              show_dialog=True, parent=win, default_return=None)
            if ok:
                messagebox.showinfo("Saved", "Member details updated.", parent=win)
                win.destroy()
                self._load_member_profile(self.selected_member_db_id)
                self._load_all_members()

        tk.Button(body, text="Save Changes", font=("Segoe UI", 11, "bold"),
                  bg="#2E7D32", fg="#FFFFFF", relief="flat", padx=16, pady=5,
                  command=save).grid(row=r + 4, column=0, columnspan=2, pady=(14, 0))

    def _print_card(self):
        if not self.selected_member_db_id:
            return
        import html as _html
        import webbrowser
        conn = get_connection()
        row = conn.execute("SELECT * FROM members WHERE id = ?",
                           (self.selected_member_db_id,)).fetchone()
        if not row:
            messagebox.showerror("Error", "Member not found")
            return
        try:
            from engines.transaction_engine import get_member_charges
            charges = get_member_charges(self.selected_member_db_id)
        except Exception:
            charges = []
        summary = get_member_financial_summary(self.selected_member_db_id)

        def val(key):
            try:
                return row[key] or "--"
            except Exception:
                return "--"

        photo_src = ""
        if row["photo_path"] if "photo_path" in row.keys() else "":
            p = row["photo_path"]
            if p and os.path.exists(p):
                photo_src = "file:///" + p.replace("\\", "/")

        fin_rows = [
            ("Total Savings", summary["total_savings"]),
            ("Total Shares Value", summary["total_shares"]),
            ("Active Loan", summary["active_loan"]),
            ("Loan Repaid", summary["loan_paid"]),
            ("Loan Outstanding", summary["outstanding"]),
            ("Minutes Owed", summary.get("minutes_owed", 0)),
            ("Fines Owed", summary.get("fines_owed", 0)),
            ("Other Charges Owed", summary.get("other_owed", 0)),
            ("Charges Paid", summary.get("charges_paid", 0)),
            ("Total Paid (All Time)", summary["total_paid"]),
        ]
        fin_html = "".join(
            f"<tr><td>{_html.escape(k)}</td><td>{format_currency(v)}</td></tr>"
            for k, v in fin_rows)
        ch_html = "".join(
            f"<tr><td>{_html.escape(c['charge_type'])}</td>"
            f"<td>{_html.escape(c['description'] or '')}</td>"
            f"<td>{format_currency(c['amount'])}</td>"
            f"<td>{format_currency(c['amount_paid'])}</td>"
            f"<td>{_html.escape(c['status'])}</td></tr>"
            for c in charges) or "<tr><td colspan='5'>No charges</td></tr>"

        kyc = [("Member ID", val("member_id")), ("Full Name", val("full_name")),
               ("Phone", val("phone")), ("Address", val("address")),
               ("Date of Birth", val("dob")), ("Gender", val("gender")),
               ("Occupation", val("occupation")), ("Email", val("email")),
               ("Next of Kin", val("next_of_kin")),
               ("NOK Phone", val("next_of_kin_phone")),
               ("ID Type", val("id_type")), ("ID Number", val("id_number")),
               ("Category", val("status")), ("Date Joined", val("date_joined"))]
        kyc_html = "".join(
            f"<tr><td><b>{_html.escape(k)}</b></td><td>{_html.escape(str(v))}</td></tr>"
            for k, v in kyc)

        page = f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Member Card - {_html.escape(str(val('full_name')))}</title>
<style>body{{font-family:Segoe UI,Arial;margin:30px;color:#222}}
h1{{color:#1565C0}}h2{{color:#1565C0;border-bottom:2px solid #1565C0}}
.card{{display:flex;gap:25px;align-items:flex-start}}
.card img{{width:160px;border:2px solid #1565C0}}
table{{border-collapse:collapse;width:100%;margin:10px 0}}
td,th{{border:1px solid #bbb;padding:6px 10px;text-align:left}}
@media print{{.noprint{{display:none}}}}</style></head><body>
<h1>ORISUN IBUKUN - Member Card</h1>
<div class="card"><div>{"<img src='" + photo_src + "'>" if photo_src else "<div>No photo</div>"}</div>
<div><table>{kyc_html}</table></div></div>
<h2>Financial Summary</h2><table>{fin_html}</table>
<h2>Charges (Fines / Minutes Levies / Other)</h2>
<table><tr><th>Type</th><th>Description</th><th>Billed</th><th>Paid</th><th>Status</th></tr>{ch_html}</table>
<p class="noprint"><button onclick="window.print()">Print</button></p>
</body></html>"""
        out = DB_DIR / f"member_card_{row['member_id']}.html"
        out.write_text(page, encoding="utf-8")
        webbrowser.open("file:///" + str(out).replace("\\", "/"))
        messagebox.showinfo("Member Card",
                            "Member card opened in your browser.\nUse Ctrl+P to print it.")

    def _view_booklet(self):
        if not self.selected_member_db_id:
            return
        from ui.savings_form import SavingsForm
        for w in self.winfo_toplevel().main_area.winfo_children():
            w.destroy()
        sf = SavingsForm(self.winfo_toplevel().main_area, self.current_user)
        if not sf.load_member(self.selected_member_db_id):
            messagebox.showerror("Error", "Could not load this member's passbook.")

    def _record_payment(self):
        if not self.selected_member_db_id:
            return
        from engines.transaction_engine import (
            record_charge_payment, record_other_payment,
        )
        win = tk.Toplevel(self)
        win.title("Record Payment")
        win.geometry("400x420")
        win.configure(bg="#FFFFFF")
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Category:", font=("Segoe UI", 12, "bold"),
                 fg="#1565C0", bg="#FFFFFF").pack(anchor="w", padx=20, pady=(15, 5))
        cat_var = tk.StringVar(value="Minutes")
        ttk.Combobox(win, textvariable=cat_var,
                     values=["Minutes", "Other"],
                     state="readonly", font=("Segoe UI", 11), width=30).pack(padx=20)

        tk.Label(win, text="Amount:", font=("Segoe UI", 12), bg="#FFFFFF").pack(
            anchor="w", padx=20, pady=(10, 5))
        amount_var = tk.StringVar()
        tk.Entry(win, textvariable=amount_var, font=("Segoe UI", 12), width=30,
                 relief="solid", bd=1).pack(padx=20)

        tk.Label(win, text="Tag / Description (for Other):", font=("Segoe UI", 12),
                 bg="#FFFFFF").pack(anchor="w", padx=20, pady=(10, 5))
        tag_var = tk.StringVar()
        tk.Entry(win, textvariable=tag_var, font=("Segoe UI", 12), width=30,
                 relief="solid", bd=1).pack(padx=20)

        tk.Label(win, text="Payment Method:", font=("Segoe UI", 12),
                 bg="#FFFFFF").pack(anchor="w", padx=20, pady=(10, 5))
        method_var = tk.StringVar(value="Cash")
        ttk.Combobox(win, textvariable=method_var,
                     values=["Cash", "Bank Transfer", "Mobile"],
                     state="readonly", font=("Segoe UI", 11), width=30).pack(padx=20)

        def submit():
            def validate_and_record():
                amount = validate_amount(amount_var.get())
                if amount <= 0:
                    raise ValidationError("Amount must be greater than zero.")
                category = cat_var.get()
                method = method_var.get()
                uid = self.current_user.get("id")
                if category == "Minutes":
                    return record_charge_payment(
                        self.selected_member_db_id, amount, "Minutes",
                        payment_method=method, entered_by=uid)
                else:
                    return record_other_payment(
                        self.selected_member_db_id, amount,
                        tag=tag_var.get().strip(),
                        payment_method=method, entered_by=uid)

            def on_success(txn_id):
                messagebox.showinfo("Success",
                                    f"Payment recorded.\nTransaction: {txn_id}",
                                    parent=win)
                self._load_member_profile(self.selected_member_db_id)
                win.destroy()

            result = safe_execute(
                validate_and_record, context="record_payment",
                show_dialog=True, parent=win, default_return=None)
            if result:
                on_success(result)

        tk.Button(win, text="Record Payment", font=("Segoe UI", 12, "bold"), bg="#E65100",
                  fg="#FFFFFF", relief="flat", padx=15, pady=5, command=submit).pack(pady=18)

    def _record_savings(self):
        if not self.selected_member_db_id:
            return
        win = tk.Toplevel(self)
        win.title("Record Savings")
        win.geometry("350x200")
        win.configure(bg="#FFFFFF")
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Amount:", font=("Segoe UI", 12), bg="#FFFFFF").pack(pady=(20, 5))
        amount_var = tk.StringVar()
        tk.Entry(win, textvariable=amount_var, font=("Segoe UI", 12), width=25,
                 relief="solid", bd=1).pack()

        def submit():
            def validate_and_record():
                amount = validate_amount(amount_var.get())
                txn_id = record_savings(
                    self.selected_member_db_id, amount,
                    entered_by=self.current_user.get("id"),
                )
                return (amount, txn_id)

            def on_success(result):
                amount, txn_id = result
                messagebox.showinfo("Success", f"Savings recorded.\nTransaction: {txn_id}", parent=win)
                self._load_member_profile(self.selected_member_db_id)
                win.destroy()

            result = safe_execute(
                validate_and_record, context="record_savings",
                show_dialog=True, parent=win, default_return=None)
            if result:
                on_success(result)

        tk.Button(win, text="Save", font=("Segoe UI", 12, "bold"), bg="#1565C0",
                  fg="#FFFFFF", relief="flat", padx=15, pady=5, command=submit).pack(pady=15)

    def _record_repayment(self):
        if not self.selected_member_db_id:
            return
        conn = get_connection()
        loans = conn.execute(
            "SELECT id, loan_id, outstanding_principal FROM loans WHERE member_id = ? AND status IN ('Disbursed', 'Active', 'Overdue')",
            (self.selected_member_db_id,),
        ).fetchall()

        if not loans:
            messagebox.showinfo("No Loans", "This member has no active loans.")
            return

        win = tk.Toplevel(self)
        win.title("Record Loan Repayment")
        win.geometry("400x280")
        win.configure(bg="#FFFFFF")
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Select Loan:", font=("Segoe UI", 12, "bold"),
                 fg="#1565C0", bg="#FFFFFF").pack(anchor="w", padx=20, pady=(15, 5))
        loan_var = tk.StringVar()
        loan_options = [f"{l['loan_id']} - Outstanding: {format_currency(l['outstanding_principal'])}" for l in loans]
        loan_combo = ttk.Combobox(win, textvariable=loan_var, values=loan_options,
                                  state="readonly", font=("Segoe UI", 10), width=45)
        loan_combo.pack(padx=20)
        if loan_options:
            loan_combo.current(0)

        tk.Label(win, text="Amount:", font=("Segoe UI", 12), bg="#FFFFFF").pack(
            anchor="w", padx=20, pady=(10, 5))
        amount_var = tk.StringVar()
        tk.Entry(win, textvariable=amount_var, font=("Segoe UI", 12), width=30,
                 relief="solid", bd=1).pack(padx=20)

        def submit():
            if not loan_var.get():
                messagebox.showwarning("Validation", "Select a loan.", parent=win)
                return

            def validate_and_record():
                amount = validate_amount(amount_var.get())
                idx = loan_combo.current()
                loan_db_id = loans[idx]["id"]
                txn_id = record_repayment(
                    loan_db_id, amount, self.selected_member_db_id,
                    entered_by=self.current_user.get("id"),
                )
                return (amount, txn_id)

            def on_success(result):
                amount, txn_id = result
                messagebox.showinfo("Success", f"Repayment recorded.\nTransaction: {txn_id}", parent=win)
                self._load_member_profile(self.selected_member_db_id)
                win.destroy()

            result = safe_execute(
                validate_and_record, context="record_repayment",
                show_dialog=True, parent=win, default_return=None)
            if result:
                on_success(result)

        tk.Button(win, text="Record Repayment", font=("Segoe UI", 12, "bold"), bg="#1565C0",
                  fg="#FFFFFF", relief="flat", padx=15, pady=5, command=submit).pack(pady=15)
