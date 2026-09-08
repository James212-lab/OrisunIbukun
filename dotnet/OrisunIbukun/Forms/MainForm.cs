using System;
using System.Drawing;
using System.Windows.Forms;

namespace OrisunIbukun.Forms
{
    public class MainForm : Form
    {
        private static readonly Color Blue = Color.FromArgb(21, 101, 192);
        private static readonly Color LightBlue = Color.FromArgb(227, 242, 253);
        private static readonly Color White = Color.White;
        private static readonly Color DarkGray = Color.FromArgb(50, 50, 50);

        private readonly string _currentUserId;
        private readonly string _currentUserName;
        private readonly string _currentUserRole;

        private Panel pnlNav = null!;
        private Panel pnlMain = null!;
        private Panel pnlHeader = null!;
        private Button? _activeButton;

        public MainForm(string userId, string userName, string role)
        {
            _currentUserId = userId;
            _currentUserName = userName;
            _currentUserRole = role;
            InitializeComponent();
            LoadDashboard();
        }

        private void InitializeComponent()
        {
            SuspendLayout();

            Text = "ORISUN IBUKUN – Owode Unit";
            BackColor = White;
            StartPosition = FormStartPosition.Manual;

            var screen = Screen.FromPoint(Cursor.Position).WorkingArea;
            int w = Math.Min(1200, screen.Width);
            int h = Math.Min(750, screen.Height);
            Size = new Size(w, h);
            Location = new Point(screen.Left + (screen.Width - w) / 2, screen.Top + (screen.Height - h) / 2);
            MinimumSize = new Size(900, 550);

            pnlHeader = new Panel
            {
                Dock = DockStyle.Top,
                Height = 60,
                BackColor = Blue
            };

            var lblHeader = new Label
            {
                Text = "ORISUN IBUKUN – Owode Unit",
                ForeColor = White,
                Font = new Font("Segoe UI", 16, FontStyle.Bold),
                AutoSize = true,
                Top = 15,
                Left = 20
            };

            var lblUser = new Label
            {
                Text = $"{_currentUserName} ({_currentUserRole})",
                ForeColor = White,
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Top = 22,
                Anchor = AnchorStyles.Top | AnchorStyles.Right
            };

            var btnLogout = new Button
            {
                Text = "Logout",
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(183, 28, 28),
                ForeColor = White,
                Font = new Font("Segoe UI", 9),
                Width = 80,
                Height = 30,
                Anchor = AnchorStyles.Top | AnchorStyles.Right,
                Cursor = Cursors.Hand
            };
            btnLogout.FlatAppearance.BorderSize = 0;
            btnLogout.Top = 15;
            btnLogout.Left = pnlHeader.Width - 100;
            btnLogout.Click += (s, e) => Logout();
            pnlHeader.Resize += (s, e) =>
            {
                btnLogout.Left = pnlHeader.Width - 100;
                lblUser.Left = pnlHeader.Width - 100 - lblUser.Width - 12;
            };

            pnlHeader.Controls.AddRange(new Control[] { lblHeader, lblUser, btnLogout });

            pnlNav = new Panel
            {
                Dock = DockStyle.Left,
                Width = 200,
                BackColor = Color.FromArgb(25, 55, 109)
            };

            pnlMain = new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = LightBlue,
                Padding = new Padding(10)
            };

            string[] navItems = { "DASHBOARD", "MEMBERS", "ATTENDANCE", "SAVINGS", "LOANS", "REPORTS", "BACKUP", "SETTINGS" };
            int y = 10;
            foreach (var item in navItems)
            {
                var btn = CreateNavButton(item, y);
                pnlNav.Controls.Add(btn);
                y += 55;
            }

            Controls.Add(pnlMain);
            Controls.Add(pnlNav);
            Controls.Add(pnlHeader);

            ResumeLayout(false);

            KeyPreview = true;
            KeyDown += MainForm_KeyDown;
            _sessionTimer = new System.Windows.Forms.Timer { Interval = 30000 };
            _sessionTimer.Tick += SessionTimer_Tick;
            _sessionTimer.Start();
            Application.AddMessageFilter(_activityFilter = new ActivityFilter(this));
        }

        private System.Windows.Forms.Timer _sessionTimer = null!;
        private DateTime _lastActivity = DateTime.Now;
        private bool _warningShown = false;
        private ActivityFilter? _activityFilter;
        private bool _loggingOut = false;
        private const int SessionTimeoutMinutes = 20;
        private const int SessionWarningMinutes = 5;

