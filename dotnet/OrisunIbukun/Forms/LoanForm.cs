using System;
using System.Data;
using System.Drawing;
using System.Windows.Forms;
using OrisunIbukun.Database;
using OrisunIbukun.Engine;
using OrisunIbukun.Utils;

namespace OrisunIbukun.Forms
{
    public class LoanForm : UserControl
    {
        private static readonly Color Blue = Color.FromArgb(21, 101, 192);
        private static readonly Color LightBlue = Color.FromArgb(227, 242, 253);
        private static readonly Color White = Color.White;

        private readonly string _userId;
        private readonly string _userRole;
        private TabControl tabControl = null!;

        private TextBox txtSearchNew = null!;
        private ListBox lstMembersNew = null!;
        private Label lblLoanMember = null!;
        private TextBox txtLoanAmount = null!;
        private TextBox txtInterest = null!;
        private TextBox txtPurpose = null!;
        private TextBox txtLoanDate = null!;
        private Label lblNewMsg = null!;
        private string _newLoanMemberId = "";
        private string _detailLoanId = "";

        private Label lblLoanDetail = null!;
        private DataGridView dgvGuarantors = null!;
        private Button btnAddGuarantor = null!;
        private Button btnApprove = null!;
        private Button btnDisburse = null!;

        private TextBox txtSearchRepay = null!;
        private ListBox lstMembersRepay = null!;
        private Label lblRepayMember = null!;
        private DataGridView dgvActiveLoans = null!;
        private TextBox txtRepayAmount = null!;
        private TextBox txtRepayDate = null!;
        private Label lblRepayMsg = null!;
        private string _repayLoanId = "";
        private string _repayMemberId = "";

        private ComboBox cmbStatusFilter = null!;
        private DataGridView dgvAllLoans = null!;

        public LoanForm(string userId, string role = "")
        {
            _userId = userId;
            _userRole = string.IsNullOrEmpty(role) ? GetUserRole(userId) : role;
            BackColor = LightBlue;
            InitializeForm();
        }

        private static string GetUserRole(string userId)
        {
            try
            {
                using var conn = Connection.GetConnection();
                using var cmd = conn.CreateCommand();
                cmd.CommandText = "SELECT role FROM users WHERE id=@id";
                cmd.Parameters.AddWithValue("@id", userId);
                return cmd.ExecuteScalar()?.ToString() ?? "";
            }
            catch { return ""; }
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
                Text = "Loan Management",
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

            var tabNew = new TabPage("New Loan");
            var tabRepay = new TabPage("Loan Repayments");
            var tabAll = new TabPage("All Loans");

            BuildNewLoanTab(tabNew);
            BuildRepaymentsTab(tabRepay);
            BuildAllLoansTab(tabAll);

            tabControl.TabPages.AddRange(new[] { tabNew, tabRepay, tabAll });
            Controls.Add(tabControl);
        }

