using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;
using OrisunIbukun.Database;
using OrisunIbukun.Engine;
using OrisunIbukun.Utils;

namespace OrisunIbukun.Forms
{
    public class AttendanceForm : UserControl
    {
        private static readonly Color Blue = Color.FromArgb(21, 101, 192);
        private static readonly Color LightBlue = Color.FromArgb(227, 242, 253);
        private static readonly Color White = Color.White;
        private static readonly Color Green = Color.FromArgb(76, 175, 80);
        private static readonly Color Red = Color.FromArgb(244, 67, 54);

        private readonly string _userId;
        private TextBox txtDate = null!;
        private Label lblMeetingNum = null!;
        private Label lblSummary = null!;
        private Panel pnlMembers = null!;
        private TextBox txtNotes = null!;
        private TextBox txtFine = null!;
        private TextBox txtLevy = null!;
        private Label lblMsg = null!;
        private string _currentMeetingId = "";
        private readonly Dictionary<string, string> _memberStatus = new();
        private readonly Dictionary<string, Button> _btnYes = new();
        private readonly Dictionary<string, Button> _btnNo = new();
        private readonly Dictionary<string, Panel> _memberRows = new();

        public AttendanceForm(string userId)
        {
            _userId = userId;
            BackColor = LightBlue;
            InitializeForm();
            LoadForDate(Helpers.TodayStr());
        }

        private void InitializeForm()
        {
            var pnlHeader = new Panel
            {
                Dock = DockStyle.Top,
                Height = 60,
                BackColor = Blue
            };
            pnlHeader.Controls.Add(new Label
            {
                Text = "FRIDAY ATTENDANCE",
                Font = new Font("Segoe UI", 20, FontStyle.Bold),
                ForeColor = White,
                AutoSize = true,
                Top = 12,
                Left = 20
            });
            Controls.Add(pnlHeader);

            var pnlControls = new Panel
            {
                Dock = DockStyle.Top,
                Height = 52,
                BackColor = LightBlue,
                Padding = new Padding(15, 10, 15, 10)
            };

            lblMeetingNum = new Label
            {
                Text = "Meeting #: -",
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(15, 14)
            };
            pnlControls.Controls.Add(lblMeetingNum);

            pnlControls.Controls.Add(new Label
            {
                Text = "Date:",
                Font = new Font("Segoe UI", 11),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(170, 14)
            });

            txtDate = new TextBox
            {
                Font = new Font("Segoe UI", 11),
                Width = 120,
                Location = new Point(220, 11),
                Text = Helpers.TodayStr()
            };
            pnlControls.Controls.Add(txtDate);

            var btnToday = CreateSmallButton("Today", 348, 10, 70);
            btnToday.Click += (s, e) => { txtDate.Text = Helpers.TodayStr(); LoadForDate(txtDate.Text.Trim()); };
            pnlControls.Controls.Add(btnToday);

            var btnLoad = CreateSmallButton("Load", 424, 10, 70);
            btnLoad.Click += (s, e) => LoadForDate(txtDate.Text.Trim());
            pnlControls.Controls.Add(btnLoad);

            var btnStart = CreateSmallButton("Start New Meeting", 504, 10, 150);
            btnStart.BackColor = Blue;
            btnStart.ForeColor = White;
            btnStart.Click += BtnStart_Click;
            pnlControls.Controls.Add(btnStart);
            Controls.Add(pnlControls);

            var divider = new Panel
            {
                Dock = DockStyle.Top,
                Height = 2,
                BackColor = Blue
            };
            Controls.Add(divider);

            var pnlMembersHeader = new Panel
            {
                Dock = DockStyle.Top,
                Height = 36,
                BackColor = White,
                Padding = new Padding(15, 6, 15, 6)
            };
            pnlMembersHeader.Controls.Add(new Label
            {
                Text = "MEMBERS",
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(15, 6)
            });
            lblSummary = new Label
            {
                Text = "Present: 0 | Absent: 0 | Total: 0",
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.Gray,
                AutoSize = true,
                Location = new Point(200, 8)
            };
            pnlMembersHeader.Controls.Add(lblSummary);
            Controls.Add(pnlMembersHeader);

            pnlMembers = new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = White,
                AutoScroll = true,
                BorderStyle = BorderStyle.FixedSingle
            };
            Controls.Add(pnlMembers);

