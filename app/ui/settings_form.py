import tkinter as tk
from tkinter import ttk, messagebox

from database.connection import get_connection
from database.schema import get_setting, set_setting
from utils.helpers import hash_pin


class SettingsForm(tk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, bg="#FFFFFF")
        self.current_user = current_user
        self.pack(fill="both", expand=True)
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        header = tk.Frame(self, bg="#1565C0", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="Settings", font=("Segoe UI", 18, "bold"),
                 bg="#1565C0", fg="#FFFFFF").pack(pady=15, padx=20, anchor="w")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        self._build_coop_info_tab()
        self._build_financial_tab()
        self._build_users_tab()
        self._build_about_tab()

    def _build_coop_info_tab(self):
        frame = tk.Frame(self.notebook, bg="#FFFFFF", padx=20, pady=20)
        self.notebook.add(frame, text="  Cooperative Info  ")

        self.app_name_var = tk.StringVar()
        self.unit_name_var = tk.StringVar()
        self.currency_var = tk.StringVar()
        self.meeting_day_var = tk.StringVar()

        fields = [
            ("App Name:", self.app_name_var),
            ("Unit Name:", self.unit_name_var),
            ("Currency:", self.currency_var),
            ("Meeting Day:", self.meeting_day_var),
        ]
        for i, (label_text, var) in enumerate(fields):
            tk.Label(frame, text=label_text, font=("Segoe UI", 11),
                     bg="#FFFFFF", fg="#333333", anchor="w").grid(row=i, column=0, sticky="w", pady=(10, 2))
            tk.Entry(frame, textvariable=var, font=("Segoe UI", 11),
                     relief=tk.SOLID, bd=1, width=40).grid(row=i, column=1, sticky="w", padx=(15, 0), pady=(10, 2))

        tk.Button(frame, text="Save", font=("Segoe UI", 11, "bold"),
                  bg="#1565C0", fg="#FFFFFF", relief=tk.FLAT, cursor="hand2",
                  padx=20, pady=6, command=self._save_coop_info).grid(row=len(fields), column=1, sticky="w", padx=(15, 0), pady=(20, 0))

    def _build_financial_tab(self):
        frame = tk.Frame(self.notebook, bg="#FFFFFF", padx=20, pady=20)
        self.notebook.add(frame, text="  Financial  ")

        self.share_price_var = tk.StringVar()
        self.entrance_fee_var = tk.StringVar()
        self.min_savings_withdrawal_var = tk.StringVar()
        self.max_loan_multiplier_var = tk.StringVar()
        self.required_guarantors_var = tk.StringVar()
        self.interest_rate_var = tk.StringVar()
        self.interest_method_var = tk.StringVar(value="Flat")
        self.late_payment_penalty_var = tk.StringVar()
        self.absent_fine_var = tk.StringVar()

        fields = [
            ("Share Price:", self.share_price_var),
            ("Entrance Fee:", self.entrance_fee_var),
            ("Min Savings Withdrawal:", self.min_savings_withdrawal_var),
            ("Max Loan Multiplier:", self.max_loan_multiplier_var),
            ("Required Guarantors:", self.required_guarantors_var),
            ("Interest Rate (%):", self.interest_rate_var),
            ("Late Payment Penalty:", self.late_payment_penalty_var),
            ("Absence Fine:", self.absent_fine_var),
        ]
        for i, (label_text, var) in enumerate(fields):
            tk.Label(frame, text=label_text, font=("Segoe UI", 11),
                     bg="#FFFFFF", fg="#333333", anchor="w").grid(row=i, column=0, sticky="w", pady=(8, 2))
            tk.Entry(frame, textvariable=var, font=("Segoe UI", 11),
                     relief=tk.SOLID, bd=1, width=25).grid(row=i, column=1, sticky="w", padx=(15, 0), pady=(8, 2))

        method_row = len(fields)
        tk.Label(frame, text="Interest Method:", font=("Segoe UI", 11),
                 bg="#FFFFFF", fg="#333333", anchor="w").grid(row=method_row, column=0, sticky="w", pady=(8, 2))
        ttk.Combobox(frame, textvariable=self.interest_method_var,
                     values=["Flat", "Reducing"], state="readonly", width=22).grid(row=method_row, column=1, sticky="w", padx=(15, 0), pady=(8, 2))

        tk.Button(frame, text="Save", font=("Segoe UI", 11, "bold"),
                  bg="#1565C0", fg="#FFFFFF", relief=tk.FLAT, cursor="hand2",
                  padx=20, pady=6, command=self._save_financial).grid(row=method_row + 1, column=1, sticky="w", padx=(15, 0), pady=(20, 0))

    def _build_users_tab(self):
        frame = tk.Frame(self.notebook, bg="#FFFFFF", padx=20, pady=20)
        self.notebook.add(frame, text="  Users  ")

        btn_frame = tk.Frame(frame, bg="#FFFFFF")
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Button(btn_frame, text="Add User", font=("Segoe UI", 10, "bold"),
                  bg="#1565C0", fg="#FFFFFF", relief=tk.FLAT, cursor="hand2",
                  padx=15, pady=5, command=self._add_user_dialog).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="Deactivate", font=("Segoe UI", 10, "bold"),
                  bg="#E3F2FD", fg="#1565C0", relief=tk.FLAT, cursor="hand2",
                  padx=15, pady=5, command=self._deactivate_user).pack(side=tk.LEFT, padx=(10, 0))

        columns = ("id", "username", "role", "active", "last_login")
        self.users_tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        self.users_tree.heading("id", text="ID")
        self.users_tree.heading("username", text="Username")
        self.users_tree.heading("role", text="Role")
        self.users_tree.heading("active", text="Active")
        self.users_tree.heading("last_login", text="Last Login")
        self.users_tree.column("id", width=0, stretch=False)
        self.users_tree.column("username", width=150)
        self.users_tree.column("role", width=120)
        self.users_tree.column("active", width=70)
        self.users_tree.column("last_login", width=150)

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=vsb.set)
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._load_users()

    def _build_about_tab(self):
        frame = tk.Frame(self.notebook, bg="#FFFFFF", padx=20, pady=20)
        self.notebook.add(frame, text="  About  ")

        info = [
            ("App Name:", "ORISUN IBUKUN Cooperative"),
            ("Unit:", "Owode Unit"),
            ("Version:", "1.0.0"),
            ("Schema Version:", "1"),
        ]
        for i, (label_text, value) in enumerate(info):
            tk.Label(frame, text=label_text, font=("Segoe UI", 11, "bold"),
                     bg="#FFFFFF", fg="#333333", anchor="w").grid(row=i, column=0, sticky="w", pady=(12, 2))
            tk.Label(frame, text=value, font=("Segoe UI", 11),
                     bg="#FFFFFF", fg="#666666", anchor="w").grid(row=i, column=1, sticky="w", padx=(15, 0), pady=(12, 2))

    def _load_settings(self):
        self.app_name_var.set(get_setting("app_name") or "ORISUN IBUKUN")
        self.unit_name_var.set(get_setting("unit_name") or "Owode Unit")
        self.currency_var.set(get_setting("currency") or "₦")
        self.meeting_day_var.set(get_setting("meeting_day") or "Friday")
        self.share_price_var.set(get_setting("share_price") or "1000")
        self.entrance_fee_var.set(get_setting("entrance_fee") or "5000")
        self.min_savings_withdrawal_var.set(get_setting("min_savings_withdrawal") or "10000")
        self.max_loan_multiplier_var.set(get_setting("max_loan_multiplier") or "3")
        self.required_guarantors_var.set(get_setting("required_guarantors") or "2")
        self.interest_rate_var.set(get_setting("interest_rate") or "5")
        self.interest_method_var.set(get_setting("interest_method") or "Flat")
        self.late_payment_penalty_var.set(get_setting("late_payment_penalty") or "500")
        self.absent_fine_var.set(get_setting("absent_fine") or "0")

    def _save_coop_info(self):
        set_setting("app_name", self.app_name_var.get().strip())
        set_setting("unit_name", self.unit_name_var.get().strip())
        set_setting("currency", self.currency_var.get().strip())
        set_setting("meeting_day", self.meeting_day_var.get().strip())
        messagebox.showinfo("Saved", "Cooperative info saved successfully.")

    def _save_financial(self):
        set_setting("share_price", self.share_price_var.get().strip())
        set_setting("entrance_fee", self.entrance_fee_var.get().strip())
        set_setting("min_savings_withdrawal", self.min_savings_withdrawal_var.get().strip())
        set_setting("max_loan_multiplier", self.max_loan_multiplier_var.get().strip())
        set_setting("required_guarantors", self.required_guarantors_var.get().strip())
        set_setting("interest_rate", self.interest_rate_var.get().strip())
        set_setting("interest_method", self.interest_method_var.get())
        set_setting("late_payment_penalty", self.late_payment_penalty_var.get().strip())
        set_setting("absent_fine", self.absent_fine_var.get().strip() or "0")
        messagebox.showinfo("Saved", "Financial settings saved successfully.")

    def _load_users(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        conn = get_connection()
        rows = conn.execute(
            """SELECT u.id, u.username, r.name as role_name, u.is_active, u.last_login
               FROM users u JOIN roles r ON u.role_id = r.id
               ORDER BY u.username"""
        ).fetchall()
        for row in rows:
            active = "Yes" if row["is_active"] else "No"
            self.users_tree.insert("", tk.END, values=(
                row["id"], row["username"], row["role_name"], active, row["last_login"] or "Never",
            ))

    def _add_user_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Add User")
        dialog.geometry("350x280")
        dialog.resizable(False, False)
        dialog.configure(bg="#FFFFFF")
        dialog.grab_set()

        tk.Label(dialog, text="Add New User", font=("Segoe UI", 14, "bold"),
                 bg="#FFFFFF", fg="#1565C0").pack(pady=(15, 10))

        fields_frame = tk.Frame(dialog, bg="#FFFFFF", padx=20)
        fields_frame.pack(fill=tk.X)

        tk.Label(fields_frame, text="Username:", font=("Segoe UI", 10),
                 bg="#FFFFFF", fg="#333333", anchor="w").pack(fill=tk.X, pady=(5, 2))
        username_entry = tk.Entry(fields_frame, font=("Segoe UI", 10), relief=tk.SOLID, bd=1)
        username_entry.pack(fill=tk.X, pady=(0, 5))

        tk.Label(fields_frame, text="PIN:", font=("Segoe UI", 10),
                 bg="#FFFFFF", fg="#333333", anchor="w").pack(fill=tk.X, pady=(5, 2))
        pin_entry = tk.Entry(fields_frame, font=("Segoe UI", 10), relief=tk.SOLID, bd=1, show="*")
        pin_entry.pack(fill=tk.X, pady=(0, 5))

        tk.Label(fields_frame, text="Role:", font=("Segoe UI", 10),
                 bg="#FFFFFF", fg="#333333", anchor="w").pack(fill=tk.X, pady=(5, 2))

        conn = get_connection()
        roles = conn.execute("SELECT id, name FROM roles ORDER BY name").fetchall()
        role_map = {r["name"]: r["id"] for r in roles}
        role_names = list(role_map.keys())

        role_var = tk.StringVar(value=role_names[0] if role_names else "")
        ttk.Combobox(fields_frame, textvariable=role_var,
                     values=role_names, state="readonly").pack(fill=tk.X, pady=(0, 5))

        def save_user():
            uname = username_entry.get().strip()
            pin = pin_entry.get().strip()
            role_name = role_var.get()
            if not uname or not pin:
                messagebox.showwarning("Missing Fields", "Username and PIN are required.", parent=dialog)
                return
            if len(pin) < 4:
                messagebox.showwarning("Invalid PIN", "PIN must be at least 4 digits.", parent=dialog)
                return

            pin_hashed = hash_pin(pin)
            role_id = role_map.get(role_name)
            try:
                conn2 = get_connection()
                conn2.execute(
                    "INSERT INTO users (username, pin_hash, role_id, is_active) VALUES (?, ?, ?, 1)",
                    (uname, pin_hashed, role_id),
                )
                conn2.commit()
                messagebox.showinfo("Success", f"User '{uname}' created.", parent=dialog)
                dialog.destroy()
                self._load_users()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dialog)

        tk.Button(fields_frame, text="Create User", font=("Segoe UI", 10, "bold"),
                  bg="#1565C0", fg="#FFFFFF", relief=tk.FLAT, cursor="hand2",
                  padx=15, pady=5, command=save_user).pack(pady=(15, 0))

    def _deactivate_user(self):
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a user to deactivate.")
            return
        values = self.users_tree.item(selected[0], "values")
        user_db_id = values[0]
        username = values[1]

        if username == self.current_user.get("username"):
            messagebox.showwarning("Cannot Deactivate", "You cannot deactivate your own account.")
            return
        if values[3] == "No":
            messagebox.showinfo("Info", f"User '{username}' is already inactive.")
            return

        confirm = messagebox.askyesno("Confirm", f"Deactivate user '{username}'?")
        if not confirm:
            return

        conn = get_connection()
        conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_db_id,))
        conn.commit()
        messagebox.showinfo("Done", f"User '{username}' deactivated.")
        self._load_users()