        private void BuildNewLoanTab(TabPage tab)
        {
            var pnlApply = new Panel
            {
                Dock = DockStyle.Left,
                Width = 470,
                BackColor = White,
                AutoScroll = true,
                Padding = new Padding(15)
            };

            int y = 10;
            AddLabel(pnlApply, "Search Member:", 15, y);
            txtSearchNew = AddTextBox(pnlApply, 15, y + 25, 280);
            txtSearchNew.TextChanged += (s, e) => SearchMembers(txtSearchNew, lstMembersNew);
            var btnSearchNew = CreateButton("Search", 305, y + 23, 90, 32);
            btnSearchNew.Click += (s, e) => SearchMembers(txtSearchNew, lstMembersNew);
            pnlApply.Controls.Add(btnSearchNew);
            y += 65;

            lstMembersNew = new ListBox
            {
                Location = new Point(15, y),
                Size = new Size(380, 70),
                Font = new Font("Segoe UI", 10)
            };
            lstMembersNew.SelectedIndexChanged += (s, e) =>
            {
                if (lstMembersNew.SelectedItem is MemberItem mi)
                {
                    _newLoanMemberId = mi.Id;
                    lblLoanMember.Text = $"{mi.Name} ({mi.Number})";
                }
            };
            pnlApply.Controls.Add(lstMembersNew);
            y += 80;

            lblLoanMember = new Label
            {
                Text = "No member selected",
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(15, y)
            };
            pnlApply.Controls.Add(lblLoanMember);
            y += 32;

            AddLabel(pnlApply, "Principal Amount (₦):", 15, y);
            txtLoanAmount = AddTextBox(pnlApply, 15, y + 25, 200);
            y += 65;

            AddLabel(pnlApply, "Interest Rate (%):", 15, y);
            txtInterest = AddTextBox(pnlApply, 15, y + 25, 100);
            txtInterest.Text = Schema.GetSetting("interest_rate");
            if (string.IsNullOrEmpty(txtInterest.Text)) txtInterest.Text = "5";
            y += 65;

            AddLabel(pnlApply, "Purpose:", 15, y);
            txtPurpose = AddTextBox(pnlApply, 15, y + 25, 380);
            y += 65;

            AddLabel(pnlApply, "Date:", 15, y);
            txtLoanDate = AddTextBox(pnlApply, 15, y + 25, 150);
            txtLoanDate.Text = Helpers.TodayStr();
            y += 65;

            var btnSubmit = CreateButton("Submit Application", 15, y, 200, 42);
            btnSubmit.Click += BtnSubmitLoan_Click;
            pnlApply.Controls.Add(btnSubmit);
            y += 52;

            lblNewMsg = new Label
            {
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Location = new Point(15, y)
            };
            pnlApply.Controls.Add(lblNewMsg);
            tab.Controls.Add(pnlApply);

            var pnlDetail = new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = White,
                AutoScroll = true,
                Padding = new Padding(15)
            };

            pnlDetail.Controls.Add(new Label
            {
                Text = "Loan Detail / Guarantors",
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(15, 10)
            });

            lblLoanDetail = new Label
            {
                Text = "Submit or select a loan to see details.",
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.FromArgb(80, 80, 80),
                AutoSize = false,
                Location = new Point(15, 42),
                Size = new Size(420, 190)
            };
            pnlDetail.Controls.Add(lblLoanDetail);

            pnlDetail.Controls.Add(new Label
            {
                Text = "Guarantors",
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(15, 240)
            });

            dgvGuarantors = CreateGrid();
            dgvGuarantors.Location = new Point(15, 266);
            dgvGuarantors.Size = new Size(420, 150);
            dgvGuarantors.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            pnlDetail.Controls.Add(dgvGuarantors);

            btnAddGuarantor = CreateButton("Add Guarantor", 15, 425, 140, 36);
            btnAddGuarantor.Click += (s, e) => OpenAddGuarantorDialog();
            pnlDetail.Controls.Add(btnAddGuarantor);

            btnApprove = CreateButton("Approve Loan", 165, 425, 130, 36);
            btnApprove.BackColor = Color.FromArgb(46, 125, 50);
            btnApprove.Click += BtnApprove_Click;
            pnlDetail.Controls.Add(btnApprove);

            btnDisburse = CreateButton("Disburse Loan", 305, 425, 130, 36);
            btnDisburse.BackColor = Color.FromArgb(230, 81, 0);
            btnDisburse.Click += BtnDisburse_Click;
            pnlDetail.Controls.Add(btnDisburse);

            tab.Controls.Add(pnlDetail);
        }