        private sealed class ActivityFilter : IMessageFilter
        {
            private readonly MainForm _form;
            public ActivityFilter(MainForm form) { _form = form; }
            public bool PreFilterMessage(ref Message m)
            {
                const int WM_KEYDOWN = 0x0100;
                const int WM_LBUTTONDOWN = 0x0201;
                const int WM_RBUTTONDOWN = 0x0204;
                const int WM_MOUSEWHEEL = 0x020A;
                if (m.Msg == WM_KEYDOWN || m.Msg == WM_LBUTTONDOWN || m.Msg == WM_RBUTTONDOWN || m.Msg == WM_MOUSEWHEEL)
                    _form.RecordActivity();
                return false;
            }
        }

        private void RecordActivity()
        {
            _lastActivity = DateTime.Now;
            _warningShown = false;
        }

        private void SessionTimer_Tick(object? sender, EventArgs e)
        {
            if (_loggingOut) return;
            double idleMinutes = (DateTime.Now - _lastActivity).TotalMinutes;
            if (idleMinutes >= SessionTimeoutMinutes)
            {
                _sessionTimer.Stop();
                MessageBox.Show(this, "Your session has expired due to inactivity.", "Session Expired",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
                Logout();
            }
            else if (idleMinutes >= SessionTimeoutMinutes - SessionWarningMinutes && !_warningShown)
            {
                _warningShown = true;
                int remaining = (int)Math.Ceiling(SessionTimeoutMinutes - idleMinutes);
                MessageBox.Show(this, $"Your session will expire in {remaining} minute(s) due to inactivity.",
                    "Session Expiring Soon", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        private void MainForm_KeyDown(object? sender, KeyEventArgs e)
        {
            if (ActiveControl is TextBox || ActiveControl is ComboBox || ActiveControl is RichTextBox)
            {
                if (e.KeyCode != Keys.F1 && e.KeyCode != Keys.Escape) return;
            }
            if (e.Control && e.KeyCode == Keys.M) { Nav_Click("MEMBERS"); e.Handled = true; }
            else if (e.Control && e.KeyCode == Keys.A) { Nav_Click("ATTENDANCE"); e.Handled = true; }
            else if (e.Control && e.KeyCode == Keys.S) { Nav_Click("SAVINGS"); e.Handled = true; }
            else if (e.Control && e.KeyCode == Keys.L) { Nav_Click("LOANS"); e.Handled = true; }
            else if (e.Control && e.KeyCode == Keys.R) { Nav_Click("REPORTS"); e.Handled = true; }
            else if (e.Control && e.KeyCode == Keys.B) { Nav_Click("BACKUP"); e.Handled = true; }
            else if (e.Control && e.KeyCode == Keys.P) { Nav_Click("SETTINGS"); e.Handled = true; }
            else if (e.Control && e.KeyCode == Keys.Q) { Logout(); e.Handled = true; }
            else if (e.KeyCode == Keys.F1)
            {
                MessageBox.Show(this,
                    "Ctrl+M: Members\nCtrl+A: Attendance\nCtrl+S: Savings\nCtrl+L: Loans\nCtrl+R: Reports\nCtrl+B: Backup\nCtrl+P: Settings\nCtrl+Q: Logout\nF1: Show this help",
                    "Keyboard Shortcuts", MessageBoxButtons.OK, MessageBoxIcon.Information);
                e.Handled = true;
            }
            else if (e.KeyCode == Keys.Escape) { Focus(); e.Handled = true; }
        }

        public void Logout()
        {
            if (_loggingOut) return;
            _loggingOut = true;
            try
            {
                Engine.TransactionEngine.LogAudit(_currentUserId, "Logout", $"User {_currentUserName} logged out");
            }
            catch { }
            _sessionTimer.Stop();
            if (_activityFilter != null)
                Application.RemoveMessageFilter(_activityFilter);
            var login = new LoginForm();
            login.Show();
            Close();
        }

        private Button CreateNavButton(string text, int top)
        {
            var btn = new Button
            {
                Text = text,
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(25, 55, 109),
                ForeColor = White,
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                Width = 200,
                Height = 50,
                Top = top,
                Left = 0,
                TextAlign = ContentAlignment.MiddleLeft,
                Padding = new Padding(15, 0, 0, 0),
                Cursor = Cursors.Hand
            };
            btn.FlatAppearance.BorderSize = 0;
            btn.MouseEnter += (s, e) => { if (btn != _activeButton) btn.BackColor = Color.FromArgb(35, 75, 139); };
            btn.MouseLeave += (s, e) => { if (btn != _activeButton) btn.BackColor = Color.FromArgb(25, 55, 109); };
            btn.Click += (s, e) => Nav_Click(text);
            return btn;
        }

        private void Nav_Click(string section)
        {
            pnlMain.Controls.Clear();

            foreach (Control c in pnlNav.Controls)
            {
                if (c is Button b)
                {
                    if (b.Text == section)
                    {
                        b.BackColor = Color.FromArgb(66, 129, 244);
                        b.ForeColor = White;
                        _activeButton = b;
                    }
                    else
                    {
                        b.BackColor = Color.FromArgb(25, 55, 109);
                        b.ForeColor = White;
                    }
                }
            }

            Control form = section switch
            {
                "MEMBERS" => new MemberForm(_currentUserId),
                "ATTENDANCE" => new AttendanceForm(_currentUserId),
                "SAVINGS" => new SavingsForm(_currentUserId),
                "LOANS" => new LoanForm(_currentUserId, _currentUserRole),
                "REPORTS" => new ReportForm(_currentUserId),
                "BACKUP" => new BackupForm(_currentUserId),
                "SETTINGS" => new SettingsForm(_currentUserId),
                _ => new DashboardControl(_currentUserId)
            };

            form.Dock = DockStyle.Fill;
            pnlMain.Controls.Add(form);
        }

        private void LoadDashboard()
        {
            pnlMain.Controls.Clear();
            var dashboard = new DashboardControl(_currentUserId);
            dashboard.Dock = DockStyle.Fill;
            pnlMain.Controls.Add(dashboard);
        }
    }

    public class DashboardControl : UserControl
    {
        private static readonly Color Blue = Color.FromArgb(21, 101, 192);
        private static readonly Color LightBlue = Color.FromArgb(227, 242, 253);
        private static readonly Color White = Color.White;

        private readonly string _userId;
        private FlowLayoutPanel pnlMetrics = null!;

        public DashboardControl(string userId)
        {
            _userId = userId;
            BackColor = LightBlue;
            InitializeDashboard();
            LoadDashboardData();
            Resize += (s, e) => RelayoutCards();
        }

        private void InitializeDashboard()
        {
            // ─── Scroll container so content never clips on small screens ───
            var scroll = new Panel
            {
                Dock = DockStyle.Fill,
                AutoScroll = true,
                BackColor = LightBlue,
                Padding = new Padding(8)
            };

            // ─── Header ───
            var pnlHeader = new Panel
            {
                Dock = DockStyle.Top,
                Height = 64,
                BackColor = Blue
            };

            var lblWelcome = new Label
            {
                Text = "DASHBOARD",
                ForeColor = White,
                Font = new Font("Segoe UI", 18, FontStyle.Bold),
                AutoSize = true,
                Top = 15,
                Left = 20
            };

            var lblDate = new Label
            {
                Text = DateTime.Now.ToString("dddd, dd MMMM yyyy"),
                ForeColor = Color.FromArgb(200, 255, 255, 255),
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Anchor = AnchorStyles.Top | AnchorStyles.Right
            };

            pnlHeader.Controls.Add(lblWelcome);
            pnlHeader.Controls.Add(lblDate);
            pnlHeader.Resize += (s, e) =>
            {
                lblDate.Left = pnlHeader.Width - lblDate.Width - 140;
                lblDate.Top = 24;
            };
            scroll.Controls.Add(pnlHeader);

            // ─── Quick Actions ───
            var pnlActionsTitle = new Label
            {
                Text = "QUICK ACTIONS",
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                ForeColor = Color.FromArgb(80, 100, 130),
                AutoSize = true,
                Top = 78,
                Left = 12,
                Height = 20
            };
            scroll.Controls.Add(pnlActionsTitle);

            var actionsFlow = new FlowLayoutPanel
            {
                Top = 98,
                Left = 12,
                Height = 60,
                Width = 900,
                FlowDirection = FlowDirection.LeftToRight,
                WrapContents = false,
                BackColor = LightBlue,
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
            };

            string[][] actions = {
                new[] { "MEMBERS", "Manage Registry" },
                new[] { "ATTENDANCE", "Friday Meeting" },
                new[] { "SAVINGS", "Record Deposit" },
                new[] { "LOANS", "Issue / Repay" },
                new[] { "REPORTS", "Monthly Reports" },
                new[] { "BACKUP", "Backup Vault" },
                new[] { "SETTINGS", "Configuration" },
            };
            foreach (var a in actions)
            {
                var btn = CreateQuickAction(a[0], a[1]);
                actionsFlow.Controls.Add(btn);
            }
            scroll.Controls.Add(actionsFlow);

            // ─── Financial Performance Register ───
            var lblMetricsTitle = new Label
            {
                Text = "THIS MONTH — " + DateTime.Now.ToString("MMMM yyyy").ToUpper(),
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                ForeColor = Color.FromArgb(80, 100, 130),
                AutoSize = true,
                Top = 176,
                Left = 12,
                Height = 20
            };
            scroll.Controls.Add(lblMetricsTitle);

            var lblMeetingLine = new Label
            {
                Text = "Last meeting: —",
                Font = new Font("Segoe UI", 9),
                ForeColor = Color.FromArgb(120, 130, 150),
                AutoSize = true,
                Top = 198,
                Left = 12,
                Height = 18
            };
            scroll.Controls.Add(lblMeetingLine);

            pnlMetrics = new FlowLayoutPanel
            {
                Top = 218,
                Left = 12,
                Height = 560,
                Width = 900,
                FlowDirection = FlowDirection.LeftToRight,
                WrapContents = true,
                BackColor = LightBlue,
                Padding = new Padding(0),
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
            };
            pnlMetrics.ControlAdded += (s, e) => RelayoutCards();
            scroll.Controls.Add(pnlMetrics);

            // ─── Footer notice ───
            var lblFooter = new Label
            {
                Text = "ORISUN IBUKUN – Owode Unit Cooperative Ledger  •  SQLite Encrypted  •  Offline Atomic Ledger",
                Font = new Font("Segoe UI", 8, FontStyle.Regular),
                ForeColor = Color.FromArgb(140, 150, 170),
                AutoSize = true,
                Top = 788,
                Left = 12,
                Height = 20
            };
            scroll.Controls.Add(lblFooter);

            Controls.Add(scroll);
            _lblMeetingLine = lblMeetingLine;
        }

        private Label? _lblMeetingLine;

        private void RelayoutCards()
        {
            if (pnlMetrics == null || pnlMetrics.Controls.Count == 0) return;
            int availW = Math.Max(200, pnlMetrics.Width);
            int cols = availW > 640 ? 3 : (availW > 400 ? 2 : 1);
            int cardW = (availW - (cols * 12)) / cols;
            foreach (Control c in pnlMetrics.Controls)
            {
                if (c is Panel card)
                {
                    card.Width = cardW;
                    card.Margin = new Padding(6);
                }
            }
        }

        private Button CreateQuickAction(string title, string subtitle)
        {
            var btn = new Button
            {
                Text = $"{title}\r\n{subtitle}",
                FlatStyle = FlatStyle.Flat,
                BackColor = White,
                ForeColor = Color.FromArgb(30, 60, 100),
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                Width = 150,
                Height = 52,
                Margin = new Padding(3, 0, 3, 0),
                TextAlign = ContentAlignment.MiddleCenter,
                Cursor = Cursors.Hand
            };
            btn.FlatAppearance.BorderColor = Color.FromArgb(210, 220, 235);
            btn.FlatAppearance.BorderSize = 1;
            btn.Click += (s, e) =>
            {
                if (Parent?.Parent is MainForm mf)
                {
                    var method = mf.GetType().GetMethod("Nav_Click",
                        System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
                    method?.Invoke(mf, new object[] { title });
                }
            };
            return btn;
        }

        private void LoadDashboardData()
        {
            string prefix = DateTime.Now.ToString("yyyy-MM");
            double moneyIn, loansDisbursed, repaidMonth, remitted, expenses;
            double totalSavings, totalShares;
            int activeMembers;
            string meetingLabel = "No meetings yet";
            int present = 0, absent = 0;

            using (var conn = Database.Connection.GetConnection())
            {
                using var cmd = conn.CreateCommand();
                cmd.CommandText = "SELECT COUNT(*) FROM members WHERE status='Active'";
                activeMembers = Convert.ToInt32(cmd.ExecuteScalar());

                cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM savings";
                totalSavings = Convert.ToDouble(cmd.ExecuteScalar());

                cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM shares";
                totalShares = Convert.ToDouble(cmd.ExecuteScalar());

                cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM savings WHERE savings_date LIKE @pfx || '%'";
                cmd.Parameters.AddWithValue("@pfx", prefix);
                double monthlySavings = Convert.ToDouble(cmd.ExecuteScalar());

                cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM shares WHERE share_date LIKE @pfx || '%'";
                double monthlyShares = Convert.ToDouble(cmd.ExecuteScalar());
                moneyIn = monthlySavings + monthlyShares;

                cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM loans WHERE disbursed_date LIKE @pfx || '%'";
                loansDisbursed = Convert.ToDouble(cmd.ExecuteScalar());

                cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM loan_repayments WHERE payment_date LIKE @pfx || '%'";
                repaidMonth = Convert.ToDouble(cmd.ExecuteScalar());

                cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM headquarters_remittances WHERE remittance_date LIKE @pfx || '%'";
                remitted = Convert.ToDouble(cmd.ExecuteScalar());

                cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE expense_date LIKE @pfx || '%'";
                expenses = Convert.ToDouble(cmd.ExecuteScalar());

                cmd.CommandText = "SELECT id, meeting_number, meeting_date FROM meetings ORDER BY meeting_date DESC LIMIT 1";
                using (var reader = cmd.ExecuteReader())
                {
                    if (reader.Read())
                    {
                        string mtgId = reader["id"]!.ToString()!;
                        meetingLabel = $"Meeting #{reader["meeting_number"]} ({reader["meeting_date"]})";
                        reader.Close();

                        using var c2 = conn.CreateCommand();
                        c2.CommandText = "SELECT COUNT(*) FROM attendance WHERE meeting_id=@mtg AND status='Present'";
                        c2.Parameters.AddWithValue("@mtg", mtgId);
                        present = Convert.ToInt32(c2.ExecuteScalar());

                        using var c3 = conn.CreateCommand();
                        c3.CommandText = "SELECT COUNT(*) FROM attendance WHERE meeting_id=@mtg AND status='Absent'";
                        c3.Parameters.AddWithValue("@mtg", mtgId);
                        absent = Convert.ToInt32(c3.ExecuteScalar());
                    }
                }
            }

            double outstanding = Engine.TransactionEngine.GetMemberOutstandingTotal();
            double chargesOwed = Engine.TransactionEngine.GetTotalChargesOwed();
            double net = moneyIn - loansDisbursed - remitted - expenses;

            if (_lblMeetingLine != null)
                _lblMeetingLine.Text = $"Last meeting: {meetingLabel}  •  Present: {present}  •  Absent: {absent}";

            pnlMetrics.Controls.Clear();

            AddMetricCard("Active Members", activeMembers.ToString(), Blue);
            AddMetricCard("Total Savings", Utils.Helpers.FormatCurrency(totalSavings), Color.FromArgb(16, 128, 61));
            AddMetricCard("Total Shares Value", Utils.Helpers.FormatCurrency(totalShares), Color.FromArgb(94, 120, 195));
            AddMetricCard("Money In (Month)", Utils.Helpers.FormatCurrency(moneyIn), Color.FromArgb(16, 128, 61));
            AddMetricCard("Loans Disbursed (Month)", Utils.Helpers.FormatCurrency(loansDisbursed), Color.FromArgb(180, 83, 9));
            AddMetricCard("Repaid This Month", Utils.Helpers.FormatCurrency(repaidMonth), Color.FromArgb(16, 128, 61));
            AddMetricCard("Outstanding Loans", Utils.Helpers.FormatCurrency(outstanding), Color.FromArgb(220, 38, 38));
            AddMetricCard("Charges Owed (Fines/Minutes)", Utils.Helpers.FormatCurrency(chargesOwed), Color.FromArgb(220, 38, 38));
            AddMetricCard("Remitted to HQ (Month)", Utils.Helpers.FormatCurrency(remitted), Color.FromArgb(180, 83, 9));
            AddMetricCard("Net Cash Movement (Month)", Utils.Helpers.FormatCurrency(net), Blue);

            RelayoutCards();
        }

        private void AddMetricCard(string title, string value, Color accentColor)
        {
            var card = new Panel
            {
                Height = 110,
                BackColor = White,
                Margin = new Padding(5),
                Padding = new Padding(12, 8, 12, 8)
            };

            // Left accent strip
            var strip = new Panel
            {
                Dock = DockStyle.Left,
                Width = 5,
                BackColor = accentColor
            };
            strip.BringToFront();

            var lblTitle = new Label
            {
                Text = title.ToUpper(),
                ForeColor = Color.FromArgb(100, 110, 130),
                Font = new Font("Segoe UI", 8, FontStyle.Bold),
                AutoSize = true,
                Top = 6,
                Left = 14
            };

            var lblValue = new Label
            {
                Text = value,
                ForeColor = Color.FromArgb(20, 30, 50),
                Font = new Font("Segoe UI", 18, FontStyle.Bold),
                AutoSize = true,
                Top = 32,
                Left = 14
            };

            card.Controls.Add(lblTitle);
            card.Controls.Add(lblValue);
            card.Controls.Add(strip);
            pnlMetrics.Controls.Add(card);
        }
    }
}
