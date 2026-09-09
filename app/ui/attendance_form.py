import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from database.connection import get_connection
from engines.transaction_engine import (
    create_meeting, record_attendance, delete_meeting,
    reverse_absence_charges, _log_attendance,
    apply_absence_fines,
)
from database.schema import get_setting
from utils.validators import validate_amount


MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]


class AttendanceForm(tk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent, bg="#FFFFFF")
        self.current_user = current_user
        self.current_month = datetime.date.today().month
        self.current_year = datetime.date.today().year
        self.month_meetings = []
        self.current_meeting_id = None
        self.attendance_status = {}
        self.pack(fill="both", expand=True)
        self._build_ui()
        self._load_month()

    def _build_ui(self):
        header = tk.Frame(self, bg="#1565C0", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="MEETING ATTENDANCE", font=("Segoe UI", 18, "bold"),
                 fg="white", bg="#1565C0").pack(side="left", padx=20, pady=8)

        nav = tk.Frame(self, bg="#E3F2FD")
        nav.pack(fill="x", padx=15, pady=(10, 5))

        self.prev_btn = tk.Button(nav, text="<", font=("Segoe UI", 12, "bold"),
                                  bg="#1565C0", fg="white", relief="flat",
                                  padx=10, pady=2, command=lambda: self._step_month(-1))
        self.prev_btn.pack(side="left")

        self.month_label = tk.Label(nav, text="", font=("Segoe UI", 14, "bold"),
                                    fg="#1565C0", bg="#E3F2FD")
        self.month_label.pack(side="left", padx=12)

        self.next_btn = tk.Button(nav, text=">", font=("Segoe UI", 12, "bold"),
                                  bg="#1565C0", fg="white", relief="flat",
                                  padx=10, pady=2, command=lambda: self._step_month(1))
        self.next_btn.pack(side="left")

        tk.Button(nav, text="Today", font=("Segoe UI", 10), bg="#1565C0", fg="white",
                  relief="flat", padx=8, pady=2,
                  command=self._go_today).pack(side="left", padx=(15, 0))

        self.new_meeting_btn = tk.Button(nav, text="+ New Meeting", font=("Segoe UI", 10, "bold"),
                                          bg="#2E7D32", fg="white", relief="flat",
                                          padx=12, pady=3,
                                          command=self._start_new_meeting)
        self.new_meeting_btn.pack(side="right")

        self.delete_meeting_btn = tk.Button(nav, text="Delete Meeting", font=("Segoe UI", 10, "bold"),
                                            bg="#C62828", fg="white", relief="flat",
                                            padx=12, pady=3,
                                            command=self._delete_meeting)
        self.delete_meeting_btn.pack(side="right", padx=(0, 8))

        self.summary_label = tk.Label(nav, text="", font=("Segoe UI", 10),
                                      fg="#333333", bg="#E3F2FD")
        self.summary_label.pack(side="right", padx=(0, 15))

        tk.Frame(self, bg="#1565C0", height=1).pack(fill="x", padx=15)

        grid_frame = tk.Frame(self, bg="#FFFFFF")
        grid_frame.pack(fill="both", expand=True, padx=15, pady=(5, 0))

        self.tree = ttk.Treeview(grid_frame, show="headings", height=22)
        self.tree.pack(side="left", fill="both", expand=True)

        tree_scroll_y = ttk.Scrollbar(grid_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll_y.set)
        tree_scroll_y.pack(side="right", fill="y")

        tree_scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=tree_scroll_x.set)
        tree_scroll_x.pack(fill="x", padx=15)

        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.tree.bind("<Button-1>", self._on_cell_click)

        bottom = tk.Frame(self, bg="#E3F2FD")
        bottom.pack(fill="x", padx=15, pady=(5, 10))

        notes_row = tk.Frame(bottom, bg="#E3F2FD")
        notes_row.pack(fill="x", pady=(5, 0))
        tk.Label(notes_row, text="Meeting Notes:", font=("Segoe UI", 10, "bold"),
                 bg="#E3F2FD", fg="#1565C0").pack(side="left")
        self.notes_text = tk.Text(notes_row, height=2, font=("Segoe UI", 10), wrap="word",
                                  bg="white", relief="solid", bd=1, width=60)
        self.notes_text.pack(side="left", padx=(8, 0), fill="x", expand=True)

        levy_row = tk.Frame(bottom, bg="#E3F2FD")
        levy_row.pack(fill="x", pady=(5, 0))
        tk.Label(levy_row, text="Absence fine:", font=("Segoe UI", 10, "bold"),
                 bg="#E3F2FD", fg="#1565C0").pack(side="left")
        self.fine_var = tk.StringVar(value=get_setting("absent_fine", "0"))
        tk.Entry(levy_row, textvariable=self.fine_var, font=("Segoe UI", 10),
                 width=10, bg="white", relief="solid", bd=1).pack(side="left", padx=(4, 12))
        tk.Label(levy_row, text="Minutes levy:", font=("Segoe UI", 10, "bold"),
                 bg="#E3F2FD", fg="#1565C0").pack(side="left")
        self.levy_var = tk.StringVar(value="0")
        tk.Entry(levy_row, textvariable=self.levy_var, font=("Segoe UI", 10),
                 width=10, bg="white", relief="solid", bd=1).pack(side="left", padx=(4, 12))
        tk.Button(levy_row, text="Apply Levy", font=("Segoe UI", 9, "bold"),
                  bg="#E65100", fg="white", relief="flat", padx=8, pady=2,
                  command=self._apply_levy).pack(side="left", padx=(0, 12))
        tk.Button(levy_row, text="Save Attendance", font=("Segoe UI", 10, "bold"),
                  bg="#1565C0", fg="white", relief="flat", padx=14, pady=3,
                  command=self._save_attendance).pack(side="right")

    def _step_month(self, delta):
        self.current_month += delta
        if self.current_month > 12:
            self.current_month = 1
            self.current_year += 1
        elif self.current_month < 1:
            self.current_month = 12
            self.current_year -= 1
        self._load_month()

    def _go_today(self):
        today = datetime.date.today()
        self.current_month = today.month
        self.current_year = today.year
        self._load_month()

    def _load_month(self):
        self.month_label.config(text=f"{MONTH_NAMES[self.current_month - 1]} {self.current_year}")

        conn = get_connection()
        month_start = f"{self.current_year}-{self.current_month:02d}-01"
        if self.current_month == 12:
            month_end = f"{self.current_year + 1}-01-01"
        else:
            month_end = f"{self.current_year}-{self.current_month + 1:02d}-01"

        meeting_rows = conn.execute(
            "SELECT id, date, meeting_number, notes FROM meetings "
            "WHERE date >= ? AND date < ? ORDER BY date",
            (month_start, month_end),
        ).fetchall()

        self.month_meetings = []
        for r in meeting_rows:
            d = datetime.date.fromisoformat(r["date"])
            self.month_meetings.append({
                "id": r["id"],
                "date": r["date"],
                "label": d.strftime("%d %b"),
                "notes": r["notes"] or "",
            })

        if self.month_meetings:
            self.current_meeting_id = self.month_meetings[-1]["id"]
        else:
            self.current_meeting_id = None

        self._load_all_attendance()
        self._build_grid()
        self._load_notes_for_current()
        self._update_summary()

    def _load_all_attendance(self):
        self.attendance_status = {}
        conn = get_connection()
        members = conn.execute(
            "SELECT id, full_name FROM members WHERE status = 'Active' ORDER BY full_name"
        ).fetchall()
        for m in members:
            self.attendance_status[m["id"]] = {}

        for mtg in self.month_meetings:
            att_rows = conn.execute(
                "SELECT member_id, status FROM attendance WHERE meeting_id = ?",
                (mtg["id"],),
            ).fetchall()
            for ar in att_rows:
                mid = ar["member_id"]
                if mid in self.attendance_status:
                    self.attendance_status[mid][mtg["id"]] = ar["status"]

    def _build_grid(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        self.tree["columns"] = ()

        cols = ["member_name"]
        self._date_col_map = {}
        for mtg in self.month_meetings:
            col_id = f"date_{mtg['id']}"
            cols.append(col_id)
            self._date_col_map[col_id] = mtg

        self.tree["columns"] = tuple(cols)
        self.tree.column("member_name", width=200, minwidth=160)
        self.tree.heading("member_name", text="Member Name", anchor="w")

        for mtg in self.month_meetings:
            col_id = f"date_{mtg['id']}"
            self.tree.column(col_id, width=100, minwidth=80, anchor="center")
            is_current = mtg["id"] == self.current_meeting_id
            heading_text = mtg["label"] + (" *" if is_current else "")
            self.tree.heading(col_id, text=heading_text, anchor="center")

        conn = get_connection()
        members = conn.execute(
            "SELECT id, full_name FROM members WHERE status = 'Active' ORDER BY full_name"
        ).fetchall()

        for idx, m in enumerate(members):
            values = [m["full_name"]]
            tags = ()
            for mtg in self.month_meetings:
                status = self.attendance_status.get(m["id"], {}).get(mtg["id"], "")
                if status == "Present":
                    values.append("\u2713")
                elif status == "Absent":
                    values.append("\u2717")
                else:
                    values.append("")

            row_tags = ("current",) if True else ()
            iid = str(m["id"])
            self.tree.insert("", "end", iid=iid, values=values, tags=row_tags)

        self.tree.tag_configure("current", background="#FFFFFF")

        if self.current_meeting_id:
            col_id = f"date_{self.current_meeting_id}"
            self.tree.tag_configure("editable_col", background="#E3F2FD")

    def _on_cell_click(self, event):
        if self.current_meeting_id is None:
            return

        region = self.tree.identify("region", event.x, event.y)
        if region != "cell":
            return

        col_id = self.tree.identify_column(event.x)
        if not col_id:
            return

        col_index = int(col_id.replace("#", "")) - 1
        if col_index == 0:
            return

        cols = list(self.tree["columns"])
        if col_index >= len(cols):
            return
        clicked_col = cols[col_index]

        if clicked_col not in self._date_col_map:
            return

        mtg = self._date_col_map[clicked_col]

        row_id = self.tree.identify_row(event.y)
        if not row_id:
            return

        member_id = int(row_id)
        current = self.attendance_status.get(member_id, {}).get(mtg["id"], "")

        if current == "Present":
            new_status = "Absent"
        elif current == "Absent":
            new_status = ""
        else:
            new_status = "Present"

        if member_id not in self.attendance_status:
            self.attendance_status[member_id] = {}
        self.attendance_status[member_id][mtg["id"]] = new_status

        if new_status == "Present":
            display = "\u2713"
        elif new_status == "Absent":
            display = "\u2717"
        else:
            display = ""

        vals = list(self.tree.item(row_id, "values"))
        vals[col_index] = display
        self.tree.item(row_id, values=vals)
        self._update_summary(mtg["id"])

    def _load_notes_for_current(self):
        self.notes_text.delete("1.0", "end")
        if self.current_meeting_id:
            for mtg in self.month_meetings:
                if mtg["id"] == self.current_meeting_id:
                    if mtg["notes"]:
                        self.notes_text.insert("1.0", mtg["notes"])
                    break

    def _update_summary(self, meeting_id=None):
        mid = meeting_id or self.current_meeting_id
        if mid is None:
            self.summary_label.config(text="No meeting selected")
            return
        present = 0
        absent = 0
        for member_id, meetings in self.attendance_status.items():
            status = meetings.get(mid, "")
            if status == "Present":
                present += 1
            elif status == "Absent":
                absent += 1
        total = present + absent
        self.summary_label.config(
            text=f"Present: {present}  |  Absent: {absent}  |  Total Active: {total}")

    def _start_new_meeting(self):
        from utils.date_picker import pick_date
        date_var = tk.StringVar(value=datetime.date.today().isoformat())
        win = tk.Toplevel(self)
        win.title("New Meeting Date")
        win.geometry("300x120")
        win.configure(bg="#FFFFFF")
        win.transient(self)
        win.grab_set()

        tk.Label(win, text="Meeting Date:", font=("Segoe UI", 11, "bold"),
                 fg="#1565C0", bg="#FFFFFF").pack(anchor="w", padx=15, pady=(12, 5))
        entry_row = tk.Frame(win, bg="#FFFFFF")
        entry_row.pack(fill="x", padx=15)
        tk.Entry(entry_row, textvariable=date_var, font=("Segoe UI", 11),
                 width=15, relief="solid", bd=1).pack(side="left")
        tk.Button(entry_row, text="Cal", font=("Segoe UI", 9), bg="#E3F2FD", fg="#1565C0",
                  relief="flat", padx=4,
                  command=lambda: pick_date(win, date_var, "Select Meeting Date")).pack(side="left", padx=(6, 0))

        def create():
            date_str = date_var.get().strip()
            try:
                target = datetime.date.fromisoformat(date_str)
            except ValueError:
                messagebox.showerror("Invalid Date", "Use YYYY-MM-DD format.", parent=win)
                return

            if target.month != self.current_month or target.year != self.current_year:
                messagebox.showwarning("Wrong Month",
                                       f"Date must be in {MONTH_NAMES[self.current_month - 1]} {self.current_year}.",
                                       parent=win)
                return

            conn = get_connection()
            existing = conn.execute("SELECT id FROM meetings WHERE date = ?", (date_str,)).fetchone()
            if existing:
                self.current_meeting_id = existing["id"]
                win.destroy()
                self._load_month()
                return

            meeting_id = create_meeting(
                date=date_str, notes="",
                created_by=self.current_user.get("id"),
                allow_backdate=True,
            )
            self.current_meeting_id = meeting_id
            win.destroy()
            self._load_month()

        tk.Button(win, text="Create Meeting", font=("Segoe UI", 10, "bold"),
                  bg="#2E7D32", fg="white", relief="flat", padx=12, pady=4,
                  command=create).pack(pady=12)

    def _delete_meeting(self):
        if self.current_meeting_id is None:
            messagebox.showwarning("No Meeting", "No meeting selected.")
            return
        mtg_label = ""
        mtg_date = ""
        for mtg in self.month_meetings:
            if mtg["id"] == self.current_meeting_id:
                mtg_label = f"#{mtg['id']}"
                mtg_date = mtg["label"]
                break
        confirm = messagebox.askyesno(
            "Delete Meeting",
            f"Delete Meeting {mtg_label} ({mtg_date})?\n\n"
            "This will remove ALL attendance records and charges\n"
            "for this meeting. This cannot be undone.",
            parent=self,
        )
        if not confirm:
            return
        ok = delete_meeting(self.current_meeting_id,
                            entered_by=self.current_user.get("id"))
        if ok:
            messagebox.showinfo("Deleted", f"Meeting {mtg_label} ({mtg_date}) deleted.")
        else:
            messagebox.showerror("Error", "Meeting not found.")
        self._load_month()

    def _save_attendance(self):
        if not self.month_meetings:
            messagebox.showwarning("No Meetings", "No meetings exist for this month.")
            return

        notes = self.notes_text.get("1.0", "end").strip()
        conn = get_connection()
        if self.current_meeting_id:
            conn.execute("UPDATE meetings SET notes = ? WHERE id = ?",
                         (notes, self.current_meeting_id))
            conn.commit()

        updated = 0
        reversed_count = 0
        logged = 0
        uid = self.current_user.get("id")

        for mtg in self.month_meetings:
            mtg_id = mtg["id"]
            old_statuses = {}
            old_rows = conn.execute(
                "SELECT member_id, status FROM attendance WHERE meeting_id = ?",
                (mtg_id,),
            ).fetchall()
            for r in old_rows:
                old_statuses[r["member_id"]] = r["status"]

            for member_id, meetings in self.attendance_status.items():
                new_status = meetings.get(mtg_id, "")
                if new_status not in ("Present", "Absent"):
                    continue
                old_status = old_statuses.get(member_id, "")

                if old_status == new_status:
                    continue

                record_attendance(mtg_id, member_id, new_status, uid)
                updated += 1

                if old_status == "Absent" and new_status == "Present":
                    rev = reverse_absence_charges(member_id, mtg_id, conn=conn)
                    reversed_count += rev

                _log_attendance(conn, member_id, mtg_id,
                                old_status, new_status, uid)
                logged += 1

        conn.commit()

        fine_msg = ""
        try:
            fine = validate_amount(self.fine_var.get().strip() or "0")
            if fine > 0 and self.current_meeting_id:
                n = apply_absence_fines(self.current_meeting_id, fine,
                                        entered_by=uid)
                if n:
                    fine_msg = f"\nAbsence fine charged to {n} absent member(s)."
        except ValueError as e:
            fine_msg = f"\nAbsence fine not applied: {e}"

        parts = []
        if updated:
            parts.append(f"{updated} record(s) updated")
        if reversed_count:
            parts.append(f"{reversed_count} absence charge(s) reversed")
        if not parts:
            parts.append("No changes")
        summary = ", ".join(parts) + fine_msg
        messagebox.showinfo("Saved", f"Attendance saved.\n{summary}")
        self._load_month()

    def _apply_levy(self):
        if self.current_meeting_id is None:
            messagebox.showwarning("No Meeting", "No meeting selected for this month.")
            return
        from engines.transaction_engine import apply_minutes_levy
        from utils.validators import validate_amount
        try:
            amount = validate_amount(self.levy_var.get().strip() or "0")
        except ValueError as e:
            messagebox.showerror("Invalid Amount", str(e))
            return
        if amount <= 0:
            messagebox.showwarning("Invalid Amount", "Enter a minutes levy greater than zero.")
            return
        confirm = messagebox.askyesno(
            "Confirm Minutes Levy",
            f"Apply minutes levy of {amount:,.0f} to ALL absent members of meeting #{self.current_meeting_id}?",
            parent=self)
        if not confirm:
            return
        n = apply_minutes_levy(self.current_meeting_id, amount,
                               entered_by=self.current_user.get("id"))
        if n:
            messagebox.showinfo("Levy Applied", f"Minutes levy charged to {n} absent member(s).")
        else:
            messagebox.showinfo("Levy Applied", "No new charges (levy may already have been applied).")