            var pnlBottom = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 190,
                BackColor = LightBlue,
                Padding = new Padding(15, 8, 15, 8)
            };

            pnlBottom.Controls.Add(new Label
            {
                Text = "Meeting Notes:",
                Font = new Font("Segoe UI", 11),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(15, 8)
            });

            txtNotes = new TextBox
            {
                Font = new Font("Segoe UI", 10),
                Width = 420,
                Height = 90,
                Location = new Point(15, 32),
                Multiline = true,
                ScrollBars = ScrollBars.Vertical,
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Bottom
            };
            pnlBottom.Controls.Add(txtNotes);

            pnlBottom.Controls.Add(new Label
            {
                Text = "Absence fine (₦):",
                Font = new Font("Segoe UI", 10),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(450, 12)
            });
            txtFine = new TextBox
            {
                Font = new Font("Segoe UI", 10),
                Width = 100,
                Location = new Point(450, 34),
                Text = Schema.GetSetting("absent_fine")
            };
            if (string.IsNullOrEmpty(txtFine.Text)) txtFine.Text = "0";
            pnlBottom.Controls.Add(txtFine);

            pnlBottom.Controls.Add(new Label
            {
                Text = "Minutes levy (₦):",
                Font = new Font("Segoe UI", 10),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(560, 12)
            });
            txtLevy = new TextBox
            {
                Font = new Font("Segoe UI", 10),
                Width = 100,
                Location = new Point(560, 34),
                Text = "0"
            };
            pnlBottom.Controls.Add(txtLevy);

            var btnLevy = CreateSmallButton("Apply Minutes Levy to Absent", 450, 66, 210);
            btnLevy.BackColor = Color.FromArgb(230, 81, 0);
            btnLevy.ForeColor = White;
            btnLevy.Click += BtnLevy_Click;
            pnlBottom.Controls.Add(btnLevy);

            var btnSave = CreateButton("SAVE ATTENDANCE", 450, 108, 210, 42);
            btnSave.Click += BtnSave_Click;
            pnlBottom.Controls.Add(btnSave);