        private void SearchMembers(TextBox txt, ListBox lst)
        {
            lst.Items.Clear();
            if (txt.Text.Trim().Length < 2) return;
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"SELECT id, full_name, member_number, phone FROM members
                WHERE (full_name LIKE @s OR member_number LIKE @s OR phone LIKE @s) AND status='Active'
                ORDER BY full_name LIMIT 20";
            cmd.Parameters.AddWithValue("@s", $"%{txt.Text.Trim()}%");
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                lst.Items.Add(new MemberItem(
                    reader["id"]!.ToString()!,
                    reader["full_name"]!.ToString()!,
                    reader["member_number"]!.ToString()!,
                    $"{reader["full_name"]} | {reader["member_number"]} | {reader["phone"]}"));
            }
        }

        private sealed class MemberItem
        {
            public string Id; public string Name; public string Number; public string Display;
            public MemberItem(string id, string name, string number, string display)
            { Id = id; Name = name; Number = number; Display = display; }
            public override string ToString() => Display;
        }

        private void BtnSubmitLoan_Click(object? sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(_newLoanMemberId))
            {
                lblNewMsg.ForeColor = Color.Red;
                lblNewMsg.Text = "Please select a member";
                return;
            }

            var (valid, amount) = Validators.ValidateAmount(txtLoanAmount.Text);
            if (!valid)
            {
                lblNewMsg.ForeColor = Color.Red;
                lblNewMsg.Text = "Enter a valid amount greater than zero";
                return;
            }

            if (!double.TryParse(txtInterest.Text, out double rate)) rate = 0;
            string date = string.IsNullOrWhiteSpace(txtLoanDate.Text) ? Helpers.TodayStr() : txtLoanDate.Text.Trim();
            var (validDate, dateErr) = Validators.ValidateDate(date, "Date");
            if (!validDate) { lblNewMsg.ForeColor = Color.Red; lblNewMsg.Text = dateErr; return; }

            var btn = (Button)sender!;
            btn.Enabled = false;
            btn.Text = "Submitting...";
            try
            {
                string loanId = TransactionEngine.CreateLoan(_newLoanMemberId, amount, rate, txtPurpose.Text.Trim(), date);
                TransactionEngine.LogAudit(_userId, "Loan Application", $"Loan application submitted for member {_newLoanMemberId}, amount {Helpers.FormatCurrency(amount)}");
                lblNewMsg.ForeColor = Color.Green;
                lblNewMsg.Text = "Loan application submitted!";
                txtLoanAmount.Text = "";
                txtPurpose.Text = "";
                _detailLoanId = loanId;
                LoadLoanDetail(loanId);
                LoadAllLoans();
            }
            finally
            {
                btn.Enabled = true;
                btn.Text = "Submit Application";
            }
        }

        private void LoadLoanDetail(string loanId)
        {
            _detailLoanId = loanId;
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"SELECT l.*, m.full_name, m.member_number FROM loans l
                INNER JOIN members m ON l.member_id=m.id WHERE l.id=@id";
            cmd.Parameters.AddWithValue("@id", loanId);
            using var reader = cmd.ExecuteReader();
            if (!reader.Read())
            {
                lblLoanDetail.Text = "Loan not found.";
                btnApprove.Enabled = false;
                btnDisburse.Enabled = false;
                return;
            }

            double amount = Convert.ToDouble(reader["amount"]);
            double rate = Convert.ToDouble(reader["interest_rate"]);
            double payable = Convert.ToDouble(reader["total_payable"]);
            string status = reader["status"]!.ToString()!;

            double repaid;
            using (var c2 = conn.CreateCommand())
            {
                c2.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM loan_repayments WHERE loan_id=@id";
                c2.Parameters.AddWithValue("@id", loanId);
                repaid = Convert.ToDouble(c2.ExecuteScalar());
            }
            double outstanding = payable - repaid;
            if (outstanding < 0) outstanding = 0;

            lblLoanDetail.Text =
                $"Member: {reader["full_name"]} ({reader["member_number"]})\n" +
                $"Principal: {Helpers.FormatCurrency(amount)}   Interest: {rate:N2}% ({Helpers.FormatCurrency(amount * rate / 100)})\n" +
                $"Total Repayable: {Helpers.FormatCurrency(payable)}   Outstanding: {Helpers.FormatCurrency(outstanding)}\n" +
                $"Status: {status}\n" +
                $"Applied: {reader["applied_date"]}   Approved: {reader["approved_date"]}   Disbursed: {reader["disbursed_date"]}\n" +
                $"Purpose: {reader["purpose"]}";

            btnApprove.Enabled = status == "Pending" && _userRole == "Administrator";
            btnDisburse.Enabled = status == "Approved";
            LoadGuarantors(loanId);
        }

        private void LoadGuarantors(string loanId)
        {
            var dt = new DataTable();
            dt.Columns.Add("Guarantor");
            dt.Columns.Add("Amount");
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"SELECT m.full_name, lg.guarantee_amount FROM loan_guarantors lg
                INNER JOIN members m ON lg.member_id=m.id WHERE lg.loan_id=@id";
            cmd.Parameters.AddWithValue("@id", loanId);
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
                dt.Rows.Add(reader["full_name"]!.ToString()!, Helpers.FormatCurrency(Convert.ToDouble(reader["guarantee_amount"])));
            dgvGuarantors.DataSource = dt;
        }

        private void OpenAddGuarantorDialog()
        {
            if (string.IsNullOrEmpty(_detailLoanId))
            {
                MessageBox.Show("Submit or select a loan first.", "No Loan", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            using var dlg = new Form
            {
                Text = "Add Guarantor",
                Size = new Size(430, 380),
                StartPosition = FormStartPosition.CenterParent,
                FormBorderStyle = FormBorderStyle.FixedDialog,
                MaximizeBox = false,
                MinimizeBox = false
            };
            dlg.Controls.Add(new Label { Text = "Search Member:", Font = new Font("Segoe UI", 11), ForeColor = Blue, AutoSize = true, Location = new Point(20, 15) });
            var txt = new TextBox { Font = new Font("Segoe UI", 11), Width = 370, Location = new Point(20, 42) };
            dlg.Controls.Add(txt);
            var lst = new ListBox { Font = new Font("Segoe UI", 10), Width = 370, Height = 110, Location = new Point(20, 75) };
            dlg.Controls.Add(lst);
            txt.TextChanged += (s, e) =>
            {
                lst.Items.Clear();
                if (txt.Text.Trim().Length < 2) return;
                using var conn = Connection.GetConnection();
                using var cmd = conn.CreateCommand();
                cmd.CommandText = @"SELECT id, full_name, member_number FROM members
                    WHERE (full_name LIKE @s OR member_number LIKE @s) AND status='Active' ORDER BY full_name LIMIT 20";
                cmd.Parameters.AddWithValue("@s", $"%{txt.Text.Trim()}%");
                using var reader = cmd.ExecuteReader();
                while (reader.Read())
                    lst.Items.Add(new MemberItem(reader["id"]!.ToString()!, reader["full_name"]!.ToString()!,
                        reader["member_number"]!.ToString()!, $"{reader["full_name"]} ({reader["member_number"]})"));
            };
            dlg.Controls.Add(new Label { Text = "Guarantee Amount:", Font = new Font("Segoe UI", 11), ForeColor = Blue, AutoSize = true, Location = new Point(20, 200) });
            var txtAmt = new TextBox { Font = new Font("Segoe UI", 11), Width = 200, Location = new Point(20, 227), Text = "0" };
            dlg.Controls.Add(txtAmt);
            var btnAdd = CreateButton("Add", 20, 270, 120, 38);
            btnAdd.Click += (s, e) =>
            {
                if (lst.SelectedItem is not MemberItem mi)
                { MessageBox.Show("Select a guarantor.", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
                double.TryParse(txtAmt.Text, out double amt);
                TransactionEngine.AddGuarantor(_detailLoanId, mi.Id, amt);
                TransactionEngine.LogAudit(_userId, "Add Guarantor", $"Guarantor {mi.Name} added to loan {_detailLoanId}");
                LoadGuarantors(_detailLoanId);
                dlg.Close();
            };
            dlg.Controls.Add(btnAdd);
            dlg.ShowDialog(this);
        }

        private void BtnApprove_Click(object? sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(_detailLoanId)) return;
            if (_userRole != "Administrator")
            {
                MessageBox.Show("Only Administrators can approve loans.", "Permission Denied", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            TransactionEngine.ApproveLoan(_detailLoanId, _userId);
            TransactionEngine.LogAudit(_userId, "Approve Loan", $"Loan {_detailLoanId} approved");
            LoadLoanDetail(_detailLoanId);
            LoadAllLoans();
            MessageBox.Show("Loan approved.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void BtnDisburse_Click(object? sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(_detailLoanId)) return;
            TransactionEngine.DisburseLoan(_detailLoanId, _userId);
            TransactionEngine.LogAudit(_userId, "Disburse Loan", $"Loan {_detailLoanId} disbursed");
            LoadLoanDetail(_detailLoanId);
            LoadAllLoans();
            MessageBox.Show("Loan disbursed.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void BuildRepaymentsTab(TabPage tab)
        {
            int y = 20;
            AddLabel(tab, "Search Member:", 20, y);
            txtSearchRepay = AddTextBox(tab, 160, y, 280);
            txtSearchRepay.TextChanged += (s, e) => SearchMembers(txtSearchRepay, lstMembersRepay);
            var btnSearch = CreateButton("Search", 450, y - 2, 90, 32);
            btnSearch.Click += (s, e) => SearchMembers(txtSearchRepay, lstMembersRepay);
            tab.Controls.Add(btnSearch);
            y += 40;

            lstMembersRepay = new ListBox
            {
                Location = new Point(160, y),
                Size = new Size(380, 60),
                Font = new Font("Segoe UI", 10)
            };
            lstMembersRepay.SelectedIndexChanged += (s, e) =>
            {
                if (lstMembersRepay.SelectedItem is MemberItem mi)
                {
                    _repayMemberId = mi.Id;
                    lblRepayMember.Text = $"{mi.Name} ({mi.Number})";
                    LoadActiveLoans(mi.Id);
                }
            };
            tab.Controls.Add(lstMembersRepay);
            y += 70;

            lblRepayMember = new Label
            {
                Text = "No member selected",
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Top = y,
                Left = 20
            };
            tab.Controls.Add(lblRepayMember);
            y += 32;

            tab.Controls.Add(new Label
            {
                Text = "Active Loans:",
                Font = new Font("Segoe UI", 11, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Top = y,
                Left = 20
            });
            y += 28;

            dgvActiveLoans = CreateGrid();
            dgvActiveLoans.Top = y;
            dgvActiveLoans.Left = 20;
            dgvActiveLoans.Width = 900;
            dgvActiveLoans.Height = 180;
            dgvActiveLoans.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            dgvActiveLoans.SelectionChanged += DgvActiveLoans_SelectionChanged;
            tab.Controls.Add(dgvActiveLoans);
            y += 190;

            AddLabel(tab, "Repayment Amount:", 20, y);
            txtRepayAmount = AddTextBox(tab, 200, y, 150);
            y += 45;

            AddLabel(tab, "Date:", 20, y);
            txtRepayDate = AddTextBox(tab, 200, y, 150);
            txtRepayDate.Text = Helpers.TodayStr();
            y += 55;

            var btnRepay = CreateButton("RECORD REPAYMENT", 200, y, 180, 42);
            btnRepay.Click += BtnRepay_Click;
            tab.Controls.Add(btnRepay);

            lblRepayMsg = new Label
            {
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Top = y + 50,
                Left = 200
            };
            tab.Controls.Add(lblRepayMsg);
        }

        private void LoadActiveLoans(string memberId)
        {
            var dt = new DataTable();
            dt.Columns.Add("id");
            dt.Columns.Add("Applied");
            dt.Columns.Add("Amount");
            dt.Columns.Add("Total Payable");
            dt.Columns.Add("Paid");
            dt.Columns.Add("Outstanding");
            dt.Columns.Add("Status");
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"SELECT l.id, l.applied_date, l.amount, l.total_payable, l.status,
                (SELECT COALESCE(SUM(amount), 0) FROM loan_repayments WHERE loan_id=l.id) as paid
                FROM loans l WHERE l.member_id=@mid AND l.status IN ('Approved','Disbursed') ORDER BY l.applied_date DESC";
            cmd.Parameters.AddWithValue("@mid", memberId);
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                double payable = Convert.ToDouble(reader["total_payable"]);
                double paid = Convert.ToDouble(reader["paid"]);
                double outstanding = payable - paid;
                if (outstanding < 0) outstanding = 0;
                dt.Rows.Add(reader["id"]!.ToString()!, reader["applied_date"]!.ToString()!,
                    Helpers.FormatCurrency(Convert.ToDouble(reader["amount"])),
                    Helpers.FormatCurrency(payable), Helpers.FormatCurrency(paid),
                    Helpers.FormatCurrency(outstanding), reader["status"]!.ToString()!);
            }
            dgvActiveLoans.DataSource = dt;
            if (dgvActiveLoans.Columns.Contains("id"))
                dgvActiveLoans.Columns["id"].Visible = false;
        }

        private void DgvActiveLoans_SelectionChanged(object? sender, EventArgs e)
        {
            if (dgvActiveLoans.CurrentRow != null)
                _repayLoanId = dgvActiveLoans.CurrentRow.Cells["id"].Value?.ToString() ?? "";
        }

        private void BtnRepay_Click(object? sender, EventArgs e)
        {
            if (string.IsNullOrEmpty(_repayLoanId))
            {
                lblRepayMsg.ForeColor = Color.Red;
                lblRepayMsg.Text = "Select a loan first";
                return;
            }

            var (valid, amount) = Validators.ValidateAmount(txtRepayAmount.Text);
            if (!valid)
            {
                lblRepayMsg.ForeColor = Color.Red;
                lblRepayMsg.Text = "Enter a valid amount greater than zero";
                return;
            }

            string date = string.IsNullOrWhiteSpace(txtRepayDate.Text) ? Helpers.TodayStr() : txtRepayDate.Text.Trim();
            TransactionEngine.RecordRepayment(_repayLoanId, amount, _userId, date);
            TransactionEngine.LogAudit(_userId, "Loan Repayment", $"Repayment of {Helpers.FormatCurrency(amount)} on loan {_repayLoanId}");

            lblRepayMsg.ForeColor = Color.Green;
            lblRepayMsg.Text = "Repayment recorded!";
            txtRepayAmount.Text = "";
            if (!string.IsNullOrEmpty(_repayMemberId))
                LoadActiveLoans(_repayMemberId);
        }

        private void BuildAllLoansTab(TabPage tab)
        {
            var pnlTop = new Panel
            {
                Dock = DockStyle.Top,
                Height = 48,
                BackColor = White,
                Padding = new Padding(15, 8, 15, 8)
            };

            pnlTop.Controls.Add(new Label
            {
                Text = "Filter by Status:",
                Font = new Font("Segoe UI", 11),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(15, 12)
            });

            cmbStatusFilter = new ComboBox
            {
                DropDownStyle = ComboBoxStyle.DropDownList,
                Width = 150,
                Location = new Point(140, 9)
            };
            cmbStatusFilter.Items.AddRange(new object[] { "All", "Pending", "Approved", "Disbursed", "Completed" });
            cmbStatusFilter.SelectedIndex = 0;
            cmbStatusFilter.SelectedIndexChanged += (s, e) => LoadAllLoans();
            pnlTop.Controls.Add(cmbStatusFilter);

            var btnRefresh = CreateButton("Refresh", 300, 6, 100, 34);
            btnRefresh.Click += (s, e) => LoadAllLoans();
            pnlTop.Controls.Add(btnRefresh);

            var btnView = CreateButton("View Selected", 410, 6, 130, 34);
            btnView.BackColor = Color.FromArgb(46, 125, 50);
            btnView.Click += (s, e) => ViewSelectedLoan();
            pnlTop.Controls.Add(btnView);
            tab.Controls.Add(pnlTop);

            dgvAllLoans = CreateGrid();
            dgvAllLoans.Dock = DockStyle.Fill;
            dgvAllLoans.DoubleClick += (s, e) => ViewSelectedLoan();
            tab.Controls.Add(dgvAllLoans);
            LoadAllLoans();
        }

        private void ViewSelectedLoan()
        {
            if (dgvAllLoans.CurrentRow == null) return;
            string loanId = dgvAllLoans.CurrentRow.Cells["id"].Value?.ToString() ?? "";
            if (string.IsNullOrEmpty(loanId)) return;
            tabControl.SelectedIndex = 0;
            LoadLoanDetail(loanId);
        }

        private void LoadAllLoans()
        {
            if (dgvAllLoans == null) return;
            string filter = cmbStatusFilter?.SelectedItem?.ToString() ?? "All";
            var dt = new DataTable();
            dt.Columns.Add("id");
            dt.Columns.Add("Member");
            dt.Columns.Add("Amount");
            dt.Columns.Add("Rate %");
            dt.Columns.Add("Payable");
            dt.Columns.Add("Paid");
            dt.Columns.Add("Outstanding");
            dt.Columns.Add("Status");
            dt.Columns.Add("Applied");

            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            string sql = @"SELECT l.id, m.full_name as Member, l.amount as Amount, l.interest_rate as Rate,
                l.total_payable as Payable, l.status as Status, l.applied_date as Applied,
                (SELECT COALESCE(SUM(amount), 0) FROM loan_repayments WHERE loan_id=l.id) as Paid
                FROM loans l INNER JOIN members m ON l.member_id=m.id";
            if (filter != "All")
            {
                sql += " WHERE l.status=@st";
                cmd.Parameters.AddWithValue("@st", filter);
            }
            sql += " ORDER BY l.applied_date DESC";
            cmd.CommandText = sql;
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                double payable = Convert.ToDouble(reader["Payable"]);
                double paid = Convert.ToDouble(reader["Paid"]);
                double outstanding = payable - paid;
                if (outstanding < 0) outstanding = 0;
                dt.Rows.Add(reader["id"]!.ToString()!, reader["Member"]!.ToString()!,
                    Helpers.FormatCurrency(Convert.ToDouble(reader["Amount"])),
                    Convert.ToDouble(reader["Rate"]).ToString("N2"),
                    Helpers.FormatCurrency(payable), Helpers.FormatCurrency(paid),
                    Helpers.FormatCurrency(outstanding),
                    reader["Status"]!.ToString()!, reader["Applied"]!.ToString()!);
            }
            dgvAllLoans.DataSource = dt;
            if (dgvAllLoans.Columns.Contains("id"))
                dgvAllLoans.Columns["id"].Visible = false;
        }

        private DataGridView CreateGrid()
        {
            return new DataGridView
            {
                BackgroundColor = White,
                BorderStyle = BorderStyle.None,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                MultiSelect = false,
                ReadOnly = true,
                AllowUserToAddRows = false,
                Font = new Font("Segoe UI", 9)
            };
        }

        private void AddLabel(Control parent, string text, int x, int y)
        {
            parent.Controls.Add(new Label
            {
                Text = text,
                Font = new Font("Segoe UI", 11),
                ForeColor = Blue,
                AutoSize = true,
                Top = y,
                Left = x
            });
        }

        private TextBox AddTextBox(Control parent, int x, int y, int width)
        {
            var txt = new TextBox { Font = new Font("Segoe UI", 11), Width = width, Top = y, Left = x };
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
