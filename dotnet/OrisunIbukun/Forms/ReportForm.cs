using System;
using System.Data;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using Microsoft.Data.Sqlite;
using OrisunIbukun.Database;
using OrisunIbukun.Engine;
using OrisunIbukun.Utils;

namespace OrisunIbukun.Forms
{
    public class ReportForm : UserControl
    {
        private static readonly Color Blue = Color.FromArgb(21, 101, 192);
        private static readonly Color LightBlue = Color.FromArgb(227, 242, 253);
        private static readonly Color White = Color.White;

        private readonly string _userId;
        private ListBox lstReports = null!;
        private Panel pnlParams = null!;
        private DataGridView dgvResults = null!;
        private TextBox txtParam1 = null!;
        private TextBox txtParam2 = null!;
        private Label lblParam1 = null!;
        private Label lblParam2 = null!;
        private string _selectedReport = "";

        private readonly string[] _reportTypes = {
            "Monthly Summary",
            "Member Savings Report",
            "Loan Status Report",
            "Outstanding Loans Report",
            "Outstanding Charges Report",
            "Attendance Report",
            "Shares Report",
            "Share Register",
            "Expense Report",
            "Remittance Report",
            "Transaction History",
            "Audit Log Report"
        };

        public ReportForm(string userId)
        {
            _userId = userId;
            BackColor = LightBlue;
            InitializeForm();
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
                Text = "Reports",
                Font = new Font("Segoe UI", 16, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Top = 10,
                Left = 15
            };
            pnlTop.Controls.Add(lblTitle);
            Controls.Add(pnlTop);

            var pnlButtons = new Panel
            {
                Dock = DockStyle.Top,
                Height = 50,
                BackColor = LightBlue
            };

            var btnGenerate = CreateButton("GENERATE", 15, 5, 120, 40);
            btnGenerate.Click += BtnGenerate_Click;
            pnlButtons.Controls.Add(btnGenerate);

            var btnExport = CreateButton("EXPORT CSV", 145, 5, 120, 40);
            btnExport.Click += BtnExport_Click;
            btnExport.BackColor = Color.Green;
            pnlButtons.Controls.Add(btnExport);

            var btnPrint = CreateButton("PRINT", 275, 5, 100, 40);
            btnPrint.Click += BtnPrint_Click;
            btnPrint.BackColor = Color.FromArgb(55, 71, 79);
            pnlButtons.Controls.Add(btnPrint);
            Controls.Add(pnlButtons);

            var panelLeft = new Panel
            {
                Dock = DockStyle.Left,
                Width = 220,
                BackColor = White
            };

            var lblSelect = new Label
            {
                Text = "Report Type",
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Top = 10,
                Left = 10
            };
            panelLeft.Controls.Add(lblSelect);

            lstReports = new ListBox
            {
                Font = new Font("Segoe UI", 10),
                Top = 40,
                Left = 5,
                Width = 210,
                Height = 450,
                Dock = DockStyle.Fill,
                BorderStyle = BorderStyle.None
            };
            foreach (var report in _reportTypes)
                lstReports.Items.Add(report);
            lstReports.SelectedIndexChanged += LstReports_SelectedIndexChanged;
            panelLeft.Controls.Add(lstReports);
            Controls.Add(panelLeft);

            pnlParams = new Panel
            {
                Dock = DockStyle.Top,
                Height = 120,
                BackColor = White
            };

            lblParam1 = new Label
            {
                Text = "Month:",
                Font = new Font("Segoe UI", 10),
                ForeColor = Blue,
                AutoSize = true,
                Top = 10,
                Left = 10
            };
            pnlParams.Controls.Add(lblParam1);

            txtParam1 = new TextBox
            {
                Font = new Font("Segoe UI", 10),
                Width = 180,
                Top = 30,
                Left = 10
            };
            pnlParams.Controls.Add(txtParam1);

            lblParam2 = new Label
            {
                Text = "Year:",
                Font = new Font("Segoe UI", 10),
                ForeColor = Blue,
                AutoSize = true,
                Top = 60,
                Left = 10
            };
            pnlParams.Controls.Add(lblParam2);

            txtParam2 = new TextBox
            {
                Font = new Font("Segoe UI", 10),
                Width = 180,
                Top = 80,
                Left = 10
            };
            pnlParams.Controls.Add(txtParam2);
            Controls.Add(pnlParams);

            dgvResults = new DataGridView
            {
                Dock = DockStyle.Fill,
                BackgroundColor = White,
                BorderStyle = BorderStyle.None,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                ReadOnly = true,
                AllowUserToAddRows = false,
                Font = new Font("Segoe UI", 9)
            };
            Controls.Add(dgvResults);
        }