            lblMsg = new Label
            {
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Location = new Point(15, 132)
            };
            pnlBottom.Controls.Add(lblMsg);
            Controls.Add(pnlBottom);
        }

        private void BtnStart_Click(object? sender, EventArgs e)
        {
            string date = txtDate.Text.Trim();
            var (validDate, dateErr) = Validators.ValidateDate(date, "Date");
            if (!validDate) { lblMsg.ForeColor = Color.Red; lblMsg.Text = dateErr; return; }

            using (var conn = Connection.GetConnection())
            using (var cmd = conn.CreateCommand())
            {
                cmd.CommandText = "SELECT id FROM meetings WHERE meeting_date=@date LIMIT 1";
                cmd.Parameters.AddWithValue("@date", date);
                if (cmd.ExecuteScalar() != null)
                {
                    lblMsg.ForeColor = Color.Red;
                    lblMsg.Text = "A meeting already exists for this date. Loading it instead.";
                    LoadForDate(date);
                    return;
                }
            }

            _currentMeetingId = TransactionEngine.CreateMeeting(date, "", _userId);
            TransactionEngine.LogAudit(_userId, "Start Meeting", $"Meeting started for {date}");
            LoadForDate(date);
            lblMsg.ForeColor = Color.Green;
            lblMsg.Text = $"Meeting started for {date}";
        }

        private void LoadForDate(string date)
        {
            txtDate.Text = date;
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT id, meeting_number, notes FROM meetings WHERE meeting_date=@date ORDER BY created_at DESC LIMIT 1";
            cmd.Parameters.AddWithValue("@date", date);
            using var reader = cmd.ExecuteReader();
            if (reader.Read())
            {
                _currentMeetingId = reader["id"]!.ToString()!;
                lblMeetingNum.Text = $"Meeting #: {reader["meeting_number"]}";
                txtNotes.Text = reader["notes"]?.ToString() ?? "";
                LoadMemberList(_currentMeetingId);
            }
            else
            {
                _currentMeetingId = "";
                lblMeetingNum.Text = "Meeting #: -";
                txtNotes.Text = "";
                LoadMemberList(null);
            }
        }

        private void LoadMemberList(string? meetingId)
        {
            pnlMembers.Controls.Clear();
            _memberStatus.Clear();
            _btnYes.Clear();
            _btnNo.Clear();
            _memberRows.Clear();

            var saved = new Dictionary<string, string>();
            if (!string.IsNullOrEmpty(meetingId))
            {
                using var conn = Connection.GetConnection();
                using var cmd = conn.CreateCommand();
                cmd.CommandText = "SELECT member_id, status FROM attendance WHERE meeting_id=@mid";
                cmd.Parameters.AddWithValue("@mid", meetingId);
                using var reader = cmd.ExecuteReader();
                while (reader.Read())
                    saved[reader["member_id"]!.ToString()!] = reader["status"]!.ToString()!;
            }

            List<(string id, string name)> members = new();
            using (var conn = Connection.GetConnection())
            using (var cmd = conn.CreateCommand())
            {
                cmd.CommandText = "SELECT id, full_name, member_number FROM members WHERE status='Active' ORDER BY full_name";
                using var reader = cmd.ExecuteReader();
                while (reader.Read())
                    members.Add((reader.GetString(0), $"{reader["full_name"]} ({reader["member_number"]})"));
            }

            int y = 6;
            bool alt = false;
            foreach (var (id, name) in members)
            {
                string status = saved.TryGetValue(id, out var s) ? s : "Absent";
                _memberStatus[id] = status;

                var row = new Panel
                {
                    Location = new Point(6, y),
                    Size = new Size(620, 36),
                    BackColor = alt ? Color.FromArgb(245, 245, 245) : White,
                    Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
                };
                alt = !alt;

                row.Controls.Add(new Label
                {
                    Text = name,
                    Font = new Font("Segoe UI", 10),
                    ForeColor = Color.FromArgb(50, 50, 50),
                    AutoSize = true,
                    Location = new Point(8, 8)
                });

                var btnYes = new Button
                {
                    Text = "✓",
                    FlatStyle = FlatStyle.Flat,
                    Font = new Font("Segoe UI", 11, FontStyle.Bold),
                    Size = new Size(44, 30),
                    Location = new Point(460, 3),
                    Cursor = Cursors.Hand,
                    Tag = id
                };
                btnYes.FlatAppearance.BorderSize = 0;
                btnYes.Click += (s, e) => SetStatus(id, "Present");

                var btnNo = new Button
                {
                    Text = "✗",
                    FlatStyle = FlatStyle.Flat,
                    Font = new Font("Segoe UI", 11, FontStyle.Bold),
                    Size = new Size(44, 30),
                    Location = new Point(510, 3),
                    Cursor = Cursors.Hand,
                    Tag = id
                };
                btnNo.FlatAppearance.BorderSize = 0;
                btnNo.Click += (s, e) => SetStatus(id, "Absent");

                row.Controls.Add(btnYes);
                row.Controls.Add(btnNo);
                _btnYes[id] = btnYes;
                _btnNo[id] = btnNo;
                _memberRows[id] = row;
                PaintRow(id);
                pnlMembers.Controls.Add(row);
                y += 40;
            }
            UpdateSummary();
        }

        private void PaintRow(string memberId)
        {
            bool present = _memberStatus[memberId] == "Present";
            _btnYes[memberId].BackColor = present ? Green : Color.FromArgb(224, 224, 224);
            _btnYes[memberId].ForeColor = present ? White : Color.Gray;
            _btnNo[memberId].BackColor = !present ? Red : Color.FromArgb(224, 224, 224);
            _btnNo[memberId].ForeColor = !present ? White : Color.Gray;
        }

        private void SetStatus(string memberId, string status)
        {
            _memberStatus[memberId] = status;
            PaintRow(memberId);
            UpdateSummary();
        }

        private void UpdateSummary()
        {
            int present = 0;
            foreach (var s in _memberStatus.Values)
                if (s == "Present") present++;
            int total = _memberStatus.Count;
            lblSummary.Text = $"Present: {present} | Absent: {total - present} | Total: {total}";
        }

        private void BtnSave_Click(object? sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(_currentMeetingId))
            {
                lblMsg.ForeColor = Color.Red;
                lblMsg.Text = "Start or load a meeting first";
                return;
            }

            TransactionEngine.ClearMeetingAttendance(_currentMeetingId);
            foreach (var kvp in _memberStatus)
                TransactionEngine.RecordAttendance(_currentMeetingId, kvp.Key, kvp.Value);
            TransactionEngine.UpdateMeetingNotes(_currentMeetingId, txtNotes.Text.Trim());

            int present = 0, absent = 0;
            foreach (var s in _memberStatus.Values)
                if (s == "Present") present++; else absent++;

            string msg = $"Attendance saved! Present: {present}, Absent: {absent}";

            double.TryParse(txtFine.Text, out double fine);
            if (fine > 0 && absent > 0)
            {
                int fined = TransactionEngine.ApplyAbsenceFines(_currentMeetingId, fine, _userId);
                msg += $" | Absence fines applied to {fined} member(s)";
            }

            TransactionEngine.LogAudit(_userId, "Save Attendance", $"Attendance saved for meeting {_currentMeetingId}: {present} present, {absent} absent");
            lblMsg.ForeColor = Color.Green;
            lblMsg.Text = msg;
        }

        private void BtnLevy_Click(object? sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(_currentMeetingId))
            {
                lblMsg.ForeColor = Color.Red;
                lblMsg.Text = "Start or load a meeting first";
                return;
            }

            var (valid, amount) = Validators.ValidateAmount(txtLevy.Text);
            if (!valid)
            {
                lblMsg.ForeColor = Color.Red;
                lblMsg.Text = "Enter a valid levy amount greater than zero";
                return;
            }

            if (MessageBox.Show($"Apply {Helpers.FormatCurrency(amount)} minutes levy to ALL absent members? Present members should pay cash now.",
                "Confirm Levy", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
                return;

            int count = TransactionEngine.ApplyMinutesLevy(_currentMeetingId, amount, _userId);
            TransactionEngine.LogAudit(_userId, "Minutes Levy", $"Levy of {Helpers.FormatCurrency(amount)} applied to {count} absent member(s)");
            lblMsg.ForeColor = Color.Green;
            lblMsg.Text = $"Minutes levy applied to {count} absent member(s)";
        }

        private Button CreateSmallButton(string text, int x, int y, int width)
        {
            var btn = new Button
            {
                Text = text,
                FlatStyle = FlatStyle.Flat,
                BackColor = White,
                ForeColor = Blue,
                Font = new Font("Segoe UI", 9, FontStyle.Bold),
                Width = width,
                Height = 30,
                Top = y,
                Left = x,
                Cursor = Cursors.Hand
            };
            btn.FlatAppearance.BorderColor = Blue;
            btn.FlatAppearance.BorderSize = 1;
            return btn;
        }

        private Button CreateButton(string text, int x, int y, int width, int height)
        {
            var btn = new Button
            {
                Text = text,
                FlatStyle = FlatStyle.Flat,
                BackColor = Blue,
                ForeColor = White,
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                Width = width,
                Height = height,
                Top = y,
                Left = x,
                Cursor = Cursors.Hand
            };
            btn.FlatAppearance.BorderSize = 0;
            return btn;
        }
    }
}
