using System;
using System.Drawing;
using System.Windows.Forms;
using OrisunIbukun.Database;
using OrisunIbukun.Utils;

namespace OrisunIbukun.Forms
{
    public class SettingsForm : UserControl
    {
        private static readonly Color Blue = Color.FromArgb(21, 101, 192);
        private static readonly Color LightBlue = Color.FromArgb(227, 242, 253);
        private static readonly Color White = Color.White;

        private readonly string _userId;
        private TabControl tabControl = null!;

        private TextBox txtAppName = null!;
        private TextBox txtUnitName = null!;
        private TextBox txtCurrency = null!;
        private TextBox txtMeetingDay = null!;
        private Label lblInfoMsg = null!;

        private TextBox txtSharePrice = null!;
        private TextBox txtEntranceFee = null!;
        private TextBox txtMaxLoan = null!;
        private TextBox txtInterestRate = null!;
        private TextBox txtSavingsTarget = null!;
        private TextBox txtMinWithdrawal = null!;
        private TextBox txtGuarantors = null!;
        private ComboBox cmbInterestMethod = null!;
        private TextBox txtLatePenalty = null!;
        private TextBox txtAbsentFine = null!;
        private Label lblFinMsg = null!;

        private TextBox txtNewUsername = null!;
        private TextBox txtNewPin = null!;
        private TextBox txtNewFullName = null!;
        private ComboBox cboNewRole = null!;
        private Label lblUserMsg = null!;
        private DataGridView dgvUsers = null!;

        public SettingsForm(string userId)
        {
            _userId = userId;
            BackColor = LightBlue;
            InitializeForm();
            LoadSettings();
            LoadUsers();
        }