        private void LstReports_SelectedIndexChanged(object? sender, EventArgs e)
        {
            if (lstReports.SelectedItem == null) return;
            _selectedReport = lstReports.SelectedItem.ToString()!;
            SetParamsForReport(_selectedReport);
        }

        private void SetParamsForReport(string report)
        {
            bool needsParams = report switch
            {
                "Outstanding Loans Report" => false,
                "Outstanding Charges Report" => false,
                "Share Register" => false,
                "Audit Log Report" => false,
                _ => true
            };
            txtParam1.Enabled = needsParams;
            txtParam2.Enabled = needsParams;
            switch (report)
            {
                case "Monthly Summary":
                case "Member Savings Report":
                case "Loan Status Report":
                case "Attendance Report":
                case "Shares Report":
                case "Expense Report":
                case "Remittance Report":
                case "Transaction History":
                    lblParam1.Text = "Month (MM):";
                    lblParam2.Text = "Year (YYYY):";
                    txtParam1.Text = DateTime.Now.ToString("MM");
                    txtParam2.Text = DateTime.Now.ToString("yyyy");
                    break;
                default:
                    lblParam1.Text = "No parameters";
                    lblParam2.Text = "required";
                    txtParam1.Text = "";
                    txtParam2.Text = "";
                    break;
            }
        }

