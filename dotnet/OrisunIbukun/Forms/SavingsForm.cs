using System;
using System.Data;
using System.Drawing;
using System.Windows.Forms;
using Microsoft.Data.Sqlite;
using OrisunIbukun.Database;
using OrisunIbukun.Engine;
using OrisunIbukun.Utils;

namespace OrisunIbukun.Forms
{
    public class SavingsForm : UserControl
    {
        private static readonly Color Blue = Color.FromArgb(21, 101, 192);
        private static readonly Color LightBlue = Color.FromArgb(227, 242, 253);
        private static readonly Color White = Color.White;

        private readonly string _userId;
        private TextBox txtSearch = null!;
        private ListBox lstMembers = null!;
        private Label lblMemberName = null!;
        private Label lblMemberId = null!;
        private Label lblSavingsBalance = null!;
        private Label lblTotalShares = null!;
        private TextBox txtAmount = null!;
        private ComboBox cboMethod = null!;
        private DateTimePicker dtpDate = null!;
        private Label lblMsg = null!;
        private DataGridView dgvBooklet = null!;
        private string _selectedMemberId = "";
        private double _lastNewSavings = -1;
        private double _lastNewShares = -1;

        public SavingsForm(string userId)
        {
            _userId = userId;
            BackColor = LightBlue;
            InitializeForm();
        }

