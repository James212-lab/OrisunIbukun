import tkinter as tk
from tkinter import ttk, messagebox
import datetime
import os

from engines.backup_engine import create_backup, list_backups, restore_backup
from database.connection import get_connection


class BackupForm(tk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, bg="#FFFFFF")
        self.current_user = current_user
        self.pack(fill="both", expand=True)
        self._build_ui()
        self._load_backups()

    def _build_ui(self):
        header = tk.Frame(self, bg="#1565C0", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="Backup & Restore", font=("Segoe UI", 18, "bold"),
                 bg="#1565C0", fg="#FFFFFF").pack(pady=15, padx=20, anchor="w")

        status_frame = tk.Frame(self, bg="#E3F2FD", padx=20, pady=12)
        status_frame.pack(fill=tk.X, padx=20, pady=(20, 5))
        tk.Label(status_frame, text="Last Backup:", font=("Segoe UI", 11, "bold"),
                 bg="#E3F2FD", fg="#333333").pack(side=tk.LEFT)
        self.last_backup_label = tk.Label(status_frame, text="Never", font=("Segoe UI", 11),
                                          bg="#E3F2FD", fg="#666666")
        self.last_backup_label.pack(side=tk.LEFT, padx=(8, 0))

        btn_frame = tk.Frame(self, bg="#FFFFFF")
        btn_frame.pack(fill=tk.X, padx=20, pady=(10, 5))
        self.backup_btn = tk.Button(btn_frame, text="BACK UP NOW", font=("Segoe UI", 13, "bold"),
                                    bg="#1565C0", fg="#FFFFFF", activebackground="#0D47A1",
                                    relief=tk.FLAT, cursor="hand2", padx=30, pady=12,
                                    command=self._do_backup)
        self.backup_btn.pack(side=tk.LEFT)

        tk.Label(self, text="Available Backups", font=("Segoe UI", 11, "bold"),
                 bg="#FFFFFF", fg="#333333", anchor="w").pack(fill=tk.X, padx=20, pady=(15, 5))

        restore_frame = tk.Frame(self, bg="#FFFFFF")
        restore_frame.pack(fill=tk.X, padx=20, pady=(0, 10), side="bottom")
        tk.Button(restore_frame, text="RESTORE", font=("Segoe UI", 12, "bold"),
                  bg="#E3F2FD", fg="#1565C0", relief=tk.FLAT, cursor="hand2",
                  padx=25, pady=10, command=self._do_restore).pack(side=tk.LEFT)

        columns = ("id", "date", "type", "size", "notes")
        tree_frame = tk.Frame(self, bg="#FFFFFF")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))

        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("type", text="Type")
        self.tree.heading("size", text="Size")
        self.tree.heading("notes", text="Notes")
        self.tree.column("id", width=0, stretch=False)
        self.tree.column("date", width=160)
        self.tree.column("type", width=100)
        self.tree.column("size", width=90)
        self.tree.column("notes", width=200)

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _load_backups(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        conn = get_connection()
        rows = conn.execute(
            "SELECT id, created_at, backup_type, file_size, notes FROM backups ORDER BY created_at DESC LIMIT 20"
        ).fetchall()

        last_date = None
        for row in rows:
            size = f"{row['file_size'] / 1024:.0f} KB" if row["file_size"] else "N/A"
            self.tree.insert("", tk.END, values=(
                row["id"], row["created_at"] or "", row["backup_type"] or "Manual",
                size, row["notes"] or "",
            ))
            if row["created_at"]:
                last_date = row["created_at"]

        self.last_backup_label.config(text=last_date if last_date else "Never")

    def _do_backup(self):
        self.backup_btn.config(state=tk.DISABLED, text="Backing up...")
        self.update_idletasks()
        try:
            create_backup(notes="Manual backup", created_by=self.current_user.get("id"))
            messagebox.showinfo("Backup Complete", "Backup created successfully.")
            self._load_backups()
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))
        finally:
            self.backup_btn.config(state=tk.NORMAL, text="BACK UP NOW")

    def _do_restore(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Select a backup to restore.")
            return

        values = self.tree.item(selected[0], "values")
        backup_id = values[0]
        date_str = values[1]

        conn = get_connection()
        row = conn.execute("SELECT backup_path FROM backups WHERE id = ?", (backup_id,)).fetchone()
        if not row or not row["backup_path"]:
            messagebox.showerror("Error", "Backup file path not found.")
            return

        backup_path = row["backup_path"]
        if not os.path.exists(backup_path):
            messagebox.showerror("Error", f"Backup file not found:\n{backup_path}")
            return

        confirm = messagebox.askyesno(
            "Confirm Restore",
            f"Restoring backup from {date_str}.\n\n"
            "A safety backup will be created first.\n"
            "All current data will be replaced.\n\nContinue?"
        )
        if not confirm:
            return

        try:
            restore_backup(backup_path)
            messagebox.showinfo("Restore Complete", "Backup restored successfully.\nPlease restart the application.")
        except Exception as e:
            messagebox.showerror("Restore Failed", str(e))
