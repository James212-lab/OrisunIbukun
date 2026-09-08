"""Shared calendar date-picker used by every date input app-wide."""
import datetime
import tkinter as tk
from tkinter import messagebox


def pick_date(parent, var: tk.StringVar, title: str = "Select Date") -> None:
    """Open a calendar popup and write the chosen YYYY-MM-DD date into var.

    Falls back to a manual-entry hint when tkcalendar is unavailable.
    Works with any tk.StringVar bound to a date Entry, so every date
    input across the app gets the same accurate picker.
    """
    try:
        from tkcalendar import Calendar
    except ImportError:
        messagebox.showinfo(
            "Calendar Unavailable",
            "Type the date as YYYY-MM-DD.\nInstall the 'tkcalendar' package for a picker.")
        return
    try:
        dlg = tk.Toplevel(parent)
    except Exception:
        return
    dlg.title(title)
    dlg.resizable(False, False)
    try:
        dlg.transient(parent)
        dlg.grab_set()
    except Exception:
        pass
    try:
        initial = datetime.date.fromisoformat((var.get() or "").strip())
    except (ValueError, AttributeError):
        initial = datetime.date.today()
    cal = Calendar(dlg, selectmode="day", year=initial.year,
                   month=initial.month, day=initial.day,
                   date_pattern="yyyy-mm-dd")
    cal.pack(padx=15, pady=15)

    def choose():
        try:
            var.set(cal.get_date())
        finally:
            try:
                dlg.destroy()
            except Exception:
                pass

    tk.Button(dlg, text="Use This Date", font=("Segoe UI", 11, "bold"),
              bg="#1565C0", fg="white", command=choose).pack(pady=(0, 12))