        private void InitializeForm()
        {
            BackColor = LightBlue;

            var pnlTop = new Panel
            {
                Dock = DockStyle.Top,
                Height = 50,
                BackColor = LightBlue
            };

            var lblTitle = new Label
            {
                Text = "Record Savings",
                Font = new Font("Segoe UI", 18, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Top = 10,
                Left = 20
            };
            pnlTop.Controls.Add(lblTitle);
            Controls.Add(pnlTop);

            var pnlLeft = new Panel
            {
                Dock = DockStyle.Left,
                Width = 500,
                BackColor = LightBlue,
                AutoScroll = true
            };

            var lblSearch = new Label
            {
                Text = "Search Member:",
                Font = new Font("Segoe UI", 11),
                ForeColor = Blue,
                AutoSize = true,
                Top = 10,
                Left = 10
            };
            pnlLeft.Controls.Add(lblSearch);

            txtSearch = new TextBox
            {
                Font = new Font("Segoe UI", 11),
                Width = 320,
                Top = 7,
                Left = 130,
                PlaceholderText = "Search by name, ID, or phone..."
            };
            txtSearch.TextChanged += TxtSearch_TextChanged;
            pnlLeft.Controls.Add(txtSearch);

            lstMembers = new ListBox
            {
                Font = new Font("Segoe UI", 10),
                Width = 460,
                Height = 80,
                Top = 42,
                Left = 10
            };
            lstMembers.SelectedIndexChanged += LstMembers_SelectedIndexChanged;
            pnlLeft.Controls.Add(lstMembers);

            var panelInfo = new Panel
            {
                Top = 130,
                Left = 10,
                Width = 470,
                Height = 120,
                BackColor = White,
                BorderStyle = BorderStyle.FixedSingle
            };

            lblMemberName = new Label
            {
                Text = "No member selected",
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Top = 10,
                Left = 12
            };

            lblMemberId = new Label
            {
                Text = "",
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.Gray,
                AutoSize = true,
                Top = 35,
                Left = 12
            };

            lblSavingsBalance = new Label
            {
                Text = "Savings Balance: " + Helpers.FormatCurrency(0),
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.Green,
                AutoSize = true,
                Top = 60,
                Left = 12
            };

            lblTotalShares = new Label
            {
                Text = "Total Shares: " + Helpers.FormatCurrency(0),
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.FromArgb(194, 123, 16),
                AutoSize = true,
                Top = 85,
                Left = 12
            };

            panelInfo.Controls.Add(lblMemberName);
            panelInfo.Controls.Add(lblMemberId);
            panelInfo.Controls.Add(lblSavingsBalance);
            panelInfo.Controls.Add(lblTotalShares);
            pnlLeft.Controls.Add(panelInfo);

            var lblSplitNote = new Label
            {
                Text = "Note: Savings are automatically split 50% Savings / 50% Shares",
                Font = new Font("Segoe UI", 9, FontStyle.Italic),
                ForeColor = Color.FromArgb(120, 120, 120),
                AutoSize = true,
                Top = 258,
                Left = 10
            };
            pnlLeft.Controls.Add(lblSplitNote);

            int y = 285;
            AddLabel(pnlLeft, "Amount:", 10, y);
            txtAmount = AddTextBox(pnlLeft, 130, y, 200);
            y += 40;

            AddLabel(pnlLeft, "Payment Method:", 10, y);
            cboMethod = new ComboBox
            {
                Font = new Font("Segoe UI", 11),
                Width = 200,
                Top = y,
                Left = 130,
                DropDownStyle = ComboBoxStyle.DropDownList
            };
            cboMethod.Items.AddRange(new object[] { "Cash", "Bank Transfer", "Mobile" });
            cboMethod.SelectedIndex = 0;
            pnlLeft.Controls.Add(cboMethod);
            y += 40;

            AddLabel(pnlLeft, "Date:", 10, y);
            dtpDate = new DateTimePicker
            {
                Font = new Font("Segoe UI", 11),
                Width = 200,
                Top = y,
                Left = 130,
                Format = DateTimePickerFormat.Short,
                Value = DateTime.Now
            };
            pnlLeft.Controls.Add(dtpDate);
            y += 50;

            var btnRecord = new Button
            {
                Text = "RECORD SAVINGS",
                FlatStyle = FlatStyle.Flat,
                BackColor = Blue,
                ForeColor = White,
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                Width = 250,
                Height = 50,
                Top = y,
                Left = 130,
                Cursor = Cursors.Hand
            };
            btnRecord.FlatAppearance.BorderSize = 0;
            btnRecord.Click += BtnRecord_Click;
            pnlLeft.Controls.Add(btnRecord);

            lblMsg = new Label
            {
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Top = y + 55,
                Left = 130
            };
            pnlLeft.Controls.Add(lblMsg);
            Controls.Add(pnlLeft);

            var pnlRight = new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = LightBlue
            };

            var lblBooklet = new Label
            {
                Text = "Savings Booklet",
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Top = 10,
                Left = 10
            };
            pnlRight.Controls.Add(lblBooklet);

            dgvBooklet = new DataGridView
            {
                Top = 40,
                Left = 10,
                Width = 500,
                Height = 500,
                Dock = DockStyle.Fill,
                BackgroundColor = White,
                BorderStyle = BorderStyle.None,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                MultiSelect = false,
                ReadOnly = true,
                AllowUserToAddRows = false,
                Font = new Font("Segoe UI", 9)
            };
            dgvBooklet.ColumnHeadersDefaultCellStyle.BackColor = Blue;
            dgvBooklet.ColumnHeadersDefaultCellStyle.ForeColor = White;
            dgvBooklet.ColumnHeadersDefaultCellStyle.Font = new Font("Segoe UI", 10, FontStyle.Bold);
            dgvBooklet.EnableHeadersVisualStyles = false;
            dgvBooklet.RowHeadersVisible = false;
            pnlRight.Controls.Add(dgvBooklet);
            Controls.Add(pnlRight);
        }

private void TxtSearch_TextChanged(object? sender, EventArgs e)
        {
            string search = txtSearch.Text.Trim();
            lstMembers.Items.Clear();
            if (search.Length < 2) return;

            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"SELECT id, full_name, member_number, phone
                FROM members
                WHERE (full_name LIKE @s OR member_number LIKE @s OR phone LIKE @s)
                AND status='Active' ORDER BY full_name LIMIT 20";
            cmd.Parameters.AddWithValue("@s", $"%{search}%");
            using var reader = cmd.ExecuteReader();

            bool any = false;
            while (reader.Read())
            {
                any = true;
                lstMembers.Items.Add(new MemberPick(
                    reader.GetString(0),
                    reader.GetString(1),
                    reader.GetString(2),
                    $"{reader.GetString(1)} | {reader.GetString(2)} | {reader.GetString(3)}"));
            }

            if (any)
            {
                lstMembers.SelectedIndex = 0;
            }
            else
            {
                _selectedMemberId = "";
                lblMemberName.Text = "No member found";
                lblMemberId.Text = "";
                lblSavingsBalance.Text = "Savings Balance: " + Helpers.FormatCurrency(0);
                lblTotalShares.Text = "Total Shares: " + Helpers.FormatCurrency(0);
                dgvBooklet.DataSource = null;
            }
        }

        private void LstMembers_SelectedIndexChanged(object? sender, EventArgs e)
        {
            if (lstMembers.SelectedItem is MemberPick pick)
            {
                _selectedMemberId = pick.Id;
                lblMemberName.Text = pick.Name;
                lblMemberId.Text = $"Member ID: {pick.Number}";
                LoadMemberFinancials();
                LoadBooklet();
                lblMsg.Text = "";
            }
        }

        private sealed class MemberPick
        {
            public string Id; public string Name; public string Number; public string Display;
            public MemberPick(string id, string name, string number, string display)
            { Id = id; Name = name; Number = number; Display = display; }
            public override string ToString() => Display;
        }

        private void LoadMemberFinancials()
        {
            if (string.IsNullOrEmpty(_selectedMemberId)) return;

            var summary = TransactionEngine.GetMemberFinancialSummary(_selectedMemberId);
            double savings = Convert.ToDouble(summary["TotalSavings"]);
            double shares = Convert.ToDouble(summary["TotalShares"]);

            lblSavingsBalance.Text = "Savings Balance: " + Helpers.FormatCurrency(savings);
            lblTotalShares.Text = "Total Shares: " + Helpers.FormatCurrency(shares);
        }

