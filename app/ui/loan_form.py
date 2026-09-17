import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import datetime
import os
import shutil
from database.connection import get_connection
from database.schema import get_setting
from engines.transaction_engine import (
    create_loan, approve_loan, disburse_loan, record_repayment,
    add_guarantor, add_external_guarantor, get_loan_guarantors,
    add_loan_document, list_loan_documents,
    get_member_loans, get_all_loan_members,
    get_member_financial_summary, reverse_transaction,
    get_loan_repayments,
)
from utils.validators import validate_amount
from utils.helpers import format_currency, PaginationHelper
from utils.date_picker import pick_date
from errors import handle_error, safe_execute, ValidationError
from constants import (
    LOAN_STATUS_APPLIED, LOAN_STATUS_APPROVED, LOAN_STATUS_DISBURSED,
    LOAN_STATUS_ACTIVE, LOAN_STATUS_OVERDUE, LOAN_STATUS_COMPLETED,
    REPAY_MONTHLY, REPAY_WEEKLY,
)
from permissions import has_permission, PERM_REVERSE_TXN, PERM_LOANS_MANAGE


BLUE = "#1565C0"
WHITE = "#FFFFFF"
LIGHT_BLUE = "#E3F2FD"
DARK_BLUE = "#0D47A1"
GREY = "#F5F5F5"
GREEN = "#2E7D32"
LIGHT_GREEN = "#E8F5E9"
ORANGE = "#E65100"