        private void InitializeForm()
        {
            var pnlTop = new Panel
            {
                Dock = DockStyle.Top,
                Height = 50,
                BackColor = LightBlue
            };

            var lblTitle = new Label
            {
                Text = "Settings",
                Font = new Font("Segoe UI", 16, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Top = 10,
                Left = 15
            };
            pnlTop.Controls.Add(lblTitle);
            Controls.Add(pnlTop);

            tabControl = new TabControl
            {
                Dock = DockStyle.Fill,
                Font = new Font("Segoe UI", 10)
            };

            var tabInfo = new TabPage("Cooperative Info");
            var tabFinancial = new TabPage("Financial");
            var tabUsers = new TabPage("Users");
            var tabAbout = new TabPage("About");

            BuildInfoTab(tabInfo);
            BuildFinancialTab(tabFinancial);
            BuildUsersTab(tabUsers);
            BuildAboutTab(tabAbout);

            tabControl.TabPages.AddRange(new[] { tabInfo, tabFinancial, tabUsers, tabAbout });
            Controls.Add(tabControl);
        }

        private void BuildInfoTab(TabPage tab)
        {
            int y = 20;
            AddLabel(tab, "App Name:", 20, y);
            txtAppName = AddTextBox(tab, 150, y, 300);
            y += 45;

            AddLabel(tab, "Unit Name:", 20, y);
            txtUnitName = AddTextBox(tab, 150, y, 300);
            y += 45;

            AddLabel(tab, "Currency Symbol:", 20, y);
            txtCurrency = AddTextBox(tab, 150, y, 100);
            y += 45;

            AddLabel(tab, "Meeting Day:", 20, y);
            txtMeetingDay = AddTextBox(tab, 150, y, 200);
            y += 60;

            var btnSave = CreateButton("SAVE", 150, y, 120, 40);
            btnSave.Click += (s, e) =>
            {
                Schema.SetSetting("app_name", txtAppName.Text.Trim());
                Schema.SetSetting("unit_name", txtUnitName.Text.Trim());
                Schema.SetSetting("currency", txtCurrency.Text.Trim());
                Schema.SetSetting("meeting_day", txtMeetingDay.Text.Trim());
                lblInfoMsg.ForeColor = Color.Green;
                lblInfoMsg.Text = "Settings saved!";
            };
            tab.Controls.Add(btnSave);

            lblInfoMsg = new Label
            {
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Top = y + 50,
                Left = 150
            };
            tab.Controls.Add(lblInfoMsg);
        }

        private void BuildFinancialTab(TabPage tab)
        {
            tab.AutoScroll = true;
            int y = 20;
            AddLabel(tab, "Share Price:", 20, y);
            txtSharePrice = AddTextBox(tab, 180, y, 150);
            y += 45;

            AddLabel(tab, "Entrance Fee:", 20, y);
            txtEntranceFee = AddTextBox(tab, 180, y, 150);
            y += 45;

            AddLabel(tab, "Max Loan Multiplier:", 20, y);
            txtMaxLoan = AddTextBox(tab, 180, y, 100);
            y += 45;

            AddLabel(tab, "Interest Rate (%):", 20, y);
            txtInterestRate = AddTextBox(tab, 180, y, 100);
            y += 45;

            AddLabel(tab, "Savings Target:", 20, y);
            txtSavingsTarget = AddTextBox(tab, 180, y, 150);
            y += 45;

            AddLabel(tab, "Min Savings Withdrawal:", 20, y);
            txtMinWithdrawal = AddTextBox(tab, 240, y, 150);
            y += 45;

            AddLabel(tab, "Required Guarantors:", 20, y);
            txtGuarantors = AddTextBox(tab, 240, y, 100);
            y += 45;

            AddLabel(tab, "Interest Method:", 20, y);
            cmbInterestMethod = new ComboBox
            {
                Font = new Font("Segoe UI", 10),
                Width = 150,
                Top = y,
                Left = 240,
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            cmbInterestMethod.Items.AddRange(new object[] { "Flat", "Reducing" });
            cmbInterestMethod.SelectedIndex = 0;
            tab.Controls.Add(cmbInterestMethod);
            y += 45;

            AddLabel(tab, "Late Payment Penalty:", 20, y);
            txtLatePenalty = AddTextBox(tab, 240, y, 150);
            y += 45;

            AddLabel(tab, "Absent Fine:", 20, y);
            txtAbsentFine = AddTextBox(tab, 240, y, 150);
            y += 60;

            var btnSave = CreateButton("SAVE", 180, y, 120, 40);
            btnSave.Click += (s, e) =>
            {
                Schema.SetSetting("share_price", txtSharePrice.Text.Trim());
                Schema.SetSetting("entrance_fee", txtEntranceFee.Text.Trim());
                Schema.SetSetting("max_loan_multiplier", txtMaxLoan.Text.Trim());
                Schema.SetSetting("interest_rate", txtInterestRate.Text.Trim());
                Schema.SetSetting("savings_target", txtSavingsTarget.Text.Trim());
                Schema.SetSetting("min_savings_withdrawal", txtMinWithdrawal.Text.Trim());
                Schema.SetSetting("required_guarantors", txtGuarantors.Text.Trim());
                Schema.SetSetting("interest_method", cmbInterestMethod.SelectedItem?.ToString() ?? "Flat");
                Schema.SetSetting("late_payment_penalty", txtLatePenalty.Text.Trim());
                Schema.SetSetting("absent_fine", txtAbsentFine.Text.Trim());
                lblFinMsg.ForeColor = Color.Green;
                lblFinMsg.Text = "Settings saved!";
            };
            tab.Controls.Add(btnSave);

            lblFinMsg = new Label
            {
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Top = y + 50,
                Left = 180
            };
            tab.Controls.Add(lblFinMsg);
        }

        private void BuildUsersTab(TabPage tab)
        {
            var pnlAdd = new Panel
            {
                Dock = DockStyle.Left,
                Width = 400,
                BackColor = White,
                Padding = new Padding(15)
            };

            var lblAdd = new Label
            {
                Text = "Add New User",
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Top = 10,
                Left = 15
            };
            pnlAdd.Controls.Add(lblAdd);

            int y = 45;
            AddLabel(pnlAdd, "Full Name:", 15, y);
            txtNewFullName = AddTextBox(pnlAdd, 15, y + 25, 250);
            y += 65;

            AddLabel(pnlAdd, "Username:", 15, y);
            txtNewUsername = AddTextBox(pnlAdd, 15, y + 25, 200);
            y += 65;

            AddLabel(pnlAdd, "PIN (4-6 digits):", 15, y);
            txtNewPin = AddTextBox(pnlAdd, 15, y + 25, 150);
            txtNewPin.UseSystemPasswordChar = true;
            y += 65;

            AddLabel(pnlAdd, "Role:", 15, y);
            cboNewRole = new ComboBox
            {
                Font = new Font("Segoe UI", 10),
                Width = 180,
                Top = y + 25,
                Left = 15,
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            cboNewRole.Items.AddRange(new object[] { "Administrator", "Treasurer", "Secretary", "Member" });
            cboNewRole.SelectedIndex = 0;
            pnlAdd.Controls.Add(cboNewRole);
            y += 70;

            var btnAdd = CreateButton("ADD USER", 15, y, 120, 35);
            btnAdd.Click += BtnAddUser_Click;
            pnlAdd.Controls.Add(btnAdd);
            y += 45;

            lblUserMsg = new Label
            {
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Top = y,
                Left = 15
            };
            pnlAdd.Controls.Add(lblUserMsg);
            tab.Controls.Add(pnlAdd);

            var pnlGrid = new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = White,
                Padding = new Padding(10)
            };

            var btnDeactivate = CreateButton("Deactivate", 10, 6, 120, 34);
            btnDeactivate.BackColor = Color.Firebrick;
            btnDeactivate.Click += BtnDeactivate_Click;
            pnlGrid.Controls.Add(btnDeactivate);

            var btnReactivate = CreateButton("Reactivate", 140, 6, 120, 34);
            btnReactivate.BackColor = Color.SeaGreen;
            btnReactivate.Click += BtnReactivate_Click;
            pnlGrid.Controls.Add(btnReactivate);

            dgvUsers = new DataGridView
            {
                Top = 48,
                Left = 10,
                BackgroundColor = White,
                BorderStyle = BorderStyle.None,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                MultiSelect = false,
                ReadOnly = true,
                AllowUserToAddRows = false,
                Font = new Font("Segoe UI", 9),
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom
            };
            pnlGrid.Controls.Add(dgvUsers);
            pnlGrid.Resize += (s, e) =>
            {
                dgvUsers.Width = pnlGrid.ClientSize.Width - 20;
                dgvUsers.Height = pnlGrid.ClientSize.Height - 58;
            };
            tab.Controls.Add(pnlGrid);
        }

        private void BuildAboutTab(TabPage tab)
        {
            var lblAppName = new Label
            {
                Text = Schema.GetSetting("app_name"),
                Font = new Font("Segoe UI", 20, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Top = 30,
                Left = 50
            };
            tab.Controls.Add(lblAppName);

            var lblUnit = new Label
            {
                Text = Schema.GetSetting("unit_name"),
                Font = new Font("Segoe UI", 14),
                ForeColor = Color.FromArgb(50, 50, 50),
                AutoSize = true,
                Top = 80,
                Left = 50
            };
            tab.Controls.Add(lblUnit);

            var lines = new[]
            {
                "Offline Cooperative Management System",
                "",
                "Version: 1.0.0",
                "Framework: .NET 8 WinForms",
                "Database: SQLite",
                "",
                "Features:",
                "  - Member Management",
                "  - Savings & Shares Tracking",
                "  - Loan Management",
                "  - Attendance Tracking",
                "  - Financial Reports",
                "  - Backup & Restore",
                "",
                "© 2026 Orisun Ibukun Cooperative"
            };

            int y = 130;
            foreach (var line in lines)
            {
                tab.Controls.Add(new Label
                {
                    Text = line,
                    Font = new Font("Segoe UI", 11),
                    ForeColor = Color.FromArgb(80, 80, 80),
                    AutoSize = true,
                    Top = y,
                    Left = 50
                });
                y += 25;
            }
        }

private void BtnAddUser_Click(object? sender, EventArgs e)
        {
            var (validName, nameErr) = Validators.ValidateRequired(txtNewFullName.Text, "Full Name");
            if (!validName) { lblUserMsg.ForeColor = Color.Red; lblUserMsg.Text = nameErr; return; }

            var (validUser, userErr) = Validators.ValidateRequired(txtNewUsername.Text, "Username");
            if (!validUser) { lblUserMsg.ForeColor = Color.Red; lblUserMsg.Text = userErr; return; }

            var (validPin, pinErr) = Validators.ValidatePin(txtNewPin.Text);
            if (!validPin) { lblUserMsg.ForeColor = Color.Red; lblUserMsg.Text = pinErr; return; }

            try
            {
                using var conn = Connection.GetConnection();
                using var cmd = conn.CreateCommand();
                cmd.CommandText = @"INSERT INTO users (id, username, pin_hash, full_name, role)
                    VALUES (@id, @uname, @pin, @fname, @role)";
                cmd.Parameters.AddWithValue("@id", Helpers.GenerateId("usr"));
                cmd.Parameters.AddWithValue("@uname", txtNewUsername.Text.Trim());
                cmd.Parameters.AddWithValue("@pin", Helpers.HashPin(txtNewPin.Text.Trim()));
                cmd.Parameters.AddWithValue("@fname", txtNewFullName.Text.Trim());
                cmd.Parameters.AddWithValue("@role", cboNewRole.SelectedItem?.ToString() ?? "Member");
                cmd.ExecuteNonQuery();

                lblUserMsg.ForeColor = Color.Green;
                lblUserMsg.Text = "User added successfully!";
                txtNewUsername.Text = "";
                txtNewPin.Text = "";
                txtNewFullName.Text = "";
                LoadUsers();
            }
            catch (Exception ex)
            {
                lblUserMsg.ForeColor = Color.Red;
                lblUserMsg.Text = ex.Message.Contains("UNIQUE") ? "Username already exists" : "Error: " + ex.Message;
            }
        }

        private void BtnDeactivate_Click(object? sender, EventArgs e)
        {
            if (dgvUsers.CurrentRow == null) return;
            string id = dgvUsers.CurrentRow.Cells["id"].Value?.ToString() ?? "";
            string username = dgvUsers.CurrentRow.Cells["Username"].Value?.ToString() ?? "";
            if (string.IsNullOrEmpty(id)) return;
            if (id == _userId)
            {
                MessageBox.Show("You cannot deactivate your own account.", "Not Allowed", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            if (dgvUsers.CurrentRow.Cells["Active"].Value?.ToString() == "No")
            {
                MessageBox.Show("This user is already deactivated.", "Info", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            if (MessageBox.Show($"Deactivate user '{username}'?", "Confirm", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
                return;
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "UPDATE users SET is_active=0 WHERE id=@id";
            cmd.Parameters.AddWithValue("@id", id);
            cmd.ExecuteNonQuery();
            LoadUsers();
        }

        private void BtnReactivate_Click(object? sender, EventArgs e)
        {
            if (dgvUsers.CurrentRow == null) return;
            string id = dgvUsers.CurrentRow.Cells["id"].Value?.ToString() ?? "";
            if (string.IsNullOrEmpty(id)) return;
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "UPDATE users SET is_active=1 WHERE id=@id";
            cmd.Parameters.AddWithValue("@id", id);
            cmd.ExecuteNonQuery();
            LoadUsers();
        }

        private void LoadSettings()
        {
            txtAppName.Text = Schema.GetSetting("app_name");
            txtUnitName.Text = Schema.GetSetting("unit_name");
            txtCurrency.Text = Schema.GetSetting("currency");
            txtMeetingDay.Text = Schema.GetSetting("meeting_day");
            txtSharePrice.Text = Schema.GetSetting("share_price");
            txtEntranceFee.Text = Schema.GetSetting("entrance_fee");
            txtMaxLoan.Text = Schema.GetSetting("max_loan_multiplier");
            txtInterestRate.Text = Schema.GetSetting("interest_rate");
            txtSavingsTarget.Text = Schema.GetSetting("savings_target");
            txtMinWithdrawal.Text = Schema.GetSetting("min_savings_withdrawal");
            txtGuarantors.Text = Schema.GetSetting("required_guarantors");
            string method = Schema.GetSetting("interest_method");
            cmbInterestMethod.SelectedIndex = method == "Reducing" ? 1 : 0;
            txtLatePenalty.Text = Schema.GetSetting("late_payment_penalty");
            txtAbsentFine.Text = Schema.GetSetting("absent_fine");
        }

        private void LoadUsers()
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"SELECT id, username as Username, full_name as Name, role as Role,
                CASE WHEN is_active=1 THEN 'Yes' ELSE 'No' END as Active,
                COALESCE(last_login, 'Never') as LastLogin FROM users ORDER BY created_at";
            using var reader = cmd.ExecuteReader();
            var dt = new System.Data.DataTable();
            dt.Load(reader);
            dgvUsers.DataSource = dt;
            if (dgvUsers.Columns.Contains("id"))
                dgvUsers.Columns["id"].Visible = false;
        }

        private void AddLabel(TabPage tab, string text, int x, int y)
        {
            AddLabel((Control)tab, text, x, y);
        }

        private void AddLabel(Control parent, string text, int x, int y)
        {
            parent.Controls.Add(new Label
            {
                Text = text,
                Font = new Font("Segoe UI", 10),
                ForeColor = Blue,
                AutoSize = true,
                Top = y,
                Left = x
            });
        }

        private TextBox AddTextBox(TabPage tab, int x, int y, int width)
        {
            return AddTextBox((Control)tab, x, y, width);
        }

        private TextBox AddTextBox(Control parent, int x, int y, int width)
        {
            var txt = new TextBox { Font = new Font("Segoe UI", 10), Width = width, Top = y, Left = x };
            parent.Controls.Add(txt);
            return txt;
        }

        private Button CreateButton(string text, int x, int y, int width, int height)
        {
            var btn = new Button
            {
                Text = text,
                FlatStyle = FlatStyle.Flat,
                BackColor = Blue,
                ForeColor = Color.White,
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
