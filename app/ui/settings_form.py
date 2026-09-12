import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.font as tkfont

from constants import APP_VERSION, GITHUB_REPO
from database.connection import get_connection
from database.schema import get_setting, set_setting
from utils.helpers import hash_pin

MASTER_PIN_HASH_KEY = "master_pin_hash"
UPDATE_UNLOCK_KEY = "__update_unlocked"


class SettingsForm(tk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, bg="#FFFFFF")
        self.current_user = current_user
        self._update_unlocked = False
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

    # ── Cooperative Info ─────────────────────────────────────────

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
                     bg="#FFFFFF", fg="#333333", anchor="w").grid(
                row=i, column=0, sticky="w", pady=(10, 2))
            tk.Entry(frame, textvariable=var, font=("Segoe UI", 11),
                     relief=tk.SOLID, bd=1, width=40).grid(
                row=i, column=1, sticky="w", padx=(15, 0), pady=(10, 2))

        tk.Button(frame, text="Save", font=("Segoe UI", 11, "bold"),
                  bg="#1565C0", fg="#FFFFFF", relief=tk.FLAT, cursor="hand2",
                  padx=20, pady=6, command=self._save_coop_info).grid(
            row=len(fields), column=1, sticky="w", padx=(15, 0), pady=(20, 0))

    # ── Financial ────────────────────────────────────────────────

    def _build_financial_tab(self):
        frame = tk.Frame(self.notebook, bg="#FFFFFF", padx=20, pady=20)
        self.notebook.add(frame, text="  Financial  ")

        self.entrance_fee_var = tk.StringVar()
        self.min_savings_withdrawal_var = tk.StringVar()
        self.max_loan_multiplier_var = tk.StringVar()
        self.required_guarantors_var = tk.StringVar()
        self.interest_rate_var = tk.StringVar()
        self.interest_method_var = tk.StringVar(value="Flat")
        self.late_payment_penalty_var = tk.StringVar()
        self.absent_fine_var = tk.StringVar()

        fields = [
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
                     bg="#FFFFFF", fg="#333333", anchor="w").grid(
                row=i, column=0, sticky="w", pady=(8, 2))
            tk.Entry(frame, textvariable=var, font=("Segoe UI", 11),
                     relief=tk.SOLID, bd=1, width=25).grid(
                row=i, column=1, sticky="w", padx=(15, 0), pady=(8, 2))

        method_row = len(fields)
        tk.Label(frame, text="Interest Method:", font=("Segoe UI", 11),
                 bg="#FFFFFF", fg="#333333", anchor="w").grid(
            row=method_row, column=0, sticky="w", pady=(8, 2))
        ttk.Combobox(frame, textvariable=self.interest_method_var,
                     values=["Flat", "Reducing"], state="readonly", width=22).grid(
            row=method_row, column=1, sticky="w", padx=(15, 0), pady=(8, 2))

        tk.Button(frame, text="Save", font=("Segoe UI", 11, "bold"),
                  bg="#1565C0", fg="#FFFFFF", relief=tk.FLAT, cursor="hand2",
                  padx=20, pady=6, command=self._save_financial).grid(
            row=method_row + 1, column=1, sticky="w", padx=(15, 0), pady=(20, 0))

    # ── Users ────────────────────────────────────────────────────

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
                  padx=15, pady=5, command=self._deactivate_user).pack(
            side=tk.LEFT, padx=(10, 0))

        columns = ("id", "username", "role", "active", "last_login")
        self.users_tree = ttk.Treeview(
            frame, columns=columns, show="headings", selectmode="browse")
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

        vsb = ttk.Scrollbar(frame, orient=tk.VERTICAL,
                            command=self.users_tree.yview)
        self.users_tree.configure(yscrollcommand=vsb.set)
        self.users_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self._load_users()

    # ── About tab (version + updates + master PIN) ───────────────

    def _build_about_tab(self):
        frame = tk.Frame(self.notebook, bg="#FFFFFF", padx=20, pady=20)
        self.notebook.add(frame, text="  About  ")

        # ── App info ──
        from database.schema import SCHEMA_VERSION
        info = [
            ("App Name:", "ORISUN IBUKUN Cooperative"),
            ("Unit:", "Owode Unit"),
            ("Version:", APP_VERSION),
            ("Schema Version:", str(SCHEMA_VERSION)),
        ]
        for i, (label_text, value) in enumerate(info):
            tk.Label(frame, text=label_text, font=("Segoe UI", 11, "bold"),
                     bg="#FFFFFF", fg="#333333", anchor="w").grid(
                row=i, column=0, sticky="w", pady=(12, 2))
            tk.Label(frame, text=value, font=("Segoe UI", 11),
                     bg="#FFFFFF", fg="#666666", anchor="w").grid(
                row=i, column=1, sticky="w", padx=(15, 0), pady=(12, 2))

        sep = ttk.Separator(frame, orient="horizontal")
        sep.grid(row=len(info), column=0, columnspan=2, sticky="ew",
                 pady=(15, 5))

        # ── Software Updates ──
        row = len(info) + 1
        tk.Label(frame, text="Software Updates",
                 font=("Segoe UI", 13, "bold"), bg="#FFFFFF", fg="#1565C0",
                 anchor="w").grid(row=row, column=0, columnspan=2, sticky="w",
                                  pady=(5, 10))

        row += 1
        self.update_status_var = tk.StringVar(value="Locked")
        tk.Label(frame, text="Status:", font=("Segoe UI", 11, "bold"),
                 bg="#FFFFFF", fg="#333333", anchor="w").grid(
            row=row, column=0, sticky="w", pady=(4, 2))
        tk.Label(frame, textvariable=self.update_status_var,
                 font=("Segoe UI", 11), bg="#FFFFFF", fg="#666666",
                 anchor="w").grid(
            row=row, column=1, sticky="w", padx=(15, 0), pady=(4, 2))

        row += 1
        self.update_btn = tk.Button(
            frame, text="Unlock (PIN)", font=("Segoe UI", 10, "bold"),
            bg="#E3F2FD", fg="#1565C0", relief=tk.FLAT, cursor="hand2",
            padx=12, pady=4, command=self._toggle_update_lock)
        self.update_btn.grid(row=row, column=1, sticky="w", padx=(15, 0),
                             pady=(6, 0))

        row += 1
        self.update_notes_var = tk.StringVar(value="")
        notes_font = tkfont.Font(family="Segoe UI", size=10)
        self.update_notes_label = tk.Label(
            frame, textvariable=self.update_notes_var,
            font=notes_font, bg="#FFFFFF", fg="#333333",
            anchor="w", justify="left", wraplength=450)
        self.update_notes_label.grid(
            row=row, column=0, columnspan=2, sticky="w",
            padx=(0, 0), pady=(8, 0))

        row += 1
        self.check_btn = tk.Button(
            frame, text="Check for Updates",
            font=("Segoe UI", 10, "bold"), bg="#1565C0", fg="#FFFFFF",
            relief=tk.FLAT, cursor="hand2", padx=12, pady=4,
            command=self._check_for_update, state="disabled")
        self.check_btn.grid(row=row, column=1, sticky="w", padx=(15, 0),
                            pady=(8, 0))

        sep2 = ttk.Separator(frame, orient="horizontal")
        sep2.grid(row=row + 1, column=0, columnspan=2, sticky="ew",
                  pady=(15, 5))

        # ── Master PIN ──
        row += 2
        tk.Label(frame, text="Master PIN",
                 font=("Segoe UI", 13, "bold"), bg="#FFFFFF", fg="#1565C0",
                 anchor="w").grid(row=row, column=0, columnspan=2, sticky="w",
                                  pady=(5, 10))

        row += 1
        has_mp = bool(get_setting(MASTER_PIN_HASH_KEY))
        mp_status = "Set" if has_mp else "Not set"
        self.master_pin_status_var = tk.StringVar(value=mp_status)
        tk.Label(frame, text="Master PIN:", font=("Segoe UI", 11, "bold"),
                 bg="#FFFFFF", fg="#333333", anchor="w").grid(
            row=row, column=0, sticky="w", pady=(4, 2))
        tk.Label(frame, textvariable=self.master_pin_status_var,
                 font=("Segoe UI", 11), bg="#FFFFFF", fg="#666666",
                 anchor="w").grid(
            row=row, column=1, sticky="w", padx=(15, 0), pady=(4, 2))

        row += 1
        btn_row = tk.Frame(frame, bg="#FFFFFF")
        btn_row.grid(row=row, column=1, sticky="w", padx=(15, 0), pady=(6, 0))
        tk.Button(btn_row, text="Change", font=("Segoe UI", 10, "bold"),
                  bg="#E3F2FD", fg="#1565C0", relief=tk.FLAT, cursor="hand2",
                  padx=10, pady=3,
                  command=self._change_master_pin).pack(side=tk.LEFT)
        tk.Button(btn_row, text="Remove", font=("Segoe UI", 10, "bold"),
                  bg="#FFEBEE", fg="#D32F2F", relief=tk.FLAT, cursor="hand2",
                  padx=10, pady=3,
                  command=self._remove_master_pin).pack(side=tk.LEFT, padx=(8, 0))

    # ── Update lock / check ──────────────────────────────────────

    def _toggle_update_lock(self):
        if self._update_unlocked:
            self._update_unlocked = False
            self.update_btn.config(text="Unlock (PIN)")
            self.update_status_var.set("Locked")
            self.check_btn.config(state="disabled")
            self.update_notes_var.set("")
            return

        # Prompt for logged-in user's PIN
        pin = tk.simpledialog.askstring(
            "Verify PIN",
            "Enter your login PIN to unlock updates:",
            show="*", parent=self)
        if not pin:
            return
        stored = self._get_user_pin_hash()
        if hash_pin(pin) != stored:
            messagebox.showerror("Incorrect PIN", "That PIN is wrong.")
            return
        self._update_unlocked = True
        self.update_btn.config(text="Lock")
        self.update_status_var.set("Unlocked")
        self.check_btn.config(state="normal")

    def _get_user_pin_hash(self) -> str:
        conn = get_connection()
        row = conn.execute(
            "SELECT pin_hash FROM users WHERE id = ?",
            (self.current_user.get("id"),)).fetchone()
        return row["pin_hash"] if row else ""

    def _check_for_update(self):
        if not self._update_unlocked:
            return
        self.update_status_var.set("Checking...")
        self.check_btn.config(state="disabled")
        self.update_notes_var.set("")

        def _worker():
            from engines.update_engine import check_for_update, UpdateError
            try:
                info = check_for_update()
                self.after(0, lambda: self._on_update_result(info))
            except UpdateError as exc:
                self.after(0, lambda: self._on_update_error(str(exc)))
            except Exception as exc:
                self.after(0, lambda: self._on_update_error(str(exc)))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_update_result(self, info):
        if not self._update_unlocked:
            return
        self.check_btn.config(state="normal")
        if info is None:
            self.update_status_var.set(f"Up to date (v{APP_VERSION})")
            self.update_notes_var.set("")
            return

        self.update_status_var.set(
            f"New version: v{info['version']}  ({info['published_at'][:10]})")
        notes = info.get("notes", "") or ""
        self.update_notes_var.set(f"Release notes:\n{notes}" if notes else "")
        self._pending_update = info

        if messagebox.askyesno(
            "Update Available",
            f"Version {info['version']} is available.\n\n"
            f"Published: {info['published_at'][:10]}\n"
            "Download and apply now?"
        ):
            self._download_and_apply(info)

    def _on_update_error(self, msg):
        if not self._update_unlocked:
            return
        self.check_btn.config(state="normal")
        self.update_status_var.set("Update check failed")
        self.update_notes_var.set(msg)
        messagebox.showerror("Update Error", msg)

    def _download_and_apply(self, info):
        if not self._update_unlocked:
            return
        from engines.update_engine import (
            download_update, apply_update, _extract_expected_sha256, can_update)

        if not can_update():
            messagebox.showinfo(
                "Auto-Update",
                "Auto-update requires the built OrisunIbukun.exe.\n"
                "Run the exe to use this feature.")
            return

        dest_dir = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")),
                                "orisun_update")
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, "OrisunIbukun_new.exe")

        expected_sha = _extract_expected_sha256(info.get("notes", ""))
        if not expected_sha:
            messagebox.showwarning(
                "No Checksum",
                "The release notes do not contain a SHA-256 checksum.\n"
                "Download blocked for security. Please ask the developer "
                "to add 'SHA256: <hex>' to the release notes.")
            return

        progress_win = tk.Toplevel(self)
        progress_win.title("Downloading Update")
        progress_win.geometry("380x130")
        progress_win.resizable(False, False)
        progress_win.configure(bg="#FFFFFF")
        progress_win.transient(self.winfo_toplevel())
        progress_win.grab_set()

        tk.Label(progress_win,
                 text=f"Downloading v{info['version']}...",
                 font=("Segoe UI", 11, "bold"), bg="#FFFFFF", fg="#1565C0"
                 ).pack(pady=(15, 8))
        progress_var = tk.DoubleVar(value=0)
        pbar = ttk.Progressbar(progress_win, variable=progress_var,
                               maximum=100, length=320)
        pbar.pack(pady=(0, 5))
        pct_var = tk.StringVar(value="0%")
        tk.Label(progress_win, textvariable=pct_var,
                 font=("Segoe UI", 10), bg="#FFFFFF", fg="#666666").pack()

        def _do_download():
            from engines.update_engine import download_update as _dl, UpdateError
            try:
                def on_progress(downloaded, total):
                    if total:
                        pct = (downloaded / total) * 100
                        self.after(0, lambda: progress_var.set(pct))
                        self.after(0, lambda: pct_var.set(f"{pct:.0f}%"))
                _dl(info["download_url"], dest, expected_sha,
                    progress_cb=on_progress)
                self.after(0, lambda: self._on_download_done(
                    dest, progress_win))
            except UpdateError as exc:
                self.after(0, lambda: self._on_download_fail(
                    str(exc), progress_win))

        threading.Thread(target=_do_download, daemon=True).start()

    def _on_download_done(self, dest, progress_win):
        progress_win.destroy()
        from engines.update_engine import apply_update as _apply
        if messagebox.askyesno(
            "Update Ready",
            "Download complete. Close the app now to apply the update?"
        ):
            try:
                _apply(dest)
            except Exception as exc:
                messagebox.showerror("Apply Error", str(exc))
                return
            self.winfo_toplevel().destroy()

    def _on_download_fail(self, msg, progress_win):
        progress_win.destroy()
        messagebox.showerror("Download Failed", msg)

    # ── Master PIN management ────────────────────────────────────

    def _change_master_pin(self):
        dialog = tk.Toplevel(self)
        dialog.title("Change Master PIN")
        dialog.geometry("380x280")
        dialog.resizable(False, False)
        dialog.configure(bg="#FFFFFF")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        tk.Label(dialog, text="Change Master PIN",
                 font=("Segoe UI", 14, "bold"),
                 bg="#FFFFFF", fg="#1565C0").pack(pady=(15, 10))

        f = tk.Frame(dialog, bg="#FFFFFF", padx=20)
        f.pack(fill="x")

        tk.Label(f, text="Current Master PIN:", font=("Segoe UI", 10),
                 bg="#FFFFFF").pack(fill="x", pady=(5, 2))
        cur_pin = tk.Entry(f, font=("Segoe UI", 10), show="*",
                           relief=tk.SOLID, bd=1)
        cur_pin.pack(fill="x", pady=(0, 5))

        tk.Label(f, text="New Master PIN:", font=("Segoe UI", 10),
                 bg="#FFFFFF").pack(fill="x", pady=(5, 2))
        new_pin = tk.Entry(f, font=("Segoe UI", 10), show="*",
                           relief=tk.SOLID, bd=1)
        new_pin.pack(fill="x", pady=(0, 5))

        tk.Label(f, text="Confirm New PIN:", font=("Segoe UI", 10),
                 bg="#FFFFFF").pack(fill="x", pady=(5, 2))
        conf_pin = tk.Entry(f, font=("Segoe UI", 10), show="*",
                            relief=tk.SOLID, bd=1)
        conf_pin.pack(fill="x", pady=(0, 5))

        def do_change():
            old = cur_pin.get().strip()
            new = new_pin.get().strip()
            conf = conf_pin.get().strip()
            stored = get_setting(MASTER_PIN_HASH_KEY)
            if hash_pin(old) != stored:
                messagebox.showerror("Error", "Current master PIN is wrong.",
                                     parent=dialog)
                return
            if len(new) < 4:
                messagebox.showerror("Error",
                                     "New PIN must be at least 4 digits.",
                                     parent=dialog)
                return
            if new != conf:
                messagebox.showerror("Error", "New PINs do not match.",
                                     parent=dialog)
                return
            set_setting(MASTER_PIN_HASH_KEY, hash_pin(new))
            messagebox.showinfo("Done", "Master PIN changed.", parent=dialog)
            dialog.destroy()
            self.master_pin_status_var.set("Set")

        tk.Button(f, text="Change PIN", font=("Segoe UI", 10, "bold"),
                  bg="#1565C0", fg="#FFFFFF", relief=tk.FLAT, cursor="hand2",
                  padx=15, pady=5, command=do_change).pack(pady=(12, 0))

    def _remove_master_pin(self):
        if not get_setting(MASTER_PIN_HASH_KEY):
            messagebox.showinfo("Info", "No master PIN is set.")
            return
        pin = tk.simpledialog.askstring(
            "Verify PIN",
            "Enter your login PIN to remove the master PIN:",
            show="*", parent=self)
        if not pin:
            return
        if hash_pin(pin) != self._get_user_pin_hash():
            messagebox.showerror("Incorrect PIN", "That PIN is wrong.")
            return
        if not messagebox.askyesno(
            "Confirm", "Remove the master PIN? The app will no longer "
            "lock on startup."
        ):
            return
        set_setting(MASTER_PIN_HASH_KEY, "")
        self.master_pin_status_var.set("Not set")
        messagebox.showinfo("Done", "Master PIN removed.")

    # ── Settings load / save ─────────────────────────────────────

    def _load_settings(self):
        self.app_name_var.set(get_setting("app_name") or "ORISUN IBUKUN")
        self.unit_name_var.set(get_setting("unit_name") or "Owode Unit")
        self.currency_var.set(get_setting("currency") or "₦")
        self.meeting_day_var.set(get_setting("meeting_day") or "Friday")
        self.entrance_fee_var.set(get_setting("entrance_fee") or "5000")
        self.min_savings_withdrawal_var.set(
            get_setting("min_savings_withdrawal") or "10000")
        self.max_loan_multiplier_var.set(
            get_setting("max_loan_multiplier") or "3")
        self.required_guarantors_var.set(
            get_setting("required_guarantors") or "2")
        self.interest_rate_var.set(get_setting("interest_rate") or "5")
        self.interest_method_var.set(get_setting("interest_method") or "Flat")
        self.late_payment_penalty_var.set(
            get_setting("late_payment_penalty") or "500")
        self.absent_fine_var.set(get_setting("absent_fine") or "0")

    def _save_coop_info(self):
        set_setting("app_name", self.app_name_var.get().strip())
        set_setting("unit_name", self.unit_name_var.get().strip())
        set_setting("currency", self.currency_var.get().strip())
        set_setting("meeting_day", self.meeting_day_var.get().strip())
        messagebox.showinfo("Saved", "Cooperative info saved successfully.")

    def _save_financial(self):
        set_setting("entrance_fee", self.entrance_fee_var.get().strip())
        set_setting("min_savings_withdrawal",
                     self.min_savings_withdrawal_var.get().strip())
        set_setting("max_loan_multiplier",
                     self.max_loan_multiplier_var.get().strip())
        set_setting("required_guarantors",
                     self.required_guarantors_var.get().strip())
        set_setting("interest_rate", self.interest_rate_var.get().strip())
        set_setting("interest_method", self.interest_method_var.get())
        set_setting("late_payment_penalty",
                     self.late_payment_penalty_var.get().strip())
        set_setting("absent_fine",
                     self.absent_fine_var.get().strip() or "0")
        messagebox.showinfo("Saved", "Financial settings saved successfully.")

    # ── Users ────────────────────────────────────────────────────

    def _load_users(self):
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        conn = get_connection()
        rows = conn.execute(
            """SELECT u.id, u.username, r.name as role_name,
                      u.is_active, u.last_login
               FROM users u JOIN roles r ON u.role_id = r.id
               ORDER BY u.username"""
        ).fetchall()
        for row in rows:
            active = "Yes" if row["is_active"] else "No"
            self.users_tree.insert("", tk.END, values=(
                row["id"], row["username"], row["role_name"],
                active, row["last_login"] or "Never",
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
                 bg="#FFFFFF", fg="#333333", anchor="w").pack(
            fill=tk.X, pady=(5, 2))
        username_entry = tk.Entry(fields_frame, font=("Segoe UI", 10),
                                  relief=tk.SOLID, bd=1)
        username_entry.pack(fill=tk.X, pady=(0, 5))

        tk.Label(fields_frame, text="PIN:", font=("Segoe UI", 10),
                 bg="#FFFFFF", fg="#333333", anchor="w").pack(
            fill=tk.X, pady=(5, 2))
        pin_entry = tk.Entry(fields_frame, font=("Segoe UI", 10),
                             relief=tk.SOLID, bd=1, show="*")
        pin_entry.pack(fill=tk.X, pady=(0, 5))

        tk.Label(fields_frame, text="Role:", font=("Segoe UI", 10),
                 bg="#FFFFFF", fg="#333333", anchor="w").pack(
            fill=tk.X, pady=(5, 2))

        conn = get_connection()
        roles = conn.execute(
            "SELECT id, name FROM roles ORDER BY name").fetchall()
        role_map = {r["name"]: r["id"] for r in roles}
        role_names = list(role_map.keys())

        role_var = tk.StringVar(value=role_names[0] if role_names else "")
        ttk.Combobox(fields_frame, textvariable=role_var,
                     values=role_names, state="readonly").pack(
            fill=tk.X, pady=(0, 5))

        def save_user():
            uname = username_entry.get().strip()
            pin = pin_entry.get().strip()
            role_name = role_var.get()
            if not uname or not pin:
                messagebox.showwarning(
                    "Missing Fields",
                    "Username and PIN are required.", parent=dialog)
                return
            if len(pin) < 4:
                messagebox.showwarning(
                    "Invalid PIN",
                    "PIN must be at least 4 digits.", parent=dialog)
                return
            pin_hashed = hash_pin(pin)
            role_id = role_map.get(role_name)
            try:
                conn2 = get_connection()
                conn2.execute(
                    "INSERT INTO users (username, pin_hash, role_id, "
                    "is_active) VALUES (?, ?, ?, 1)",
                    (uname, pin_hashed, role_id))
                conn2.commit()
                messagebox.showinfo(
                    "Success", f"User '{uname}' created.", parent=dialog)
                dialog.destroy()
                self._load_users()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dialog)

        tk.Button(fields_frame, text="Create User",
                  font=("Segoe UI", 10, "bold"),
                  bg="#1565C0", fg="#FFFFFF", relief=tk.FLAT,
                  cursor="hand2", padx=15, pady=5,
                  command=save_user).pack(pady=(15, 0))

    def _deactivate_user(self):
        selected = self.users_tree.selection()
        if not selected:
            messagebox.showwarning(
                "No Selection", "Select a user to deactivate.")
            return
        values = self.users_tree.item(selected[0], "values")
        user_db_id = values[0]
        username = values[1]

        if username == self.current_user.get("username"):
            messagebox.showwarning(
                "Cannot Deactivate",
                "You cannot deactivate your own account.")
            return
        if values[3] == "No":
            messagebox.showinfo(
                "Info", f"User '{username}' is already inactive.")
            return

        confirm = messagebox.askyesno(
            "Confirm", f"Deactivate user '{username}'?")
        if not confirm:
            return

        conn = get_connection()
        conn.execute("UPDATE users SET is_active = 0 WHERE id = ?",
                     (user_db_id,))
        conn.commit()
        messagebox.showinfo("Done", f"User '{username}' deactivated.")
        self._load_users()