class LoanForm(tk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, bg=WHITE)
        self.current_user = current_user
        self.selected_member_db_id = None
        self._search_query = ""
        self._search_after_id = None
        self._pagination = PaginationHelper(page_size=50)
        self._loan_search_query = ""
        self._loan_search_after_id = None

        self.pack(fill="both", expand=True)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)

        self.tab_register = tk.Frame(self.notebook, bg=WHITE)
        self.tab_new = tk.Frame(self.notebook, bg=WHITE)
        self.notebook.add(self.tab_register, text="  Loan Register  ")
        self.notebook.add(self.tab_new, text="  New Loan  ")

        self._build_register_tab()
        self._build_new_loan_tab()

    # ── REGISTER TAB ──────────────────────────────────────────────

    def _build_register_tab(self):
        self.register_list_frame = tk.Frame(self.tab_register, bg=WHITE)
        self.register_detail_frame = tk.Frame(self.tab_register, bg=WHITE)

        self._build_register_list()
        self._build_register_detail()

        self.register_list_frame.pack(fill="both", expand=True)

    def _show_register_list(self):
        self.register_detail_frame.pack_forget()
        self.register_list_frame.pack(fill="both", expand=True)
        self._load_register_page(self._search_query)

    def _show_register_detail(self, member_db_id):
        self.selected_member_db_id = member_db_id
        self.register_list_frame.pack_forget()
        self.register_detail_frame.pack(fill="both", expand=True)
        self._load_member_loan_detail(member_db_id)

    # ── REGISTER LIST ─────────────────────────────────────────────

    def _build_register_list(self):
        top_bar = tk.Frame(self.register_list_frame, bg=WHITE)
        top_bar.pack(fill="x", padx=15, pady=(12, 8))

        tk.Label(top_bar, text="LOANS", font=("Segoe UI", 16, "bold"),
                 fg=BLUE, bg=WHITE).pack(side="left")

        filter_frame = tk.Frame(top_bar, bg=WHITE)
        filter_frame.pack(side="right")

        tk.Label(filter_frame, text="Status:", font=("Segoe UI", 10),
                 fg="#666666", bg=WHITE).pack(side="left", padx=(0, 4))
        self._status_filter = ttk.Combobox(filter_frame, width=14, state="readonly",
                                           values=["All", "Applied", "Approved",
                                                   "Disbursed", "Active", "Overdue",
                                                   "Completed"])
        self._status_filter.set("All")
        self._status_filter.pack(side="left")
        self._status_filter.bind("<<ComboboxSelected>>",
                                 lambda e: self._load_register_page(self._search_query))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *a: self._schedule_filter())
        tk.Entry(filter_frame, textvariable=self.search_var, font=("Segoe UI", 11),
                 width=25, relief="solid", bd=1).pack(side="left", padx=(10, 0))
        tk.Button(filter_frame, text="Search", font=("Segoe UI", 10, "bold"),
                  bg=BLUE, fg=WHITE, relief="flat", padx=8, pady=3,
                  command=self._filter_register).pack(side="left", padx=(6, 0))

        self.status_var = tk.StringVar(value="")
        tk.Label(self.register_list_frame, textvariable=self.status_var,
                 font=("Segoe UI", 9), fg="#666666", bg=WHITE, anchor="w"
                 ).pack(fill="x", padx=15)

        pag_frame = tk.Frame(self.register_list_frame, bg=WHITE, padx=15)
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

        cols_frame = tk.Frame(self.register_list_frame, bg=WHITE, padx=15)
        cols_frame.pack(fill="both", expand=True)

        cols = ("db_id", "member_id", "full_name", "loan_count",
                "total_principal", "total_outstanding", "latest_status")
        self.reg_tree = ttk.Treeview(cols_frame, columns=cols, show="headings", height=22)
        self.reg_tree.heading("db_id", text="DB ID")
        self.reg_tree.heading("member_id", text="Member ID")
        self.reg_tree.heading("full_name", text="Full Name")
        self.reg_tree.heading("loan_count", text="# Loans")
        self.reg_tree.heading("total_principal", text="Total Principal")
        self.reg_tree.heading("total_outstanding", text="Outstanding")
        self.reg_tree.heading("latest_status", text="Status")
        self.reg_tree.column("db_id", width=0, stretch=False)
        self.reg_tree.column("member_id", width=100, anchor="center")
        self.reg_tree.column("full_name", width=200)
        self.reg_tree.column("loan_count", width=70, anchor="center")
        self.reg_tree.column("total_principal", width=130, anchor="e")
        self.reg_tree.column("total_outstanding", width=130, anchor="e")
        self.reg_tree.column("latest_status", width=100, anchor="center")

        tree_scroll = ttk.Scrollbar(cols_frame, orient="vertical", command=self.reg_tree.yview)
        self.reg_tree.configure(yscrollcommand=tree_scroll.set)
        self.reg_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.reg_tree.bind("<Double-1>", lambda e: self._on_register_select())

        self._load_all_members()

    def _on_register_select(self):
        sel = self.reg_tree.selection()
        if not sel:
            return
        values = self.reg_tree.item(sel[0], "values")
        db_id = int(values[0])
        self._show_register_detail(db_id)

    def _load_all_members(self):
        self._pagination = PaginationHelper(page_size=50)
        self._load_register_page()

    def _load_register_page(self, query: str = ""):
        for item in self.reg_tree.get_children():
            self.reg_tree.delete(item)

        status = self._status_filter.get() if hasattr(self, "_status_filter") else "All"
        rows = get_all_loan_members(status_filter=status)

        if query:
            query_lower = query.lower()
            rows = [r for r in rows if
                    query_lower in (r["full_name"] or "").lower() or
                    query_lower in (r["member_id"] or "").lower() or
                    query_lower in (r["phone"] or "").lower()]

        total = len(rows)
        start = self._pagination.get_offset()
        end = start + self._pagination.get_limit()
        page_rows = rows[start:end]

        for row in page_rows:
            outstanding = row["total_outstanding"] or 0
            status_val = row["latest_status"] or ""
            self.reg_tree.insert("", "end", iid=str(row["db_id"]),
                                 values=(row["db_id"], row["member_id"],
                                         row["full_name"], row["loan_count"],
                                         format_currency(row["total_principal"]),
                                         format_currency(outstanding),
                                         status_val))

        self._pagination.set_total_items(total)
        info = self._pagination.get_page_info()
        self.status_var.set(
            f"Showing {info['start_item']}-{info['end_item']} of {info['total_items']} members")
        self.page_info_var.set(f"Page {info['current_page']} of {info['total_pages']}")
        self.prev_btn.config(state="normal" if info["has_prev"] else "disabled")
        self.next_btn.config(state="normal" if info["has_next"] else "disabled")

    def _prev_page(self):
        if self._pagination.prev_page():
            self._load_register_page(self._search_query)

    def _next_page(self):
        if self._pagination.next_page():
            self._load_register_page(self._search_query)

    def _schedule_filter(self):
        if self._search_after_id:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(300, self._filter_register)

    def _filter_register(self):
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
        self._load_register_page(query)

    # ── REGISTER DETAIL ───────────────────────────────────────────

    def _build_register_detail(self):
        _canvas = tk.Canvas(self.register_detail_frame, bg=WHITE, highlightthickness=0)
        _scroll = ttk.Scrollbar(self.register_detail_frame, orient="vertical", command=_canvas.yview)
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

        # Navbar
        navbar = tk.Frame(c, bg=WHITE)
        navbar.pack(fill="x", pady=(0, 8))
        tk.Button(navbar, text="< Back to Loans", font=("Segoe UI", 10, "bold"),
                  bg=LIGHT_BLUE, fg=BLUE, relief="flat", padx=10, pady=4,
                  command=self._show_register_list).pack(side="left")
        self.detail_title = tk.Label(navbar, text="", font=("Segoe UI", 12, "bold"),
                                     fg=BLUE, bg=WHITE)
        self.detail_title.pack(side="left", padx=(15, 0))

        # Member info
        self.member_info_frame = tk.Frame(c, bg=LIGHT_BLUE, padx=12, pady=8)
        self.member_info_frame.pack(fill="x", pady=(0, 8))
        self.member_info_labels = {}
        for key, label in [("phone", "Phone"), ("member_id", "Member ID")]:
            row = tk.Frame(self.member_info_frame, bg=LIGHT_BLUE)
            row.pack(side="left", padx=(0, 15))
            tk.Label(row, text=f"{label}:", font=("Segoe UI", 9, "bold"),
                     fg=BLUE, bg=LIGHT_BLUE).pack(side="left")
            val = tk.Label(row, text="--", font=("Segoe UI", 9),
                           fg="#333333", bg=LIGHT_BLUE)
            val.pack(side="left", padx=(4, 0))
            self.member_info_labels[key] = val

        # Loans list for this member
        tk.Label(c, text="Loans", font=("Segoe UI", 13, "bold"),
                 fg=BLUE, bg=WHITE).pack(anchor="w", pady=(8, 4))

        loan_cols = ("loan_id", "principal", "repaid", "outstanding", "status", "applied")
        self.loan_tree = ttk.Treeview(c, columns=loan_cols, show="headings", height=5)
        for col, txt, w in [("loan_id", "Loan ID", 120), ("principal", "Principal", 120),
                            ("repaid", "Repaid", 120), ("outstanding", "Outstanding", 120),
                            ("status", "Status", 90), ("applied", "Applied", 90)]:
            self.loan_tree.heading(col, text=txt)
            self.loan_tree.column(col, width=w,
                                  anchor="center" if col in ("status", "applied") else "e")
        self.loan_tree.pack(fill="x")
        self.loan_tree.bind("<Double-1>", lambda e: self._on_loan_select())

        # Loan detail section (for selected loan)
        self.loan_detail_frame = tk.Frame(c, bg=WHITE)
        self.loan_detail_frame.pack(fill="x", pady=(8, 0))

        tk.Label(self.loan_detail_frame, text="Loan Detail", font=("Segoe UI", 13, "bold"),
                 fg=BLUE, bg=WHITE).pack(anchor="w", pady=(0, 4))

        self.loan_detail_text = tk.Text(self.loan_detail_frame, font=("Consolas", 10),
                                        bg="#FAFAFA", height=6, relief="solid", bd=1)
        self.loan_detail_text.pack(fill="x")
        self.loan_detail_text.config(state="disabled")

        # Action buttons
        btn_frame = tk.Frame(c, bg=WHITE)
        btn_frame.pack(fill="x", pady=(8, 0))
        role = self.current_user.get("role", "")
        if has_permission(role, PERM_LOANS_MANAGE):
            self.btn_approve = tk.Button(btn_frame, text="Approve", font=("Segoe UI", 10, "bold"),
                                         bg=GREEN, fg=WHITE, relief="flat", padx=10, pady=4,
                                         command=self._approve_loan)
            self.btn_approve.pack(side="left", padx=(0, 6))
            self.btn_disburse = tk.Button(btn_frame, text="Disburse", font=("Segoe UI", 10, "bold"),
                                          bg=ORANGE, fg=WHITE, relief="flat", padx=10, pady=4,
                                          command=self._disburse_loan)
            self.btn_disburse.pack(side="left", padx=(0, 6))
        tk.Button(btn_frame, text="Record Repayment", font=("Segoe UI", 10, "bold"),
                  bg=BLUE, fg=WHITE, relief="flat", padx=10, pady=4,
                  command=self._record_repayment_dialog).pack(side="left", padx=(0, 6))
        if has_permission(role, PERM_LOANS_MANAGE):
            tk.Button(btn_frame, text="Add Guarantor", font=("Segoe UI", 10),
                      bg=LIGHT_BLUE, fg=BLUE, relief="flat", padx=8, pady=3,
                      command=self._add_guarantor_dialog).pack(side="left", padx=(0, 6))
            tk.Button(btn_frame, text="Upload Document", font=("Segoe UI", 10),
                      bg=LIGHT_BLUE, fg=BLUE, relief="flat", padx=8, pady=3,
                      command=self._upload_document_dialog).pack(side="left")
        if has_permission(role, PERM_REVERSE_TXN):
            tk.Button(btn_frame, text="Reverse", font=("Segoe UI", 10, "bold"),
                      bg="#D32F2F", fg=WHITE, relief="flat", padx=8, pady=3,
                      command=self._reverse_loan_txn_dialog).pack(side="left", padx=(6, 0))

        # Guarantors
        tk.Label(c, text="Guarantors", font=("Segoe UI", 13, "bold"),
                 fg=BLUE, bg=WHITE).pack(anchor="w", pady=(12, 4))
        guar_frame = tk.Frame(c, bg=WHITE)
        guar_frame.pack(fill="x")
        self.guar_tree = ttk.Treeview(guar_frame, columns=("name", "amount", "status"),
                                      show="headings", height=3)
        self.guar_tree.heading("name", text="Name")
        self.guar_tree.heading("amount", text="Guarantee Amount")
        self.guar_tree.heading("status", text="Status")
        self.guar_tree.column("name", width=200)
        self.guar_tree.column("amount", width=150, anchor="e")
        self.guar_tree.column("status", width=100, anchor="center")
        self.guar_tree.pack(fill="x")

        # Documents
        tk.Label(c, text="Documents", font=("Segoe UI", 13, "bold"),
                 fg=BLUE, bg=WHITE).pack(anchor="w", pady=(12, 4))
        doc_frame = tk.Frame(c, bg=WHITE)
        doc_frame.pack(fill="x")
        self.doc_tree = ttk.Treeview(doc_frame, columns=("name", "uploaded"),
                                     show="headings", height=3)
        self.doc_tree.heading("name", text="Document Name")
        self.doc_tree.heading("uploaded", text="Uploaded")
        self.doc_tree.column("name", width=300)
        self.doc_tree.column("uploaded", width=150, anchor="center")
        self.doc_tree.pack(fill="x")

        self._selected_loan_db_id = None

    def _on_loan_select(self):
        sel = self.loan_tree.selection()
        if not sel:
            return
        loan_db_id = int(sel[0])
        self._selected_loan_db_id = loan_db_id
        self._open_loan_popup(loan_db_id)

    def _open_loan_popup(self, loan_db_id):
        conn = get_connection()
        loan = conn.execute(
            """SELECT l.*, m.full_name, m.member_id, m.phone
               FROM loans l JOIN members m ON l.member_id = m.id
               WHERE l.id = ?""", (loan_db_id,)).fetchone()
        if not loan:
            return

        win = tk.Toplevel(self)
        win.title(f"Loan {loan['loan_id']} — {loan['full_name']}")
        win.geometry("720x560")
        win.configure(bg=WHITE)
        win.transient(self.winfo_toplevel())
        win.grab_set()

        notebook = ttk.Notebook(win)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # ── Details Tab ──
        tab_detail = tk.Frame(notebook, bg=WHITE)
        notebook.add(tab_detail, text="  Details  ")

        repaid = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM loan_repayments WHERE loan_id = ?",
            (loan_db_id,)).fetchone()["total"]

        detail_text = tk.Text(tab_detail, font=("Consolas", 11), bg="#FAFAFA",
                              relief="solid", bd=1, wrap="word")
        detail_text.pack(fill="both", expand=True, padx=8, pady=8)
        lines = [
            f"Loan ID: {loan['loan_id']}       Status: {loan['status']}",
            f"Principal: {format_currency(loan['principal_amount'])}       "
            f"Interest: {loan['interest_rate']}% ({format_currency(loan['interest_amount'])})",
            f"Processing Fee: {format_currency(loan['processing_fee'])}       "
            f"Other Charges: {format_currency(loan['other_charges'])}",
            f"Total Repayable: {format_currency(loan['total_repayable'])}",
            f"Repaid: {format_currency(repaid)}       "
            f"Outstanding: {format_currency(loan['outstanding_principal'] + loan['outstanding_interest'])}",
            f"Frequency: {loan['repayment_frequency']}       "
            f"Applied: {loan['application_date'] or '--'}       "
            f"Disbursed: {loan['disbursement_date'] or '--'}",
        ]
        detail_text.insert(tk.END, "\n".join(lines))
        detail_text.config(state="disabled")

        # ── Guarantors Tab ──
        tab_guar = tk.Frame(notebook, bg=WHITE)
        notebook.add(tab_guar, text="  Guarantors  ")

        guar_cols = ("name", "amount", "status")
        guar_tree = ttk.Treeview(tab_guar, columns=guar_cols, show="headings", height=12)
        guar_tree.heading("name", text="Name")
        guar_tree.heading("amount", text="Guarantee Amount")
        guar_tree.heading("status", text="Status")
        guar_tree.column("name", width=280)
        guar_tree.column("amount", width=180, anchor="e")
        guar_tree.column("status", width=120, anchor="center")
        guar_tree.pack(fill="both", expand=True, padx=8, pady=8)

        guar_data = get_loan_guarantors(loan_db_id)
        for g in guar_data["members"]:
            guar_tree.insert("", "end",
                             values=(f"{g['full_name']} (Member)",
                                     format_currency(g["guarantee_amount"]),
                                     g["status"]))
        for g in guar_data["external"]:
            guar_tree.insert("", "end",
                             values=(f"{g['full_name']} ({g['relationship']})",
                                     format_currency(g["guarantee_amount"]),
                                     g["status"]))

        # View Photo button
        photo_btn_frame = tk.Frame(tab_guar, bg=WHITE)
        photo_btn_frame.pack(fill="x", padx=8, pady=(4, 0))

        def _view_guarantor_photo():
            sel = guar_tree.selection()
            if not sel:
                messagebox.showinfo("No Selection", "Select a guarantor first.", parent=win)
                return
            vals = guar_tree.item(sel[0], "values")
            name = vals[0]
            photo_path = None
            for g in guar_data["members"]:
                if g["full_name"] in name and g.get("photo_path"):
                    photo_path = g["photo_path"]
                    break
            if not photo_path:
                for g in guar_data["external"]:
                    if g["full_name"] in name and g.get("photo_path"):
                        photo_path = g["photo_path"]
                        break
            if not photo_path or not os.path.exists(photo_path):
                messagebox.showinfo("No Photo", f"No photo available for {name}.", parent=win)
                return
            try:
                from PIL import Image, ImageTk
                pwin = tk.Toplevel(win)
                pwin.title(f"Photo - {name}")
                pwin.configure(bg=WHITE)
                img = Image.open(photo_path).convert("RGB")
                img.thumbnail((400, 440))
                photo = ImageTk.PhotoImage(img)
                lbl = tk.Label(pwin, image=photo, bg=WHITE)
                lbl.image = photo
                lbl.pack(padx=10, pady=10)
            except Exception as ex:
                messagebox.showerror("Error", str(ex), parent=win)

        tk.Button(photo_btn_frame, text="View Photo", font=("Segoe UI", 9),
                  bg=LIGHT_BLUE, fg=BLUE, relief="flat",
                  command=_view_guarantor_photo).pack(side="left")

        # ── Documents Tab ──
        tab_docs = tk.Frame(notebook, bg=WHITE)
        notebook.add(tab_docs, text="  Documents  ")

        doc_cols = ("name", "uploaded")
        doc_tree = ttk.Treeview(tab_docs, columns=doc_cols, show="headings", height=12)
        doc_tree.heading("name", text="Document Name")
        doc_tree.heading("uploaded", text="Uploaded")
        doc_tree.column("name", width=400)
        doc_tree.column("uploaded", width=180, anchor="center")
        doc_tree.pack(fill="both", expand=True, padx=8, pady=8)

        docs = list_loan_documents(loan_db_id)
        for d in docs:
            doc_tree.insert("", "end", values=(d["doc_name"], d["uploaded_at"]))

        # ── Repayments Tab ──
        tab_repay = tk.Frame(notebook, bg=WHITE)
        notebook.add(tab_repay, text="  Repayments  ")

        repay_cols = ("date", "amount", "principal", "interest", "balance", "method")
        repay_tree = ttk.Treeview(tab_repay, columns=repay_cols, show="headings", height=12)
        repay_tree.heading("date", text="Date")
        repay_tree.heading("amount", text="Amount Paid")
        repay_tree.heading("principal", text="Principal Portion")
        repay_tree.heading("interest", text="Interest Portion")
        repay_tree.heading("balance", text="Balance After")
        repay_tree.heading("method", text="Method")
        repay_tree.column("date", width=100, anchor="center")
        repay_tree.column("amount", width=110, anchor="e")
        repay_tree.column("principal", width=120, anchor="e")
        repay_tree.column("interest", width=110, anchor="e")
        repay_tree.column("balance", width=110, anchor="e")
        repay_tree.column("method", width=90, anchor="center")
        repay_tree.pack(fill="both", expand=True, padx=8, pady=8)

        repayments = get_loan_repayments(loan_db_id)
        for rp in repayments:
            repay_tree.insert("", "end", values=(
                rp.get("payment_date") or rp.get("txn_date") or "--",
                format_currency(rp.get("amount", 0)),
                format_currency(rp.get("principal_portion", 0)),
                format_currency(rp.get("interest_portion", 0)),
                format_currency(rp.get("balance_after", 0)),
                rp.get("payment_method") or "Cash",
            ))

    def _load_member_loan_detail(self, db_id):
        conn = get_connection()
        row = conn.execute("SELECT id, member_id, full_name, phone FROM members WHERE id = ?",
                           (db_id,)).fetchone()
        if not row:
            return

        self.detail_title.config(text=f"{row['full_name']}  ({row['member_id']})")
        self.member_info_labels["phone"].config(text=row["phone"] or "--")
        self.member_info_labels["member_id"].config(text=row["member_id"])

        # Load all loans for this member
        for item in self.loan_tree.get_children():
            self.loan_tree.delete(item)

        loans = get_member_loans(db_id)
        for loan in loans:
            repaid = loan.get("total_repaid", 0) or 0
            outstanding = (loan["outstanding_principal"] or 0) + (loan["outstanding_interest"] or 0)
            self.loan_tree.insert("", "end", iid=str(loan["id"]),
                                  values=(loan["loan_id"],
                                          format_currency(loan["principal_amount"]),
                                          format_currency(repaid),
                                          format_currency(outstanding),
                                          loan["status"],
                                          loan["application_date"] or "--"))

        # Select first loan if any
        self._selected_loan_db_id = None
        self.loan_detail_text.config(state="normal")
        self.loan_detail_text.delete("1.0", tk.END)
        self.loan_detail_text.config(state="disabled")
        self.guar_tree.delete(*self.guar_tree.get_children())
        self.doc_tree.delete(*self.doc_tree.get_children())

        if loans:
            first_iid = self.loan_tree.get_children()[0]
            self.loan_tree.selection_set(first_iid)
            self._on_loan_select()

    def _load_single_loan_detail(self, loan_db_id):
        conn = get_connection()
        loan = conn.execute(
            """SELECT l.*, m.full_name, m.member_id, m.phone
               FROM loans l JOIN members m ON l.member_id = m.id
               WHERE l.id = ?""", (loan_db_id,)).fetchone()
        if not loan:
            return

        repaid = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM loan_repayments WHERE loan_id = ?",
            (loan_db_id,)).fetchone()["total"]

        self.loan_detail_text.config(state="normal")
        self.loan_detail_text.delete("1.0", tk.END)
        lines = [
            f"Loan ID: {loan['loan_id']}       Status: {loan['status']}",
            f"Principal: {format_currency(loan['principal_amount'])}       "
            f"Interest: {loan['interest_rate']}% ({format_currency(loan['interest_amount'])})",
            f"Processing Fee: {format_currency(loan['processing_fee'])}       "
            f"Other Charges: {format_currency(loan['other_charges'])}",
            f"Total Repayable: {format_currency(loan['total_repayable'])}       "
            f"Repaid: {format_currency(repaid)}       "
            f"Outstanding: {format_currency(loan['outstanding_principal'] + loan['outstanding_interest'])}",
            f"Frequency: {loan['repayment_frequency']}       "
            f"Applied: {loan['application_date'] or '--'}       "
            f"Disbursed: {loan['disbursement_date'] or '--'}",
        ]
        self.loan_detail_text.insert(tk.END, "\n".join(lines))
        self.loan_detail_text.config(state="disabled")

        # Update action buttons based on status
        status = loan["status"]
        self.btn_approve.config(state="normal" if status == LOAN_STATUS_APPLIED else "disabled")
        self.btn_disburse.config(state="normal" if status == LOAN_STATUS_APPROVED else "disabled")

        # Load guarantors
        self.guar_tree.delete(*self.guar_tree.get_children())
        guar_data = get_loan_guarantors(loan_db_id)
        for g in guar_data["members"]:
            self.guar_tree.insert("", "end",
                                  values=(f"{g['full_name']} (Member)",
                                          format_currency(g["guarantee_amount"]),
                                          g["status"]))
        for g in guar_data["external"]:
            self.guar_tree.insert("", "end",
                                  values=(f"{g['full_name']} ({g['relationship']})",
                                          format_currency(g["guarantee_amount"]),
                                          g["status"]))

        # Load documents
        self.doc_tree.delete(*self.doc_tree.get_children())
        docs = list_loan_documents(loan_db_id)
        for d in docs:
            self.doc_tree.insert("", "end",
                                 values=(d["doc_name"], d["uploaded_at"]))

    def _approve_loan(self):
        if not self._selected_loan_db_id:
            messagebox.showwarning("No Loan", "Select a loan first.")
            return
        approve_loan(self._selected_loan_db_id, approved_by=self.current_user.get("id"))
        messagebox.showinfo("Approved", "Loan approved.")
        self._load_single_loan_detail(self._selected_loan_db_id)
        self._refresh_loan_tree()

    def _disburse_loan(self):
        if not self._selected_loan_db_id:
            messagebox.showwarning("No Loan", "Select a loan first.")
            return
        conn = get_connection()
        loan = conn.execute("SELECT * FROM loans WHERE id = ?",
                            (self._selected_loan_db_id,)).fetchone()
        if not loan:
            return
        if loan["status"] != LOAN_STATUS_APPROVED:
            messagebox.showwarning("Status", f"Loan must be Approved.\nCurrent: {loan['status']}")
            return
        disburse_loan(self._selected_loan_db_id, loan["member_id"],
                      entered_by=self.current_user.get("id"),
                      date=loan["application_date"], allow_backdate=True)
        messagebox.showinfo("Disbursed", "Loan disbursed.")
        self._load_single_loan_detail(self._selected_loan_db_id)
        self._refresh_loan_tree()

    def _refresh_loan_tree(self):
        if not self.selected_member_db_id:
            return
        for item in self.loan_tree.get_children():
            self.loan_tree.delete(item)
        loans = get_member_loans(self.selected_member_db_id)
        for loan in loans:
            repaid = loan.get("total_repaid", 0) or 0
            outstanding = (loan["outstanding_principal"] or 0) + (loan["outstanding_interest"] or 0)
            self.loan_tree.insert("", "end", iid=str(loan["id"]),
                                  values=(loan["loan_id"],
                                          format_currency(loan["principal_amount"]),
                                          format_currency(repaid),
                                          format_currency(outstanding),
                                          loan["status"],
                                          loan["application_date"] or "--"))

    def _record_repayment_dialog(self):
        if not self._selected_loan_db_id:
            messagebox.showwarning("No Loan", "Select a loan first.")
            return
        win = tk.Toplevel(self.register_detail_frame)
        win.title("Record Repayment")
        win.geometry("350x200")
        win.configure(bg=WHITE)
        win.transient(self.register_detail_frame)
        win.grab_set()

        tk.Label(win, text="Repayment Amount:", font=("Segoe UI", 11),
                 bg=WHITE).pack(padx=15, pady=(15, 5), anchor="w")
        amt_var = tk.StringVar()
        tk.Entry(win, textvariable=amt_var, font=("Segoe UI", 11),
                 width=20, relief="solid", bd=1).pack(padx=15, anchor="w")

        tk.Label(win, text="Date (YYYY-MM-DD):", font=("Segoe UI", 11),
                 bg=WHITE).pack(padx=15, pady=(10, 5), anchor="w")
        date_var = tk.StringVar(value=datetime.date.today().isoformat())
        date_entry = tk.Entry(win, textvariable=date_var, font=("Segoe UI", 11),
                              width=20, relief="solid", bd=1)
        date_entry.pack(padx=15, anchor="w")
        tk.Button(win, text="Calendar", font=("Segoe UI", 9),
                  bg=LIGHT_BLUE, fg=BLUE, relief="flat",
                  command=lambda: pick_date(win, date_var)).pack(padx=15, anchor="w", pady=(2, 0))

        def submit():
            try:
                amt = float(amt_var.get().strip().replace(",", "").replace("₦", ""))
                if amt <= 0:
                    raise ValueError("Amount must be positive.")
            except ValueError as e:
                messagebox.showerror("Error", str(e))
                return

            date_str = date_var.get().strip()
            conn = get_connection()
            loan = conn.execute("SELECT member_id FROM loans WHERE id = ?",
                                (self._selected_loan_db_id,)).fetchone()
            if not loan:
                return
            try:
                record_repayment(self._selected_loan_db_id, amt, loan["member_id"],
                                 entered_by=self.current_user.get("id"),
                                 date=date_str, allow_backdate=True)
                messagebox.showinfo("Recorded", f"Repayment of {format_currency(amt)} recorded.")
                win.destroy()
                self._load_single_loan_detail(self._selected_loan_db_id)
                self._refresh_loan_tree()
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        tk.Button(win, text="Record Payment", font=("Segoe UI", 11, "bold"),
                  bg=GREEN, fg=WHITE, relief="flat", padx=12, pady=4,
                  command=submit).pack(pady=15)

    def _add_guarantor_dialog(self):
        if not self._selected_loan_db_id:
            messagebox.showwarning("No Loan", "Select a loan first.")
            return
        win = tk.Toplevel(self.register_detail_frame)
        win.title("Add Guarantor")
        win.geometry("700x600")
        win.minsize(600, 500)
        win.configure(bg=WHITE)
        win.transient(self.register_detail_frame)
        win.grab_set()

        # Canvas + scrollbar for scrollable fields
        canvas = tk.Canvas(win, bg=WHITE, highlightthickness=0)
        vsb = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=WHITE)
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Bind mouse-wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        mode_var = tk.StringVar(value="member")
        mode_frame = tk.Frame(scroll_frame, bg=WHITE)
        mode_frame.pack(fill="x", padx=15, pady=(10, 0))
        tk.Radiobutton(mode_frame, text="Member", variable=mode_var, value="member",
                       bg=WHITE, font=("Segoe UI", 10),
                       command=lambda: _toggle_mode("member")).pack(side="left")
        tk.Radiobutton(mode_frame, text="Non-Member", variable=mode_var, value="external",
                       bg=WHITE, font=("Segoe UI", 10),
                       command=lambda: _toggle_mode("external")).pack(side="left", padx=(12, 0))

        member_frame = tk.Frame(scroll_frame, bg=WHITE)
        external_frame = tk.Frame(scroll_frame, bg=WHITE)

        tk.Label(member_frame, text="Search Member (name or ID):", font=("Segoe UI", 11),
                 bg=WHITE).pack(padx=15, pady=(10, 5), anchor="w")
        search_var = tk.StringVar()
        tk.Entry(member_frame, textvariable=search_var, font=("Segoe UI", 11),
                 width=30, relief="solid", bd=1).pack(padx=15, anchor="w")
        result_label = tk.Label(member_frame, text="", font=("Segoe UI", 10),
                                fg="#666666", bg=WHITE)
        result_label.pack(padx=15, anchor="w", pady=(5, 0))
        found_member = [None]

        def search_member():
            q = search_var.get().strip()
            if not q:
                return
            conn = get_connection()
            row = conn.execute(
                """SELECT id, member_id, full_name FROM members
                   WHERE member_id = ? OR full_name LIKE ? LIMIT 1""",
                (q, f"%{q}%")).fetchone()
            if row:
                found_member[0] = row["id"]
                result_label.config(text=f"Found: {row['full_name']} ({row['member_id']})")
            else:
                found_member[0] = None
                result_label.config(text="Member not found.")

        tk.Button(member_frame, text="Search", font=("Segoe UI", 9, "bold"),
                  bg=BLUE, fg=WHITE, relief="flat", padx=6, pady=2,
                  command=search_member).pack(padx=15, anchor="w", pady=(5, 0))

        ext_name_var = tk.StringVar()
        ext_phone_var = tk.StringVar()
        ext_addr_var = tk.StringVar()
        ext_id_type_var = tk.StringVar()
        ext_id_num_var = tk.StringVar()
        ext_rel_var = tk.StringVar()

        ext_fields = [
            ("Full Name *:", ext_name_var), ("Phone:", ext_phone_var),
            ("Address:", ext_addr_var), ("ID Type:", ext_id_type_var),
            ("ID Number:", ext_id_num_var), ("Relationship *:", ext_rel_var),
        ]
        for label, var in ext_fields:
            tk.Label(external_frame, text=label, font=("Segoe UI", 10),
                     bg=WHITE).pack(padx=15, pady=(4, 0), anchor="w")
            tk.Entry(external_frame, textvariable=var, font=("Segoe UI", 10),
                     width=30, relief="solid", bd=1).pack(padx=15, anchor="w")

        ext_photo_var = tk.StringVar(value="")

        def pick_photo():
            path = filedialog.askopenfilename(
                title="Select Passport Photo",
                filetypes=[("Images", "*.jpg;*.jpeg;*.png")])
            if path:
                ext_photo_var.set(path)

        photo_row = tk.Frame(external_frame, bg=WHITE)
        photo_row.pack(fill="x", padx=15, pady=(4, 0))
        tk.Label(photo_row, text="Passport Photo:", font=("Segoe UI", 10),
                 bg=WHITE).pack(side="left")
        tk.Button(photo_row, text="Browse", font=("Segoe UI", 9),
                  bg=LIGHT_BLUE, fg=BLUE, relief="flat",
                  command=pick_photo).pack(side="left", padx=(6, 0))

        tk.Label(scroll_frame, text="Guarantee Amount:", font=("Segoe UI", 11),
                 bg=WHITE).pack(padx=15, pady=(10, 5), anchor="w")
        amt_var = tk.StringVar()
        tk.Entry(scroll_frame, textvariable=amt_var, font=("Segoe UI", 11),
                 width=20, relief="solid", bd=1).pack(padx=15, anchor="w")

        def _toggle_mode(mode):
            member_frame.pack_forget()
            external_frame.pack_forget()
            if mode == "member":
                member_frame.pack(fill="x", after=mode_frame)
            else:
                external_frame.pack(fill="x", after=mode_frame)

        def submit():
            # Unbind mouse-wheel on close
            canvas.unbind_all("<MouseWheel>")
            try:
                amt = float(amt_var.get().strip().replace(",", "").replace("₦", ""))
            except ValueError:
                messagebox.showerror("Error", "Enter a valid amount.")
                return
            if mode_var.get() == "member":
                if not found_member[0]:
                    messagebox.showerror("Error", "Search and select a member first.")
                    return
                add_guarantor(self._selected_loan_db_id, found_member[0], amt)
            else:
                name = ext_name_var.get().strip()
                rel = ext_rel_var.get().strip()
                if not name or not rel:
                    messagebox.showerror("Error", "Full Name and Relationship are required.")
                    return
                photo_path = ext_photo_var.get()
                if photo_path:
                    import shutil as _shutil
                    from database.connection import DB_DIR
                    docs_dir = DB_DIR / "documents"
                    docs_dir.mkdir(parents=True, exist_ok=True)
                    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    ext = os.path.splitext(photo_path)[1] or ".jpg"
                    dest = docs_dir / f"guarantor_{stamp}{ext}"
                    _shutil.copy2(photo_path, dest)
                    photo_path = str(dest)
                add_external_guarantor(
                    self._selected_loan_db_id,
                    full_name=name, phone=ext_phone_var.get().strip(),
                    address=ext_addr_var.get().strip(),
                    id_type=ext_id_type_var.get().strip(),
                    id_number=ext_id_num_var.get().strip(),
                    photo_path=photo_path, relationship=rel,
                    guarantee_amount=amt)
            messagebox.showinfo("Added", "Guarantor added.")
            win.destroy()
            self._load_single_loan_detail(self._selected_loan_db_id)

        tk.Button(scroll_frame, text="Add Guarantor", font=("Segoe UI", 11, "bold"),
                  bg=GREEN, fg=WHITE, relief="flat", padx=12, pady=4,
                  command=submit).pack(pady=12)

        _toggle_mode("member")

    def _upload_document_dialog(self):
        if not self._selected_loan_db_id:
            messagebox.showwarning("No Loan", "Select a loan first.")
            return
        path = filedialog.askopenfilename(
            title="Select Document",
            filetypes=[("All Files", "*.*"), ("PDF", "*.pdf"), ("Images", "*.jpg;*.png")])
        if not path:
            return
        doc_name = os.path.basename(path)
        conn = get_connection()
        loan = conn.execute("SELECT member_id FROM loans WHERE id = ?",
                            (self._selected_loan_db_id,)).fetchone()
        if not loan:
            return
        try:
            add_loan_document(self._selected_loan_db_id, loan["member_id"],
                              doc_name, path, uploaded_by=self.current_user.get("id"))
            messagebox.showinfo("Uploaded", f"Document '{doc_name}' uploaded.")
            self._load_single_loan_detail(self._selected_loan_db_id)
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def _reverse_loan_txn_dialog(self):
        if not self._selected_loan_db_id:
            messagebox.showwarning("No Loan", "Select a loan first.")
            return
        conn = get_connection()
        loan = conn.execute("SELECT member_id FROM loans WHERE id = ?",
                            (self._selected_loan_db_id,)).fetchone()
        if not loan:
            return
        member_id = loan["member_id"]
        win = tk.Toplevel(self.register_detail_frame)
        win.title("Reverse Loan Transaction")
        win.geometry("700x550")
        win.minsize(700, 500)
        win.configure(bg=WHITE)
        win.transient(self.register_detail_frame)
        win.grab_set()

        tk.Label(win, text="Select a Posted transaction to reverse:",
                 font=("Segoe UI", 11, "bold"), fg=BLUE, bg=WHITE
                 ).pack(padx=15, pady=(12, 5), anchor="w")

        # Action bar packed BOTTOM first so it never gets clipped
        reason_var = tk.StringVar()
        action_frame = tk.Frame(win, bg=WHITE)
        action_frame.pack(side="bottom", fill="x", padx=15, pady=(6, 10))

        reason_frame = tk.Frame(action_frame, bg=WHITE)
        reason_frame.pack(fill="x")
        tk.Label(reason_frame, text="Reason:", font=("Segoe UI", 10),
                 bg=WHITE).pack(side="left")
        tk.Entry(reason_frame, textvariable=reason_var, font=("Segoe UI", 10),
                 width=40, relief="solid", bd=1).pack(side="left", padx=(6, 0))

        def do_reverse():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Select", "Pick a transaction first.")
                return
            txn_id = sel[0]
            reason = reason_var.get().strip()
            if not reason:
                messagebox.showwarning("Reason", "Enter a reason for reversal.")
                return
            try:
                reverse_transaction(txn_id, reason,
                                    self.current_user.get("id"))
                messagebox.showinfo("Reversed", "Transaction reversed successfully.")
                win.destroy()
                self._load_single_loan_detail(self._selected_loan_db_id)
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        tk.Button(action_frame, text="Reverse Selected", font=("Segoe UI", 11, "bold"),
                  bg="#D32F2F", fg=WHITE, relief="flat", padx=12, pady=4,
                  command=do_reverse).pack(pady=(6, 0))

        # Tree fills remaining space above the action bar
        cols = ("txn_id", "date", "type", "amount", "description")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=12)
        tree.heading("txn_id", text="Txn ID")
        tree.heading("date", text="Date")
        tree.heading("type", text="Type")
        tree.heading("amount", text="Amount")
        tree.heading("description", text="Description")
        tree.column("txn_id", width=90)
        tree.column("date", width=80)
        tree.column("type", width=110)
        tree.column("amount", width=90, anchor="e")
        tree.column("description", width=200)
        vsb = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", padx=15, fill="both", expand=True)
        vsb.pack(side="right", fill="y", padx=(0, 15))

        txns = conn.execute(
            """SELECT transaction_id, date, transaction_type, amount, description
               FROM transactions
               WHERE member_id = ? AND status = 'Posted'
               ORDER BY date DESC, id DESC LIMIT 50""",
            (member_id,),
        ).fetchall()
        for t in txns:
            tree.insert("", "end", iid=t["transaction_id"],
                        values=(t["transaction_id"], t["date"],
                                t["transaction_type"],
                                format_currency(t["amount"] or 0),
                                (t["description"] or "")[:50]))

        # Center over parent and ensure visibility
        win.update_idletasks()
        pw = self.register_detail_frame.winfo_width()
        ph = self.register_detail_frame.winfo_height()
        px = self.register_detail_frame.winfo_rootx()
        py = self.register_detail_frame.winfo_rooty()
        wx = px + max(0, (pw - 700) // 2)
        wy = py + max(0, (ph - 550) // 2)
        win.geometry(f"700x550+{wx}+{wy}")
        win.lift()
        win.focus_force()

    # ── NEW LOAN TAB ──────────────────────────────────────────────

    def _build_new_loan_tab(self):
        canvas = tk.Canvas(self.tab_new, bg=WHITE, highlightthickness=0)
        scroll = ttk.Scrollbar(self.tab_new, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        container = tk.Frame(canvas, bg=WHITE, padx=20, pady=15)
        win = canvas.create_window((0, 0), window=container, anchor="nw")
        container.bind("<Configure>",
                       lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                       if canvas.bbox("all") else None)
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(win, width=e.width))
        canvas.bind("<Enter>", lambda e: canvas.bind_all(
            "<MouseWheel>", lambda ev: canvas.yview_scroll(
                int(-1 * (ev.delta / 120)), "units")))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        tk.Label(container, text="NEW LOAN APPLICATION", font=("Segoe UI", 16, "bold"),
                 fg=BLUE, bg=WHITE).pack(anchor="w", pady=(0, 12))

        # Member search
        member_frame = tk.LabelFrame(container, text="Member Details",
                                     font=("Segoe UI", 11, "bold"), fg=BLUE,
                                     bg=WHITE, padx=10, pady=8)
        member_frame.pack(fill="x", pady=(0, 10))

        row = tk.Frame(member_frame, bg=WHITE)
        row.pack(fill="x", pady=2)
        tk.Label(row, text="Search Member:", font=("Segoe UI", 10),
                 bg=WHITE, width=15, anchor="w").pack(side="left")
        self._nl_member_search = tk.StringVar()
        tk.Entry(row, textvariable=self._nl_member_search, font=("Segoe UI", 10),
                 width=30, relief="solid", bd=1).pack(side="left", padx=(0, 6))
        tk.Button(row, text="Search", font=("Segoe UI", 9, "bold"),
                  bg=BLUE, fg=WHITE, relief="flat", padx=6, pady=2,
                  command=self._nl_search_member).pack(side="left")
        self._nl_member_label = tk.Label(row, text="", font=("Segoe UI", 10, "bold"),
                                         fg=GREEN, bg=WHITE)
        self._nl_member_label.pack(side="left", padx=(10, 0))
        self._nl_member_db_id = None

        # Loan details
        loan_frame = tk.LabelFrame(container, text="Loan Details",
                                   font=("Segoe UI", 11, "bold"), fg=BLUE,
                                   bg=WHITE, padx=10, pady=8)
        loan_frame.pack(fill="x", pady=(0, 10))

        self._nl_entries = {}
        for label_text, key, default in [
            ("Principal Amount:", "principal", ""),
            ("Interest Rate (%):", "interest", str(get_setting("interest_rate") or "5")),
            ("Processing Fee:", "processing_fee", ""),
            ("Other Charges:", "other_charges", ""),
        ]:
            row = tk.Frame(loan_frame, bg=WHITE)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label_text, font=("Segoe UI", 10),
                     bg=WHITE, width=18, anchor="w").pack(side="left")
            entry = tk.Entry(row, font=("Segoe UI", 10), width=20,
                             relief="solid", bd=1)
            entry.insert(0, default)
            entry.pack(side="left")
            self._nl_entries[key] = entry

        # Repayment
        repay_frame = tk.LabelFrame(container, text="Repayment",
                                    font=("Segoe UI", 11, "bold"), fg=BLUE,
                                    bg=WHITE, padx=10, pady=8)
        repay_frame.pack(fill="x", pady=(0, 10))

        row = tk.Frame(repay_frame, bg=WHITE)
        row.pack(fill="x", pady=2)
        tk.Label(row, text="Frequency:", font=("Segoe UI", 10),
                 bg=WHITE, width=18, anchor="w").pack(side="left")
        self._nl_freq = ttk.Combobox(row, width=17, state="readonly",
                                     values=[REPAY_MONTHLY, REPAY_WEEKLY])
        self._nl_freq.set(REPAY_MONTHLY)
        self._nl_freq.pack(side="left")

        row = tk.Frame(repay_frame, bg=WHITE)
        row.pack(fill="x", pady=2)
        tk.Label(row, text="Application Date:", font=("Segoe UI", 10),
                 bg=WHITE, width=18, anchor="w").pack(side="left")
        self._nl_date = tk.StringVar(value=datetime.date.today().isoformat())
        tk.Entry(row, textvariable=self._nl_date, font=("Segoe UI", 10),
                 width=20, relief="solid", bd=1).pack(side="left", padx=(0, 6))
        tk.Button(row, text="Calendar", font=("Segoe UI", 9),
                  bg=LIGHT_BLUE, fg=BLUE, relief="flat",
                  command=lambda: pick_date(container, self._nl_date)).pack(side="left")

        # Guarantors
        guar_frame = tk.LabelFrame(container, text="Guarantors",
                                   font=("Segoe UI", 11, "bold"), fg=BLUE,
                                   bg=WHITE, padx=10, pady=8)
        guar_frame.pack(fill="x", pady=(0, 10))

        self._nl_guarantors = []
        self._nl_guarantor_frame = tk.Frame(guar_frame, bg=WHITE)
        self._nl_guarantor_frame.pack(fill="x")
        self._nl_add_guarantor_row()

        # Documents
        doc_frame = tk.LabelFrame(container, text="Document Upload",
                                  font=("Segoe UI", 11, "bold"), fg=BLUE,
                                  bg=WHITE, padx=10, pady=8)
        doc_frame.pack(fill="x", pady=(0, 10))

        self._nl_doc_path = tk.StringVar()
        doc_row = tk.Frame(doc_frame, bg=WHITE)
        doc_row.pack(fill="x")
        tk.Button(doc_row, text="Browse File", font=("Segoe UI", 10),
                  bg=LIGHT_BLUE, fg=BLUE, relief="flat", padx=8, pady=3,
                  command=self._nl_browse_doc).pack(side="left")
        tk.Label(doc_row, textvariable=self._nl_doc_path, font=("Segoe UI", 9),
                 fg="#666666", bg=WHITE).pack(side="left", padx=(10, 0))

        # Submit
        tk.Button(container, text="SUBMIT LOAN APPLICATION",
                  font=("Segoe UI", 13, "bold"), bg=GREEN, fg=WHITE,
                  relief="flat", padx=20, pady=8,
                  command=self._nl_submit).pack(pady=(15, 10))

    def _nl_search_member(self):
        q = self._nl_member_search.get().strip()
        if not q:
            return
        conn = get_connection()
        row = conn.execute(
            """SELECT id, member_id, full_name FROM members
               WHERE member_id = ? OR full_name LIKE ? LIMIT 1""",
            (q, f"%{q}%")).fetchone()
        if row:
            self._nl_member_db_id = row["id"]
            self._nl_member_label.config(
                text=f"Selected: {row['full_name']} ({row['member_id']})")
        else:
            self._nl_member_db_id = None
            self._nl_member_label.config(text="Member not found.", fg="#D32F2F")

    def _nl_add_guarantor_row(self):
        row = tk.Frame(self._nl_guarantor_frame, bg=WHITE)
        row.pack(fill="x", pady=2)
        tk.Label(row, text=f"Guarantor {len(self._nl_guarantors) + 1}:",
                 font=("Segoe UI", 10), bg=WHITE, width=12, anchor="w").pack(side="left")
        search_var = tk.StringVar()
        tk.Entry(row, textvariable=search_var, font=("Segoe UI", 10),
                 width=25, relief="solid", bd=1).pack(side="left", padx=(0, 4))
        amt_var = tk.StringVar()
        tk.Entry(row, textvariable=amt_var, font=("Segoe UI", 10),
                 width=15, relief="solid", bd=1).pack(side="left", padx=(0, 4))
        tk.Label(row, text="Amount", font=("Segoe UI", 9),
                 fg="#888888", bg=WHITE).pack(side="left")

        self._nl_guarantors.append({"search_var": search_var, "amt_var": amt_var})

        if len(self._nl_guarantors) < 3:
            tk.Button(row, text="+", font=("Segoe UI", 10, "bold"),
                      bg=BLUE, fg=WHITE, relief="flat", padx=4,
                      command=self._nl_add_guarantor_row).pack(side="left", padx=(8, 0))

    def _nl_browse_doc(self):
        path = filedialog.askopenfilename(
            title="Select Document",
            filetypes=[("All Files", "*.*"), ("PDF", "*.pdf"), ("Images", "*.jpg;*.png")])
        if path:
            self._nl_doc_path.set(os.path.basename(path))
            self._nl_doc_path_full = path

    def _nl_submit(self):
        if not self._nl_member_db_id:
            messagebox.showerror("Error", "Search and select a member.")
            return

        try:
            principal = float(self._nl_entries["principal"].get().strip().replace(",", "").replace("₦", ""))
            if principal <= 0:
                raise ValueError("Principal must be positive.")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid principal: {e}")
            return

        try:
            interest = float(self._nl_entries["interest"].get().strip() or "0")
        except ValueError:
            interest = 0

        try:
            fee = float(self._nl_entries["processing_fee"].get().strip().replace(",", "").replace("₦", "") or "0")
        except ValueError:
            fee = 0

        try:
            charges = float(self._nl_entries["other_charges"].get().strip().replace(",", "").replace("₦", "") or "0")
        except ValueError:
            charges = 0

        freq = self._nl_freq.get()
        date_str = self._nl_date.get().strip()

        loan_id = safe_execute(
            create_loan,
            self._nl_member_db_id, principal, interest, fee, charges,
            freq, self.current_user.get("id"), date_str, True,
            context="create_loan")

        if not loan_id:
            return

        # Add guarantors
        conn = get_connection()
        loan_row = conn.execute("SELECT id FROM loans WHERE loan_id = ?",
                                (loan_id,)).fetchone()
        if loan_row:
            for g in self._nl_guarantors:
                q = g["search_var"].get().strip()
                amt_str = g["amt_var"].get().strip()
                if not q:
                    continue
                guarantor = conn.execute(
                    """SELECT id FROM members
                       WHERE member_id = ? OR full_name LIKE ? LIMIT 1""",
                    (q, f"%{q}%")).fetchone()
                if guarantor:
                    try:
                        amt = float(amt_str.replace(",", "").replace("₦", "") or "0")
                    except ValueError:
                        amt = 0
                    add_guarantor(loan_row["id"], guarantor["id"], amt)

            # Upload document
            if hasattr(self, "_nl_doc_path_full") and self._nl_doc_path_full:
                try:
                    add_loan_document(loan_row["id"], self._nl_member_db_id,
                                      os.path.basename(self._nl_doc_path_full),
                                      self._nl_doc_path_full,
                                      uploaded_by=self.current_user.get("id"))
                except Exception:
                    pass

        messagebox.showinfo("Success", f"Loan application submitted.\nLoan ID: {loan_id}")

        # Reset form
        self._nl_member_db_id = None
        self._nl_member_label.config(text="")
        self._nl_member_search.set("")
        for key in self._nl_entries:
            self._nl_entries[key].delete(0, tk.END)
        self._nl_entries["interest"].insert(0, str(get_setting("interest_rate") or "5"))
        self._nl_freq.set(REPAY_MONTHLY)
        self._nl_date.set(datetime.date.today().isoformat())
        self._nl_guarantors = []
        for child in self._nl_guarantor_frame.winfo_children():
            child.destroy()
        self._nl_add_guarantor_row()
        self._nl_doc_path.set("")
        self._nl_doc_path_full = ""

        # Refresh register list
        self._load_register_page(self._search_query)
