"""Shared reverse-transaction dialog used by Payments and Loans modules."""
import tkinter as tk
from tkinter import ttk, messagebox
from database.connection import get_connection
from engines.transaction_engine import reverse_transaction
from utils.helpers import format_currency

BLUE = "#1565C0"
WHITE = "#FFFFFF"
RED = "#D32F2F"
LIGHT_GREY = "#F5F5F5"


def open_reverse_dialog(parent, member_id, current_user, on_success):
    """Open a modal dialog to reverse a posted transaction.

    Parameters
    ----------
    parent : tk.Widget
        Parent widget (used for transient/grab).
    member_id : int
        Database ID of the member whose transactions to show.
    current_user : dict
        Must contain 'id' and 'role'.
    on_success : callable
        Called after a successful reversal (typically refreshes the parent view).
    """
    win = tk.Toplevel(parent)
    win.title("Reverse Transaction")
    win.geometry("750x600")
    win.minsize(700, 500)
    win.configure(bg=WHITE)
    win.transient(parent)
    win.grab_set()

    # ── Title ──────────────────────────────────────────────────────
    tk.Label(win, text="Select a Posted transaction to reverse:",
             font=("Segoe UI", 11, "bold"), fg=BLUE, bg=WHITE
             ).pack(padx=15, pady=(12, 2), anchor="w")

    # ── Filter bar ─────────────────────────────────────────────────
    filter_frame = tk.Frame(win, bg=WHITE)
    filter_frame.pack(fill="x", padx=15, pady=(0, 6))

    tk.Label(filter_frame, text="Type:", font=("Segoe UI", 10),
             bg=WHITE).pack(side="left")
    type_var = tk.StringVar(value="All")
    type_combo = ttk.Combobox(filter_frame, textvariable=type_var, width=16,
                              values=["All", "Savings", "Loan Repayment",
                                      "Charge Payment", "Expense",
                                      "Withdrawal", "HQ Funding",
                                      "Loan Disbursement"],
                              state="readonly")
    type_combo.pack(side="left", padx=(4, 12))

    tk.Label(filter_frame, text="Search:", font=("Segoe UI", 10),
             bg=WHITE).pack(side="left")
    search_var = tk.StringVar()
    search_entry = tk.Entry(filter_frame, textvariable=search_var,
                            font=("Segoe UI", 10), width=20, relief="solid", bd=1)
    search_entry.pack(side="left", padx=(4, 0))

    # ── Bottom action bar (packed first to avoid clipping) ─────────
    reason_var = tk.StringVar()
    action_frame = tk.Frame(win, bg=WHITE)
    action_frame.pack(side="bottom", fill="x", padx=15, pady=(6, 10))

    reason_row = tk.Frame(action_frame, bg=WHITE)
    reason_row.pack(fill="x")
    tk.Label(reason_row, text="Reason:", font=("Segoe UI", 10),
             bg=WHITE).pack(side="left")
    tk.Entry(reason_row, textvariable=reason_var, font=("Segoe UI", 10),
             width=40, relief="solid", bd=1).pack(side="left", padx=(6, 0))

    btn_row = tk.Frame(action_frame, bg=WHITE)
    btn_row.pack(fill="x", pady=(6, 0))

    history_var = tk.BooleanVar(value=False)

    def _show_history():
        history_var.set(not history_var.get())
        if history_var.get():
            hist_btn.config(text="Back to Transactions")
            _load_history()
        else:
            hist_btn.config(text="View Reversal History")
            _load_transactions()

    hist_btn = tk.Button(btn_row, text="View Reversal History",
                         font=("Segoe UI", 9), bg=LIGHT_GREY, fg=BLUE,
                         relief="flat", padx=8, pady=3, command=_show_history)
    hist_btn.pack(side="left")

    def _confirm_reverse():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Pick a transaction first.")
            return
        txn_id = sel[0]
        reason = reason_var.get().strip()
        if not reason:
            messagebox.showwarning("Reason", "Enter a reason for reversal.")
            return
        vals = tree.item(sel[0], "values")
        summary = (f"Transaction: {vals[0]}\n"
                   f"Date: {vals[1]}  Type: {vals[2]}\n"
                   f"Amount: {vals[3]}\n\n"
                   f"This action cannot be undone.")
        if not messagebox.askyesno("Confirm Reversal", summary):
            return
        try:
            reverse_transaction(txn_id, reason, current_user.get("id"))
            messagebox.showinfo("Reversed", "Transaction reversed successfully.")
            win.destroy()
            on_success()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    tk.Button(btn_row, text="Reverse Selected", font=("Segoe UI", 11, "bold"),
              bg=RED, fg=WHITE, relief="flat", padx=12, pady=4,
              command=_confirm_reverse).pack(side="right")

    # ── Treeview ───────────────────────────────────────────────────
    cols = ("txn_id", "date", "type", "amount", "description")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=14)
    tree.heading("txn_id", text="Txn ID")
    tree.heading("date", text="Date")
    tree.heading("type", text="Type")
    tree.heading("amount", text="Amount")
    tree.heading("description", text="Description")
    tree.column("txn_id", width=90)
    tree.column("date", width=80)
    tree.column("type", width=120)
    tree.column("amount", width=90, anchor="e")
    tree.column("description", width=220)
    vsb = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", padx=(15, 0), fill="both", expand=True)
    vsb.pack(side="right", fill="y", padx=(0, 15))

    conn = get_connection()

    def _load_transactions():
        tree.delete(*tree.get_children())
        query = """SELECT transaction_id, date, transaction_type, amount, description
                   FROM transactions
                   WHERE member_id = ? AND status = 'Posted'"""
        params = [member_id]
        tFilter = type_var.get()
        if tFilter != "All":
            query += " AND transaction_type = ?"
            params.append(tFilter)
        sVal = search_var.get().strip()
        if sVal:
            query += " AND (description LIKE ? OR transaction_id LIKE ?)"
            params.extend([f"%{sVal}%", f"%{sVal}%"])
        query += " ORDER BY date DESC, id DESC LIMIT 200"
        txns = conn.execute(query, params).fetchall()
        for t in txns:
            tree.insert("", "end", iid=t["transaction_id"],
                        values=(t["transaction_id"], t["date"],
                                t["transaction_type"],
                                format_currency(t["amount"] or 0),
                                (t["description"] or "")[:60]))

    def _load_history():
        tree.delete(*tree.get_children())
        txns = conn.execute(
            """SELECT r.original_transaction_id, r.reversed_at,
                      r.reason, t.transaction_type, t.amount, u.username
               FROM transaction_reversals r
               JOIN transactions t ON t.transaction_id = r.original_transaction_id
               LEFT JOIN users u ON u.id = r.reversed_by
               WHERE t.member_id = ?
               ORDER BY r.reversed_at DESC LIMIT 100""",
            (member_id,),
        ).fetchall()
        for t in txns:
            tree.insert("", "end",
                        values=(t["original_transaction_id"],
                                t["reversed_at"][:10] if t["reversed_at"] else "",
                                t["transaction_type"],
                                format_currency(t["amount"] or 0),
                                f"Reversed by {t['username'] or '?'}: {t['reason'] or ''}"[:60]))

    def _on_filter_change(*_args):
        if not history_var.get():
            _load_transactions()

    type_var.trace_add("write", _on_filter_change)
    search_var.trace_add("write", _on_filter_change)

    _load_transactions()

    # ── Center over parent ─────────────────────────────────────────
    win.update_idletasks()
    pw = parent.winfo_width()
    ph = parent.winfo_height()
    px = parent.winfo_rootx()
    py = parent.winfo_rooty()
    wx = px + max(0, (pw - 750) // 2)
    wy = py + max(0, (ph - 600) // 2)
    win.geometry(f"750x600+{wx}+{wy}")
    win.lift()
    win.focus_force()