        private void BtnGenerate_Click(object? sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(_selectedReport))
            {
                MessageBox.Show("Select a report type", "Info", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            try
            {
                using var conn = Connection.GetConnection();
                using var cmd = conn.CreateCommand();
                string prefix = $"{txtParam2.Text}-{txtParam1.Text.PadLeft(2, '0')}";

                switch (_selectedReport)
                {
                    case "Monthly Summary":
                        var summary = TransactionEngine.GetMonthlySummary(txtParam1.Text, txtParam2.Text);
                        var dt = new DataTable();
                        dt.Columns.Add("Metric", typeof(string));
                        dt.Columns.Add("Value", typeof(string));
                        dt.Rows.Add("Total Members", summary["TotalMembers"]);
                        dt.Rows.Add("Monthly Savings", Helpers.FormatCurrency(Convert.ToDouble(summary["MonthlySavings"])));
                        dt.Rows.Add("Monthly Shares", Helpers.FormatCurrency(Convert.ToDouble(summary["MonthlyShares"])));
                        dt.Rows.Add("Loans Applied", summary["LoansApplied"]);
                        dt.Rows.Add("Loan Repayments", Helpers.FormatCurrency(Convert.ToDouble(summary["LoanRepayments"])));
                        dt.Rows.Add("Expenses", Helpers.FormatCurrency(Convert.ToDouble(summary["Expenses"])));
                        dt.Rows.Add("Remittances", Helpers.FormatCurrency(Convert.ToDouble(summary["Remittances"])));
                        dgvResults.DataSource = dt;
                        break;

                    case "Member Savings Report":
                        cmd.CommandText = "SELECT m.full_name as Member, m.member_number as Number, COALESCE(SUM(s.amount), 0) as TotalSavings FROM members m LEFT JOIN savings s ON m.id=s.member_id AND s.savings_date LIKE @pfx||'%' WHERE m.status='Active' GROUP BY m.id ORDER BY m.full_name";
                        cmd.Parameters.AddWithValue("@pfx", prefix);
                        LoadQueryResults(cmd);
                        break;

                    case "Loan Status Report":
                        cmd.CommandText = "SELECT m.full_name as Member, l.amount as Amount, l.status as Status, l.applied_date as Applied, l.total_payable as Payable FROM loans l INNER JOIN members m ON l.member_id=m.id ORDER BY l.applied_date DESC";
                        LoadQueryResults(cmd);
                        break;

                    case "Attendance Report":
                        cmd.CommandText = "SELECT mt.meeting_date as Date, mt.meeting_number as Meeting, COUNT(CASE WHEN a.status='Present' THEN 1 END) as Present, COUNT(CASE WHEN a.status='Absent' THEN 1 END) as Absent FROM meetings mt LEFT JOIN attendance a ON mt.id=a.meeting_id WHERE mt.meeting_date LIKE @pfx||'%' GROUP BY mt.id ORDER BY mt.meeting_date";
                        cmd.Parameters.AddWithValue("@pfx", prefix);
                        LoadQueryResults(cmd);
                        break;

                    case "Shares Report":
                        cmd.CommandText = "SELECT m.full_name as Member, SUM(sh.shares_count) as Shares, SUM(sh.amount) as Amount FROM shares sh INNER JOIN members m ON sh.member_id=m.id WHERE sh.share_date LIKE @pfx||'%' GROUP BY sh.member_id ORDER BY m.full_name";
                        cmd.Parameters.AddWithValue("@pfx", prefix);
                        LoadQueryResults(cmd);
                        break;

                    case "Expense Report":
                        cmd.CommandText = "SELECT description as Description, amount as Amount, category as Category, expense_date as Date FROM expenses WHERE expense_date LIKE @pfx||'%' ORDER BY expense_date";
                        cmd.Parameters.AddWithValue("@pfx", prefix);
                        LoadQueryResults(cmd);
                        break;

                    case "Remittance Report":
                        cmd.CommandText = "SELECT amount as Amount, description as Description, remittance_date as Date FROM headquarters_remittances WHERE remittance_date LIKE @pfx||'%' ORDER BY remittance_date";
                        cmd.Parameters.AddWithValue("@pfx", prefix);
                        LoadQueryResults(cmd);
                        break;

                    case "Transaction History":
                        cmd.CommandText = "SELECT m.full_name as Member, t.type as Type, t.amount as Amount, t.description as Description, t.transaction_date as Date FROM transactions t INNER JOIN members m ON t.member_id=m.id WHERE t.transaction_date LIKE @pfx||'%' ORDER BY t.transaction_date";
                        cmd.Parameters.AddWithValue("@pfx", prefix);
                        LoadQueryResults(cmd);
                        break;

                    case "Outstanding Loans Report":
                        cmd.CommandText = @"SELECT l.id as [Loan ID], m.full_name as Member, l.amount as Principal,
                            l.total_payable as Payable,
                            (SELECT COALESCE(SUM(amount), 0) FROM loan_repayments WHERE loan_id=l.id) as Paid,
                            l.total_payable - (SELECT COALESCE(SUM(amount), 0) FROM loan_repayments WHERE loan_id=l.id) as Outstanding,
                            l.status as Status, l.applied_date as Applied
                            FROM loans l INNER JOIN members m ON l.member_id=m.id
                            WHERE l.status IN ('Approved','Disbursed') ORDER BY l.applied_date DESC";
                        LoadQueryResults(cmd);
                        break;

                    case "Outstanding Charges Report":
                        cmd.CommandText = @"SELECT m.full_name as Member, c.charge_type as Type, c.description as Description,
                            c.amount as Billed, c.amount_paid as Paid,
                            c.amount - c.amount_paid as Owed, c.status as Status
                            FROM member_charges c INNER JOIN members m ON c.member_id=m.id
                            WHERE c.status != 'Paid' ORDER BY m.full_name";
                        LoadQueryResults(cmd);
                        break;

                    case "Share Register":
                        cmd.CommandText = @"SELECT m.member_number as Number, m.full_name as Member,
                            COALESCE(SUM(sh.shares_count), 0) as Shares,
                            COALESCE(SUM(sh.amount), 0) as Value
                            FROM members m LEFT JOIN shares sh ON sh.member_id=m.id
                            WHERE m.status='Active' GROUP BY m.id ORDER BY m.full_name";
                        LoadQueryResults(cmd);
                        break;

                    case "Audit Log Report":
                        cmd.CommandText = @"SELECT a.created_at as Timestamp, COALESCE(u.username, '') as User,
                            a.action as Action, COALESCE(a.new_value, '') as Details
                            FROM audit_logs a LEFT JOIN users u ON a.user_id=u.id
                            ORDER BY a.created_at DESC LIMIT 500";
                        LoadQueryResults(cmd);
                        break;
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void LoadQueryResults(SqliteCommand cmd)
        {
            using var reader = cmd.ExecuteReader();
            var dt = new DataTable();
            dt.Load(reader);
            dgvResults.DataSource = dt;
        }

        private void BtnExport_Click(object? sender, EventArgs e)
        {
            if (dgvResults.DataSource == null) return;

            using var sfd = new SaveFileDialog
            {
                Filter = "CSV files (*.csv)|*.csv",
                FileName = $"Report_{_selectedReport.Replace(" ", "_")}_{Helpers.TodayStr()}.csv"
            };

            if (sfd.ShowDialog() == DialogResult.OK)
            {
                try
                {
                    var dt = (DataTable)dgvResults.DataSource;
                    using var sw = new StreamWriter(sfd.FileName);

                    foreach (DataColumn col in dt.Columns)
                        sw.Write($"{col.ColumnName},");
                    sw.WriteLine();

                    foreach (DataRow row in dt.Rows)
                    {
                        foreach (var item in row.ItemArray)
                            sw.Write($"\"{item}\",");
                        sw.WriteLine();
                    }

                    MessageBox.Show("Exported successfully!", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Error: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void BtnPrint_Click(object? sender, EventArgs e)
        {
            if (dgvResults.DataSource == null || dgvResults.Rows.Count == 0)
            {
                MessageBox.Show("Generate a report first.", "Info", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            using var pd = new System.Drawing.Printing.PrintDocument();
            pd.PrintPage += (s, ev) =>
            {
                var g = ev.Graphics!;
                float y = 40;
                float left = 40;
                g.DrawString("ORISUN IBUKUN", new Font("Segoe UI", 16, FontStyle.Bold), System.Drawing.Brushes.DarkBlue, left, y);
                y += 32;
                g.DrawString(_selectedReport, new Font("Segoe UI", 12), System.Drawing.Brushes.Black, left, y);
                y += 24;
                g.DrawString($"Generated: {DateTime.Now:yyyy-MM-dd HH:mm}", new Font("Segoe UI", 9), System.Drawing.Brushes.Gray, left, y);
                y += 28;

                float x = left;
                float colW = (ev.MarginBounds.Width - 40) / Math.Max(1, dgvResults.Columns.Count);
                var headerFont = new Font("Segoe UI", 9, FontStyle.Bold);
                var cellFont = new Font("Segoe UI", 9);
                foreach (DataGridViewColumn col in dgvResults.Columns)
                {
                    if (!col.Visible) continue;
                    g.DrawString(col.HeaderText, headerFont, System.Drawing.Brushes.DarkBlue, x, y);
                    x += colW;
                }
                y += 22;
                g.DrawLine(System.Drawing.Pens.DarkBlue, left, y, left + ev.MarginBounds.Width - 40, y);
                y += 8;

                foreach (DataGridViewRow row in dgvResults.Rows)
                {
                    if (y > ev.MarginBounds.Bottom - 30) { ev.HasMorePages = true; return; }
                    x = left;
                    foreach (DataGridViewCell cell in row.Cells)
                    {
                        if (!dgvResults.Columns[cell.ColumnIndex].Visible) continue;
                        g.DrawString(cell.Value?.ToString() ?? "", cellFont, System.Drawing.Brushes.Black,
                            new RectangleF(x, y, colW, 20));
                        x += colW;
                    }
                    y += 20;
                }
                ev.HasMorePages = false;
            };
            using var preview = new PrintPreviewDialog { Document = pd, Width = 900, Height = 700 };
            preview.ShowDialog(this);
        }

        private Button CreateButton(string text, int x, int y, int width, int height)
        {
            var btn = new Button
            {
                Text = text,
                FlatStyle = FlatStyle.Flat,
                BackColor = Blue,
                ForeColor = Color.White,
                Font = new Font("Segoe UI", 9, FontStyle.Bold),
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
