import tkinter as tk
from tkinter import messagebox
from database.connection import get_connection
from database.schema import get_and_clear_initial_admin_pin, get_setting, set_setting
from utils.helpers import hash_pin, set_window_icon


BLUE = "#1565C0"
WHITE = "#FFFFFF"
LIGHT_BLUE = "#E3F2FD"
TITLE_FONT = ("Segoe UI", 16, "bold")
SUBTITLE_FONT = ("Segoe UI", 11)
LABEL_FONT = ("Segoe UI", 14)
ENTRY_FONT = ("Segoe UI", 14)
BUTTON_FONT = ("Segoe UI", 14, "bold")

MASTER_PIN_HASH_KEY = "master_pin_hash"


def _has_master_pin() -> bool:
    return bool(get_setting(MASTER_PIN_HASH_KEY))


class LoginForm(tk.Tk):
    def __init__(self, on_success=None):
        super().__init__()
        self.on_success = on_success
        self.user_id = None
        self.username = None
        self.role = None

        self.title("ORISUN IBUKUN – Owode Unit")
        self.configure(bg=LIGHT_BLUE)
        self.resizable(False, False)
        set_window_icon(self)

        width = 400
        height = 380
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        self._build_login_ui()
        self._show_initial_pin()
        self._check_master_lock()

    def _show_initial_pin(self) -> None:
        try:
            pin = get_and_clear_initial_admin_pin()
            if pin:
                messagebox.showinfo(
                    "First-Time Setup",
                    f"Initial admin account created.\n\nUsername:  admin\nPIN:  {pin}\n\n"
                    "Please note this PIN and change it in Settings after logging in.",
                )
        except Exception:
            pass

    # ── Master Lock ──────────────────────────────────────────────

    def _check_master_lock(self) -> None:
        if not _has_master_pin():
            self._show_set_master_pin()
        else:
            self._show_lock_overlay()

    def _show_lock_overlay(self) -> None:
        self.lock_frame = tk.Frame(self, bg=BLUE)
        self.lock_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        inner = tk.Frame(self.lock_frame, bg=WHITE, padx=30, pady=20)
        inner.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(
            inner, text="APP LOCKED",
            font=("Segoe UI", 18, "bold"), fg="#D32F2F", bg=WHITE
        ).pack(pady=(0, 2))

        tk.Label(
            inner, text="Enter the master PIN to unlock",
            font=SUBTITLE_FONT, fg="#555555", bg=WHITE
        ).pack(pady=(0, 15))

        tk.Label(
            inner, text="Master PIN", font=LABEL_FONT, fg=BLUE, bg=WHITE, anchor="w"
        ).pack(fill="x")
        self.lock_pin_entry = tk.Entry(
            inner, font=ENTRY_FONT, show="*", bg="#F5F5F5", relief="flat"
        )
        self.lock_pin_entry.pack(fill="x", pady=(2, 10), ipady=4)
        self.lock_pin_entry.focus_set()
        self.lock_pin_entry.bind("<Return>", lambda e: self._try_unlock())

        self.lock_error = tk.Label(
            inner, text="", font=("Segoe UI", 11), fg="red", bg=WHITE
        )
        self.lock_error.pack()

        tk.Button(
            inner, text="Unlock", font=BUTTON_FONT, fg=WHITE, bg="#D32F2F",
            activebackground="#B71C1C", activeforeground=WHITE,
            relief="flat", cursor="hand2", command=self._try_unlock
        ).pack(fill="x", pady=(5, 0), ipady=6)

    def _try_unlock(self) -> None:
        pin = self.lock_pin_entry.get().strip()
        if not pin:
            self.lock_error.config(text="Enter the master PIN")
            return
        stored_hash = get_setting(MASTER_PIN_HASH_KEY)
        if hash_pin(pin) == stored_hash:
            self.lock_frame.destroy()
        else:
            self.lock_error.config(text="Incorrect master PIN")
            self.lock_pin_entry.delete(0, "end")

    def _show_set_master_pin(self) -> None:
        self.lock_frame = tk.Frame(self, bg=BLUE)
        self.lock_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        inner = tk.Frame(self.lock_frame, bg=WHITE, padx=30, pady=20)
        inner.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(
            inner, text="SET MASTER PIN",
            font=("Segoe UI", 18, "bold"), fg=BLUE, bg=WHITE
        ).pack(pady=(0, 2))

        tk.Label(
            inner, text="Create a master PIN to lock the app on startup",
            font=SUBTITLE_FONT, fg="#555555", bg=WHITE
        ).pack(pady=(0, 15))

        tk.Label(
            inner, text="New Master PIN", font=LABEL_FONT, fg=BLUE, bg=WHITE, anchor="w"
        ).pack(fill="x")
        self.set_pin_entry = tk.Entry(
            inner, font=ENTRY_FONT, show="*", bg="#F5F5F5", relief="flat"
        )
        self.set_pin_entry.pack(fill="x", pady=(2, 10), ipady=4)
        self.set_pin_entry.focus_set()

        tk.Label(
            inner, text="Confirm PIN", font=LABEL_FONT, fg=BLUE, bg=WHITE, anchor="w"
        ).pack(fill="x")
        self.set_pin_confirm = tk.Entry(
            inner, font=ENTRY_FONT, show="*", bg="#F5F5F5", relief="flat"
        )
        self.set_pin_confirm.pack(fill="x", pady=(2, 10), ipady=4)
        self.set_pin_confirm.bind("<Return>", lambda e: self._set_master_pin())

        self.set_pin_error = tk.Label(
            inner, text="", font=("Segoe UI", 11), fg="red", bg=WHITE
        )
        self.set_pin_error.pack()

        tk.Button(
            inner, text="Set Master PIN", font=BUTTON_FONT, fg=WHITE, bg="#1565C0",
            activebackground="#0D47A1", activeforeground=WHITE,
            relief="flat", cursor="hand2", command=self._set_master_pin
        ).pack(fill="x", pady=(5, 0), ipady=6)

    def _set_master_pin(self) -> None:
        pin = self.set_pin_entry.get().strip()
        confirm = self.set_pin_confirm.get().strip()
        if not pin or not confirm:
            self.set_pin_error.config(text="Enter and confirm the PIN")
            return
        if len(pin) < 4:
            self.set_pin_error.config(text="PIN must be at least 4 digits")
            return
        if pin != confirm:
            self.set_pin_error.config(text="PINs do not match")
            return
        set_setting(MASTER_PIN_HASH_KEY, hash_pin(pin))
        self.lock_frame.destroy()

    # ── Login UI ─────────────────────────────────────────────────

    def _build_login_ui(self):
        frame = tk.Frame(self, bg=WHITE, padx=30, pady=20)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(
            frame, text="ORISUN IBUKUN – Owode Unit",
            font=TITLE_FONT, fg=BLUE, bg=WHITE
        ).pack(pady=(0, 2))

        tk.Label(
            frame, text="Offline Cooperative Management System",
            font=SUBTITLE_FONT, fg="#555555", bg=WHITE
        ).pack(pady=(0, 15))

        tk.Label(
            frame, text="Username", font=LABEL_FONT, fg=BLUE, bg=WHITE, anchor="w"
        ).pack(fill="x")
        self.username_entry = tk.Entry(
            frame, font=ENTRY_FONT, bg="#F5F5F5", relief="flat"
        )
        self.username_entry.pack(fill="x", pady=(2, 10), ipady=4)
        self.username_entry.focus_set()

        tk.Label(
            frame, text="PIN", font=LABEL_FONT, fg=BLUE, bg=WHITE, anchor="w"
        ).pack(fill="x")
        self.pin_entry = tk.Entry(
            frame, font=ENTRY_FONT, show="*", bg="#F5F5F5", relief="flat"
        )
        self.pin_entry.pack(fill="x", pady=(2, 15), ipady=4)
        self.pin_entry.bind("<Return>", lambda e: self._login())

        self.error_label = tk.Label(
            frame, text="", font=("Segoe UI", 11), fg="red", bg=WHITE
        )
        self.error_label.pack()

        tk.Button(
            frame, text="Login", font=BUTTON_FONT, fg=WHITE, bg=BLUE,
            activebackground="#0D47A1", activeforeground=WHITE,
            relief="flat", cursor="hand2", command=self._login
        ).pack(fill="x", pady=(5, 0), ipady=6)

    def _login(self):
        username = self.username_entry.get().strip()
        pin = self.pin_entry.get().strip()

        if not username or not pin:
            self.error_label.config(text="Please enter both username and PIN")
            return

        hashed = hash_pin(pin)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT u.id, u.username, r.name as role_name
               FROM users u JOIN roles r ON u.role_id = r.id
               WHERE u.username = ? AND u.pin_hash = ? AND u.is_active = 1""",
            (username, hashed),
        )
        row = cursor.fetchone()

        if row is None:
            self.error_label.config(text="Invalid username or PIN")
            return

        self.user_id = row["id"]
        self.username = row["username"]
        self.role = row["role_name"]
        user_id, username, role = self.user_id, self.username, self.role
        self.destroy()
        self.on_success(user_id, username, role)
