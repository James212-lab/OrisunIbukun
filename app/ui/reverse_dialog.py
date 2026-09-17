"""Shared reverse-transaction dialog used by Payments and Loans modules."""
import tkinter as tk
from tkinter import ttk, messagebox
from database.connection import get_connection
from engines.transaction_engine import reverse_transaction, cancel_charge
from utils.helpers import format_currency

BLUE = "#1565C0"
WHITE = "#FFFFFF"
RED = "#D32F2F"
LIGHT_GREY = "#F5F5F5"
LIGHT_YELLOW = "#FFF8E1"
AMBER = "#F9A825"

# Prefix used to identify charge rows in the treeview
_CHARGE_PREFIX = "[Charge] "


def open_reverse_dialog(parent, member_id, current_user, on_success):
    """Open a modal dialog to reverse a posted transaction or cancel a charge.

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
    win.title("Reverse Transaction / Cancel Charge")
    win.geometry("780x620")
    win.minsize(700, 500)
    win.configure(bg=WHITE)
    win.transient(parent)
    win.grab_set()

    # ── Title ──────────────────────────────────────────────────────
    tk.Label(win, text="Select a transaction to reverse, or a charge to cancel:",
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
                            font=("Segoe UI", 10), width=18, relief="solid", bd=1)
    search_entry.pack(side="left", padx=(4, 12))

    show_charges_var = tk.BooleanVar(value=False)
    tk.Checkbutton(filter_frame, text="Show outstanding charges",
                   variable=show_charges_var, font=("Segoe UI", 10),
                   bg=WHITE, command=lambda: _reload()
                   ).pack(side="left")

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

    # ── History toggle ─────────────────────────────────────────────
    history_var = tk.BooleanVar(value=False)

    def _show_history():
        history_var.set(not history_var.get())
        if history_var.get():
            hist_btn.config(text="Back to Transactions")
            cancel_btn.config(state="disabled")
            rev_btn.config(state="disabled")
            _load_history()
        else:
            hist_btn.config(text="View Reversal History")
            _reload()

    hist_btn = tk.Button(btn_row, text="View Reversal History",
                         font=("Segoe UI", 9), bg=LIGHT_GREY, fg=BLUE,
                         relief="flat", padx=8, pady=3, command=_show_history)
    hist_btn.pack(side="left")

    # ── Reverse button ─────────────────────────────────────────────
    def _confirm_reverse():
        sel = tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Pick a transaction first.")
            return
        iid = sel[0]
        if iid.startswith("CH-"):
            messagebox.showwarning("Invalid",
                                   "This is a charge, not a transaction. "
                                   "Use 'Cancel Charge' instead.")
            return
        txn_id = iid
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

    rev_btn = tk.Button(btn_row, text="Reverse Selected",
                        font=("Segoe UI", 11, "bold"),
                        bg=RED, fg=WHITE, relief="flat", padx=12, pady=4,
                        command=_confirm_reverse)
    rev_btn.pack(side="right")

    # ── Cancel Charge button ───────────────────────────────────────
    def _confirm_cancel_charge():
        sel = tree.selection()
        if not sel:
            return
        iid = sel[0]
        if not iid.startswith("CH-"):
            messagebox.showwarning("Invalid", "Select a charge row to cancel.")
            return
        charge_id = iid
        reason = reason_var.get().strip()
        if not reason:
            messagebox.showwarning("Reason",
                                   "Enter a reason for cancelling this charge.")
            return
        vals = tree.item(sel[0], "values")
        summary = (f"Charge: {vals[0]}\n"
                   f"Type: {vals[2]}\n"
                   f"Amount: {vals[3]}\n\n"
                   f"If this charge has partial payments, they will be "
                   f"reversed automatically.\n\n"
                   f"This action cannot be undone.")
        if not messagebox.askyesno("Confirm Cancel Charge", summary):
            return
        try:
            cancel_charge(charge_id, reason, current_user.get("id"))
            messagebox.showinfo("Cancelled", "Charge cancelled successfully.")
            win.destroy()
            on_success()
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    cancel_btn = tk.Button(btn_row, text="Cancel Charge",
                           font=("Segoe UI", 10, "bold"),
                           bg=AMBER, fg=WHITE, relief="flat", padx=10, pady=3,
                           command=_confirm_cancel_charge, state="disabled")
    cancel_btn.pack(side="right", padx=(0, 8))

    # ── Treeview ───────────────────────────────────────────────────
    cols = ("id", "date", "type", "amount", "description")
    tree = ttk.Treeview(win, columns=cols, show="headings", height=14)
    tree.heading("id", text="ID")
    tree.heading("date", text="Date")
    tree.heading("type", text="Type")
    tree.heading("amount", text="Amount")
    tree.heading("description", text="Description")
    tree.column("id", width=100)
    tree.column("date", width=80)
    tree.column("type", width=130)
    tree.column("amount", width=90, anchor="e")
    tree.column("description", width=220)
    vsb = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", padx=(15, 0), fill="both", expand=True)
    vsb.pack(side="right", fill="y", padx=(0, 15))

    tree.tag_configure("charge", background=LIGHT_YELLOW)

    def _on_select(_event):
        sel = tree.selection()
        if not sel or history_var.get():
            rev_btn.config(state="disabled")
            cancel_btn.config(state="disabled")
            return
        iid = sel[0]
        if iid.startswith("CH-"):
            rev_btn.config(state="disabled")
            cancel_btn.config(state="normal")
        else:
            rev_btn.config(state="normal")
            cancel_btn.config(state="disabled")

    tree.bind("<<TreeviewSelect>>", _on_select)

    conn = get_connection()

    def _load_transactions():
        tree.delete(*tree.get_children())
        rev_btn.config(state="disabled")
        cancel_btn.config(state="disabled")
        # Load payment transactions
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

        # Load outstanding charges if checkbox is checked
        if show_charges_var.get():
            cquery = """SELECT charge_id, charge_type, description,
                               amount, amount_paid, status
                        FROM member_charges
                        WHERE member_id = ? AND status != 'Paid'"""
            cparams = [member_id]
            if sVal:
                cquery += " AND (description LIKE ? OR charge_id LIKE ?)"
                cparams.extend([f"%{sVal}%", f"%{sVal}%"])
            cquery += " ORDER BY created_at DESC"
            charges = conn.execute(cquery, cparams).fetchall()
            for c in charges:
                outstanding = (c["amount"] or 0) - (c["amount_paid"] or 0)
                tag = "charge"
                tree.insert("", "end", iid=c["charge_id"], tags=(tag,),
                            values=(c["charge_id"],
                                    "",
                                    f"{_CHARGE_PREFIX}{c['charge_type']}",
                                    format_currency(outstanding),
                                    (c["description"] or "")[:60]))

    def _load_history():
        tree.delete(*tree.get_children())
        rev_btn.config(state="disabled")
        cancel_btn.config(state="disabled")
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

    def _reload():
        if history_var.get():
            _load_history()
        else:
            _load_transactions()

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
    wx = px + max(0, (pw - 780) // 2)
    wy = py + max(0, (ph - 620) // 2)
    win.geometry(f"780x620+{wx}+{wy}")
    win.lift()
    win.focus_force()
