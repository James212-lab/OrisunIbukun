"""Main application window — navigation shell."""
import tkinter as tk
from tkinter import ttk, messagebox
from database.connection import get_connection, close_connection
from database.schema import get_setting
from utils.helpers import format_currency, set_window_icon
from session import SessionMixin
import datetime
import traceback


class MainForm(SessionMixin, tk.Tk):
    def __init__(self, user_id: int, username: str, role_name: str):
        super().__init__()
        self.user_id = user_id
        self.username = username
        self.role_name = role_name
        self.current_user = {"id": user_id, "username": username, "role": role_name}

        self.title("ORISUN IBUKUN – Owode Unit")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(bg="#E3F2FD")
        set_window_icon(self)

        self._apply_theme()
        self._build_ui()
        self._setup_keyboard_shortcuts()
        self._log_login()
        # SessionMixin already starts session with 20/5 min in its __init__

    def _apply_theme(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Blue.TFrame", background="#E3F2FD")
        style.configure("White.TFrame", background="#FFFFFF")
        style.configure("Header.TLabel", background="#1565C0", foreground="#FFFFFF",
                         font=("Segoe UI", 18, "bold"))
        style.configure("Title.TLabel", background="#E3F2FD", foreground="#1565C0",
                         font=("Segoe UI", 14, "bold"))
        style.configure("Info.TLabel", background="#E3F2FD", foreground="#333333",
                         font=("Segoe UI", 11))
        style.configure("Nav.TButton", font=("Segoe UI", 13, "bold"), padding=15)
        style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"), padding=10)
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        header = tk.Frame(self, bg="#1565C0", height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(header, text="ORISUN IBUKUN", bg="#1565C0", fg="#FFFFFF",
                 font=("Segoe UI", 20, "bold")).pack(side=tk.LEFT, padx=20)
        tk.Label(header, text="Owode Unit", bg="#1565C0", fg="#BBDEFB",
                 font=("Segoe UI", 14)).pack(side=tk.LEFT, padx=5)

        user_frame = tk.Frame(header, bg="#1565C0")
        user_frame.pack(side=tk.RIGHT, padx=20)
        tk.Label(user_frame, text=f"Logged in: {self.username} ({self.role_name})",
                 bg="#1565C0", fg="#FFFFFF", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 12))
        tk.Button(user_frame, text="Logout  (Ctrl+Q)", font=("Segoe UI", 10, "bold"),
                  bg="#FFFFFF", fg="#1565C0", relief=tk.FLAT, cursor="hand2",
                  padx=12, pady=4, command=self.logout).pack(side=tk.LEFT)

        content = tk.Frame(self, bg="#E3F2FD")
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        nav = tk.Frame(content, bg="#E3F2FD", width=220)
        nav.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        nav.pack_propagate(False)

        buttons = [
            ("DASHBOARD", self._show_dashboard),
            ("MEMBERS", self._open_members),
            ("ATTENDANCE", self._open_attendance),
            ("PAYMENTS", self._open_payments),
            ("LOANS", self._open_loans),
            ("REPORTS", self._open_reports),
            ("BACKUP", self._open_backup),
            ("SETTINGS", self._open_settings),
        ]

        for text, cmd in buttons:
            btn = tk.Button(nav, text=text, command=cmd, bg="#1565C0", fg="#FFFFFF",
                           font=("Segoe UI", 12, "bold"), relief=tk.FLAT, padx=10, pady=12,
                           activebackground="#0D47A1", activeforeground="#FFFFFF",
                           cursor="hand2", width=20)
            btn.pack(fill=tk.X, pady=3)

        self.main_area = tk.Frame(content, bg="#FFFFFF", relief=tk.RAISED, bd=1)
        self.main_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._show_dashboard()

    def _show_dashboard(self):
        for w in self.main_area.winfo_children():
            w.destroy()

        tk.Label(self.main_area, text="DASHBOARD", bg="#1565C0", fg="#FFFFFF",
                 font=("Segoe UI", 16, "bold"), pady=10).pack(fill=tk.X)

        try:
            today = datetime.date.today()
            year, month = today.year, today.month
            month_name = today.strftime("%B %Y")
            month_str = f"{year}-{month:02d}"

            conn = get_connection()
            cur = conn.execute("SELECT COUNT(*) as cnt FROM members WHERE status = 'Active'")
            total_members = cur.fetchone()["cnt"]

            cur = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) as t FROM savings WHERE type = 'Savings'")
            total_savings = cur.fetchone()["t"]
            cur = conn.execute(
                "SELECT COALESCE(SUM(share_value), 0) as t FROM members WHERE status = 'Active'")
            total_shares = cur.fetchone()["t"]

            last_meeting = conn.execute(
                "SELECT id, meeting_number, date FROM meetings ORDER BY date DESC, id DESC LIMIT 1"
            ).fetchone()
            if last_meeting:
                present = conn.execute(
                    "SELECT COUNT(*) as cnt FROM attendance WHERE meeting_id = ? AND status = 'Present'",
                    (last_meeting["id"],)).fetchone()["cnt"]
                absent = conn.execute(
                    "SELECT COUNT(*) as cnt FROM attendance WHERE meeting_id = ? AND status = 'Absent'",
                    (last_meeting["id"],)).fetchone()["cnt"]
                meeting_label = f"Meeting #{last_meeting['meeting_number']} ({last_meeting['date']})"
            else:
                present, absent, meeting_label = 0, 0, "No meetings yet"

            from engines.transaction_engine import get_monthly_summary
            summary = get_monthly_summary(year, month)

            cur = conn.execute(
                """SELECT COALESCE(SUM(amount), 0) as t FROM transactions
                   WHERE transaction_type = 'Loan Repayment'
                   AND strftime('%Y-%m', date) = ? AND status = 'Posted'""",
                (month_str,))
            repaid_month = cur.fetchone()["t"]

            cur = conn.execute(
                """SELECT COALESCE(SUM(outstanding_principal), 0) as p,
                          COALESCE(SUM(outstanding_interest), 0) as i FROM loans
                   WHERE status IN ('Disbursed', 'Active', 'Overdue')""")
            loan_row = cur.fetchone()
            outstanding = (loan_row["p"] or 0) + (loan_row["i"] or 0)

            try:
                cur = conn.execute(
                    """SELECT COALESCE(SUM(amount - amount_paid), 0) as t
                       FROM member_charges WHERE status != 'Paid'""")
                charges_owed = cur.fetchone()["t"]
            except Exception:
                charges_owed = 0
        except Exception as e:
            tk.Label(self.main_area, text=f"Could not load dashboard:\n{e}",
                     bg="#FFFFFF", fg="red", font=("Segoe UI", 11)).pack(pady=20)
            return

        stats = tk.Frame(self.main_area, bg="#FFFFFF", padx=20, pady=15)
        stats.pack(fill=tk.BOTH, expand=True)

        tk.Label(stats, text=f"THIS MONTH — {month_name}", bg="#FFFFFF",
                 fg="#1565C0", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W, pady=(0, 2))
        tk.Label(stats, text=f"Last meeting: {meeting_label}  •  Present: {present}  •  Absent: {absent}",
                 bg="#FFFFFF", fg="#666666", font=("Segoe UI", 11)).pack(anchor=tk.W, pady=(0, 10))

        grid = tk.Frame(stats, bg="#FFFFFF")
        grid.pack(fill=tk.BOTH, expand=True)

        items = [
            ("Active Members", str(total_members)),
            ("Total Savings", format_currency(total_savings)),
            ("Total Shares Value", format_currency(total_shares)),
            ("Money In (Month)", format_currency(summary["money_in"])),
            ("Loans Disbursed (Month)", format_currency(summary["loans_disbursed"])),
            ("Repaid This Month", format_currency(repaid_month)),
            ("Outstanding Loans", format_currency(outstanding)),
            ("Charges Owed (Fines/Minutes)", format_currency(charges_owed)),
            ("Remitted to HQ (Month)", format_currency(summary["remittance"])),
            ("Net Cash Movement (Month)", format_currency(summary["net"])),
        ]

        for i, (label, value) in enumerate(items):
            r, c = divmod(i, 4)
            card = tk.Frame(grid, bg="#E3F2FD", padx=12, pady=10, relief=tk.RAISED, bd=1)
            card.grid(row=r, column=c, padx=5, pady=5, sticky=tk.NSEW)
            grid.columnconfigure(c, weight=1)
            tk.Label(card, text=label, bg="#E3F2FD", fg="#666666",
                     font=("Segoe UI", 10)).pack(anchor=tk.W)
            tk.Label(card, text=value, bg="#E3F2FD", fg="#1565C0",
                     font=("Segoe UI", 16, "bold")).pack(anchor=tk.W)

    def _open_module(self, module_name):
        for w in self.main_area.winfo_children():
            w.destroy()
        try:
            if module_name == "members":
                from ui.member_form import MemberForm
                MemberForm(self.main_area, self.current_user)
            elif module_name == "attendance":
                from ui.attendance_form import AttendanceForm
                AttendanceForm(self.main_area, self.current_user)
            elif module_name == "savings":
                from ui.savings_form import SavingsForm
                SavingsForm(self.main_area, self.current_user)
            elif module_name == "loans":
                from ui.loan_form import LoanForm
                LoanForm(self.main_area, self.current_user)
            elif module_name == "reports":
                from ui.report_form import ReportForm
                ReportForm(self.main_area, self.current_user)
            elif module_name == "backup":
                from ui.backup_form import BackupForm
                BackupForm(self.main_area, self.current_user)
            elif module_name == "settings":
                from ui.settings_form import SettingsForm
                SettingsForm(self.main_area, self.current_user)
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to open module:\n{e}", parent=self)

    def _open_members(self):
        self._open_module("members")

    def _open_attendance(self):
        self._open_module("attendance")

    def _open_payments(self):
        self._open_module("savings")

    def _open_loans(self):
        self._open_module("loans")

    def _open_reports(self):
        self._open_module("reports")

    def _open_backup(self):
        self._open_module("backup")

    def _open_settings(self):
        self._open_module("settings")

    def _setup_keyboard_shortcuts(self) -> None:
        """Setup keyboard shortcuts for the main application."""
        shortcuts = {
            "<Control-m>": self._open_members,
            "<Control-a>": self._open_attendance,
            "<Control-s>": self._open_payments,
            "<Control-l>": self._open_loans,
            "<Control-r>": self._open_reports,
            "<Control-b>": self._open_backup,
            "<Control-p>": self._open_settings,
            "<Control-q>": self.logout,
            "<F1>": lambda: messagebox.showinfo(
                "Keyboard Shortcuts",
                "Ctrl+M: Members\n"
                "Ctrl+A: Attendance\n"
                "Ctrl+S: Payments\n"
                "Ctrl+L: Loans\n"
                "Ctrl+R: Reports\n"
                "Ctrl+B: Backup\n"
                "Ctrl+P: Settings\n"
                "Ctrl+Q: Logout\n"
                "F1: Show this help"
            ),
            "<Escape>": lambda: self.focus_set(),
        }
        for key, cmd in shortcuts.items():
            self.bind_all(key, lambda e, c=cmd: self._handle_shortcut(e, c))

    def _handle_shortcut(self, event, cmd):
        """Handle keyboard shortcut - ignore if focus is in an input widget."""
        widget = event.widget
        # Don't trigger shortcuts when typing in input fields
        if isinstance(widget, (tk.Entry, tk.Text, ttk.Combobox, tk.Spinbox)):
            return
        # Also check if any ancestor is an input widget
        parent = widget.master
        while parent:
            if isinstance(parent, (tk.Entry, tk.Text, ttk.Combobox, tk.Spinbox)):
                return
            parent = parent.master
        cmd()

    def _log_login(self):
        conn = get_connection()
        conn.execute(
            "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
            (self.user_id, "Login", f"User {self.username} logged in"),
        )
        conn.execute(
            "UPDATE users SET last_login = datetime('now') WHERE id = ?",
            (self.user_id,),
        )
        conn.commit()

    def logout(self) -> None:
        """Log out the current user."""
        try:
            conn = get_connection()
            conn.execute(
                "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
                (self.user_id, "Logout", f"User {self.username} logged out"),
            )
            conn.commit()
        except Exception:
            pass
        finally:
            # Clean up session timer before destroying
            try:
                if hasattr(self, '_cleanup_session'):
                    self._cleanup_session()
            except Exception:
                pass
            try:
                close_connection()
            except Exception:
                pass
            self.destroy()
        # Restart login
        from ui.login_form import LoginForm

        def on_login_success(user_id, username, role_name):
            from ui.main_form import MainForm
            app = MainForm(user_id, username, role_name)
            app.mainloop()

        login = LoginForm(on_success=on_login_success)
        login.mainloop()