        private void LoadBooklet()
        {
            if (string.IsNullOrEmpty(_selectedMemberId)) return;

            var dt = new DataTable();
            dt.Columns.Add("Date", typeof(string));
            dt.Columns.Add("Type", typeof(string));
            dt.Columns.Add("Amount", typeof(string));
            dt.Columns.Add("Balance", typeof(string));

            using (var conn = Connection.GetConnection())
            {
                using (var cmd = conn.CreateCommand())
                {
                    cmd.CommandText = @"SELECT savings_date, amount, balance 
                        FROM savings WHERE member_id=@mid ORDER BY savings_date DESC";
                    cmd.Parameters.AddWithValue("@mid", _selectedMemberId);
                    using var reader = cmd.ExecuteReader();
                    while (reader.Read())
                    {
                        dt.Rows.Add(
                            reader.GetString(0),
                            "Savings",
                            Helpers.FormatCurrency(reader.GetDouble(1)),
                            Helpers.FormatCurrency(reader.GetDouble(2))
                        );
                    }
                }
            }

            using (var conn = Connection.GetConnection())
            {
                using (var cmd = conn.CreateCommand())
                {
                    cmd.CommandText = @"SELECT share_date, amount 
                        FROM shares WHERE member_id=@mid ORDER BY share_date DESC";
                    cmd.Parameters.AddWithValue("@mid", _selectedMemberId);
                    using var reader = cmd.ExecuteReader();
                    while (reader.Read())
                    {
                        dt.Rows.Add(
                            reader.GetString(0),
                            "Shares",
                            Helpers.FormatCurrency(reader.GetDouble(1)),
                            "-"
                        );
                    }
                }
            }

            DataView dv = dt.DefaultView;
            dv.Sort = "Date DESC";
            dgvBooklet.DataSource = dv.ToTable();
        }

        private void BtnRecord_Click(object? sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(_selectedMemberId))
            {
                lblMsg.ForeColor = Color.Red;
                lblMsg.Text = "Please select a member first.";
                return;
            }

            var (valid, amount) = Validators.ValidateAmount(txtAmount.Text);
            if (!valid)
            {
                lblMsg.ForeColor = Color.Red;
                lblMsg.Text = "Please enter a valid amount.";
                return;
            }

            string method = cboMethod.SelectedItem?.ToString() ?? "Cash";
            string savingsDate = dtpDate.Value.ToString("yyyy-MM-dd");

            var summary = TransactionEngine.GetMemberFinancialSummary(_selectedMemberId);
            double oldSavings = Convert.ToDouble(summary["TotalSavings"]);
            double oldShares = Convert.ToDouble(summary["TotalShares"]);

            TransactionEngine.RecordSavings(_selectedMemberId, amount, method, "", _userId, savingsDate);

            var newSummary = TransactionEngine.GetMemberFinancialSummary(_selectedMemberId);
            _lastNewSavings = Convert.ToDouble(newSummary["TotalSavings"]);
            _lastNewShares = Convert.ToDouble(newSummary["TotalShares"]);

            double savingsAdded = _lastNewSavings - oldSavings;
            double sharesAdded = _lastNewShares - oldShares;

            lblMsg.ForeColor = Color.Green;
            lblMsg.Text = $"Savings recorded! Savings: {Helpers.FormatCurrency(_lastNewSavings)} (+{Helpers.FormatCurrency(savingsAdded)}) | Shares: {Helpers.FormatCurrency(_lastNewShares)} (+{Helpers.FormatCurrency(sharesAdded)})";
            MessageBox.Show($"Savings of {Helpers.FormatCurrency(amount)} recorded.\nNew Savings Balance: {Helpers.FormatCurrency(_lastNewSavings)}",
                "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);

            txtAmount.Text = "";
            lblSavingsBalance.Text = "Savings Balance: " + Helpers.FormatCurrency(_lastNewSavings);
            lblTotalShares.Text = "Total Shares: " + Helpers.FormatCurrency(_lastNewShares);
            LoadBooklet();
        }

        private void AddLabel(Panel panel, string text, int x, int y)
        {
            panel.Controls.Add(new Label
            {
                Text = text,
                Font = new Font("Segoe UI", 11),
                ForeColor = Blue,
                AutoSize = true,
                Top = y,
                Left = x
            });
        }

        private TextBox AddTextBox(Panel panel, int x, int y, int width)
        {
            var txt = new TextBox
            {
                Font = new Font("Segoe UI", 11),
                Width = width,
                Top = y,
                Left = x
            };
            panel.Controls.Add(txt);
            return txt;
        }
    }
}
