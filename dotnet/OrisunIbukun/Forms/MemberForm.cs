using System;
using System.Collections.Generic;
using System.Data;
using System.Drawing;
using System.IO;
using System.Windows.Forms;
using OrisunIbukun.Database;
using OrisunIbukun.Engine;
using OrisunIbukun.Utils;

namespace OrisunIbukun.Forms
{
    public class MemberForm : UserControl
    {
        private static readonly Color Blue = Color.FromArgb(21, 101, 192);
        private static readonly Color LightBlue = Color.FromArgb(227, 242, 253);
        private static readonly Color White = Color.White;
        private const int PageSize = 50;

        private readonly string _userId;
        private TabControl tabControl = null!;

        private TextBox txtRegName = null!;
        private TextBox txtRegPhone = null!;
        private TextBox txtRegAddress = null!;
        private TextBox txtRegDob = null!;
        private TextBox txtRegOccupation = null!;
        private TextBox txtRegEmail = null!;
        private TextBox txtRegNok = null!;
        private TextBox txtRegNokPhone = null!;
        private TextBox txtRegIdNumber = null!;
        private TextBox txtRegFee = null!;
        private TextBox txtRegDate = null!;
        private ComboBox cmbRegGender = null!;
        private ComboBox cmbRegIdType = null!;
        private Label lblRegPhoto = null!;
        private Label lblRegisterMsg = null!;
        private string _regPhotoSrc = "";

        private TextBox txtSearch = null!;
        private Label lblSearchStatus = null!;
        private DataGridView dgvMembers = null!;
        private Button btnPrev = null!;
        private Button btnNext = null!;
        private Label lblPage = null!;
        private int _page = 1;
        private int _totalMembers = 0;
        private string _searchQuery = "";

        private string? _shownMemberId;
        private Label lblProfName = null!;
        private Label lblProfId = null!;
        private readonly Dictionary<string, Label> _detailLabels = new();
        private readonly Dictionary<string, Label> _financeLabels = new();
        private Button btnViewBooklet = null!;
        private Button btnRecordSavings = null!;
        private Button btnRecordRepayment = null!;
        private Button btnRecordPayment = null!;

        public MemberForm(string userId)
        {
            _userId = userId;
            BackColor = LightBlue;
            InitializeForm();
            LoadMembersPage();
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
                Text = "Member Management",
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

            var tabRegister = new TabPage("Register Member");
            var tabSearch = new TabPage("Search Members");
            var tabProfile = new TabPage("Member Profile");

            BuildRegisterTab(tabRegister);
            BuildSearchTab(tabSearch);
            BuildProfileTab(tabProfile);

            tabControl.TabPages.AddRange(new[] { tabRegister, tabSearch, tabProfile });
            Controls.Add(tabControl);
        }

        private void BuildRegisterTab(TabPage tab)
        {
            var panel = new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = White,
                AutoScroll = true,
                Padding = new Padding(20)
            };

            var lblHeader = new Label
            {
                Text = "Register New Member (KYC)",
                Font = new Font("Segoe UI", 16, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(20, 15)
            };
            panel.Controls.Add(lblHeader);

            int labelX = 20;
            int controlX = 260;
            int y = 60;

            txtRegName = AddRegRow(panel, "Full Name *", y, labelX, controlX); y += 40;
            txtRegPhone = AddRegRow(panel, "Phone", y, labelX, controlX); y += 40;
            txtRegAddress = AddRegRow(panel, "Address", y, labelX, controlX); y += 40;
            txtRegDob = AddRegRow(panel, "Date of Birth (YYYY-MM-DD)", y, labelX, controlX); y += 40;
            txtRegOccupation = AddRegRow(panel, "Occupation", y, labelX, controlX); y += 40;
            txtRegEmail = AddRegRow(panel, "Email", y, labelX, controlX); y += 40;
            txtRegNok = AddRegRow(panel, "Next of Kin", y, labelX, controlX); y += 40;
            txtRegNokPhone = AddRegRow(panel, "Next of Kin Phone", y, labelX, controlX); y += 40;
            txtRegIdNumber = AddRegRow(panel, "ID Number", y, labelX, controlX); y += 40;
            txtRegFee = AddRegRow(panel, "Entrance Fee", y, labelX, controlX);
            txtRegFee.Text = Schema.GetSetting("entrance_fee");
            if (string.IsNullOrEmpty(txtRegFee.Text)) txtRegFee.Text = "5000";
            y += 40;
            txtRegDate = AddRegRow(panel, "Date Joined", y, labelX, controlX);
            txtRegDate.Text = Helpers.TodayStr();
            y += 40;

            panel.Controls.Add(new Label
            {
                Text = "Gender",
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.FromArgb(51, 51, 51),
                AutoSize = true,
                Location = new Point(labelX, y + 3)
            });
            cmbRegGender = new ComboBox
            {
                DropDownStyle = ComboBoxStyle.DropDownList,
                Width = 300,
                Location = new Point(controlX, y)
            };
            cmbRegGender.Items.AddRange(new object[] { "", "Male", "Female" });
            cmbRegGender.SelectedIndex = 0;
            panel.Controls.Add(cmbRegGender);
            y += 40;

            panel.Controls.Add(new Label
            {
                Text = "ID Type",
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.FromArgb(51, 51, 51),
                AutoSize = true,
                Location = new Point(labelX, y + 3)
            });
            cmbRegIdType = new ComboBox
            {
                DropDownStyle = ComboBoxStyle.DropDownList,
                Width = 300,
                Location = new Point(controlX, y)
            };
            cmbRegIdType.Items.AddRange(new object[] { "", "NIN", "Voter's Card", "Driver's License", "Passport", "Other" });
            cmbRegIdType.SelectedIndex = 0;
            panel.Controls.Add(cmbRegIdType);
            y += 40;

            panel.Controls.Add(new Label
            {
                Text = "Photograph",
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.FromArgb(51, 51, 51),
                AutoSize = true,
                Location = new Point(labelX, y + 3)
            });
            var btnPhoto = new Button
            {
                Text = "Upload Photo",
                FlatStyle = FlatStyle.Flat,
                BackColor = LightBlue,
                ForeColor = Blue,
                Width = 130,
                Height = 30,
                Location = new Point(controlX, y),
                Cursor = Cursors.Hand
            };
            btnPhoto.FlatAppearance.BorderSize = 0;
            btnPhoto.Click += (s, e) =>
            {
                using var ofd = new OpenFileDialog();
                ofd.Filter = "Images|*.jpg;*.jpeg;*.png;*.gif;*.bmp|All files|*.*";
                if (ofd.ShowDialog() == DialogResult.OK)
                {
                    _regPhotoSrc = ofd.FileName;
                    lblRegPhoto.Text = Path.GetFileName(ofd.FileName);
                }
            };
            panel.Controls.Add(btnPhoto);
            lblRegPhoto = new Label
            {
                Text = "No photo selected",
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.Gray,
                AutoSize = true,
                Location = new Point(controlX + 140, y + 5)
            };
            panel.Controls.Add(lblRegPhoto);
            y += 50;

            var btnRegister = CreateButton("Register", 20, y, 140, 40);
            btnRegister.Click += BtnRegister_Click;
            panel.Controls.Add(btnRegister);

            var btnClear = CreateButton("Clear", 170, y, 120, 40);
            btnClear.BackColor = LightBlue;
            btnClear.ForeColor = Blue;
            btnClear.Click += (s, e) => ClearRegisterForm();
            panel.Controls.Add(btnClear);
            y += 50;

            lblRegisterMsg = new Label
            {
                Font = new Font("Segoe UI", 10),
                AutoSize = true,
                Location = new Point(20, y)
            };
            panel.Controls.Add(lblRegisterMsg);

            tab.Controls.Add(panel);
        }

        private TextBox AddRegRow(Panel panel, string labelText, int y, int labelX, int controlX)
        {
            panel.Controls.Add(new Label
            {
                Text = labelText,
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.FromArgb(51, 51, 51),
                AutoSize = true,
                Location = new Point(labelX, y + 3)
            });
            var txt = new TextBox
            {
                Font = new Font("Segoe UI", 11),
                Width = 300,
                Location = new Point(controlX, y)
            };
            panel.Controls.Add(txt);
            return txt;
        }

        private void ClearRegisterForm()
        {
            txtRegName.Text = "";
            txtRegPhone.Text = "";
            txtRegAddress.Text = "";
            txtRegDob.Text = "";
            txtRegOccupation.Text = "";
            txtRegEmail.Text = "";
            txtRegNok.Text = "";
            txtRegNokPhone.Text = "";
            txtRegIdNumber.Text = "";
            txtRegFee.Text = Schema.GetSetting("entrance_fee");
            if (string.IsNullOrEmpty(txtRegFee.Text)) txtRegFee.Text = "5000";
            txtRegDate.Text = Helpers.TodayStr();
            cmbRegGender.SelectedIndex = 0;
            cmbRegIdType.SelectedIndex = 0;
            _regPhotoSrc = "";
            lblRegPhoto.Text = "No photo selected";
            lblRegisterMsg.Text = "";
        }

        private void BtnRegister_Click(object? sender, EventArgs e)
        {
            lblRegisterMsg.ForeColor = Color.Red;
            lblRegisterMsg.Text = "";

            var (validName, nameErr) = Validators.ValidateName(txtRegName.Text);
            if (!validName) { lblRegisterMsg.Text = nameErr; return; }

            double entranceFee = 0;
            if (!string.IsNullOrWhiteSpace(txtRegFee.Text))
            {
                var (validAmt, amt) = Validators.ValidateAmount(txtRegFee.Text);
                if (!validAmt) { lblRegisterMsg.Text = "Invalid entrance fee"; return; }
                entranceFee = amt;
            }

            var (validEmail, emailErr) = Validators.ValidateEmail(txtRegEmail.Text);
            if (!validEmail) { lblRegisterMsg.Text = emailErr; return; }

            var (validPhone, phoneErr) = Validators.ValidatePhone(txtRegPhone.Text);
            if (!validPhone) { lblRegisterMsg.Text = phoneErr; return; }

            if (!string.IsNullOrWhiteSpace(txtRegDob.Text))
            {
                var (validDob, dobErr) = Validators.ValidateDate(txtRegDob.Text, "Date of Birth");
                if (!validDob) { lblRegisterMsg.Text = dobErr; return; }
            }

            string dateJoined = string.IsNullOrWhiteSpace(txtRegDate.Text) ? Helpers.TodayStr() : txtRegDate.Text.Trim();

            string memberId = TransactionEngine.RegisterMember(
                txtRegName.Text.Trim(), txtRegPhone.Text.Trim(), txtRegAddress.Text.Trim(),
                entranceFee, dateJoined, _userId,
                txtRegDob.Text.Trim(), cmbRegGender.Text, txtRegOccupation.Text.Trim(),
                txtRegEmail.Text.Trim(), txtRegNok.Text.Trim(), txtRegNokPhone.Text.Trim(),
                cmbRegIdType.Text, txtRegIdNumber.Text.Trim());

            if (!string.IsNullOrEmpty(_regPhotoSrc) && File.Exists(_regPhotoSrc))
            {
                try
                {
                    string photosDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "OrisunIbukun", "photos");
                    Directory.CreateDirectory(photosDir);
                    string destPath = Path.Combine(photosDir, memberId + Path.GetExtension(_regPhotoSrc));
                    File.Copy(_regPhotoSrc, destPath, true);
                    TransactionEngine.UpdateMemberPhoto(memberId, destPath);
                }
                catch { }
            }

            string memberNumber = "";
            using (var conn = Connection.GetConnection())
            using (var cmd = conn.CreateCommand())
            {
                cmd.CommandText = "SELECT member_number FROM members WHERE id=@id";
                cmd.Parameters.AddWithValue("@id", memberId);
                memberNumber = cmd.ExecuteScalar()?.ToString() ?? "";
            }

            MessageBox.Show($"Member registered.\nID: {memberNumber}\nName: {txtRegName.Text.Trim()}",
                "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
            ClearRegisterForm();
            _page = 1;
            _searchQuery = "";
            txtSearch.Text = "";
            LoadMembersPage();
        }

        private void BuildSearchTab(TabPage tab)
        {
            var lblHeader = new Label
            {
                Text = "Search Members",
                Font = new Font("Segoe UI", 16, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Dock = DockStyle.Top,
                Height = 40,
                Padding = new Padding(20, 8, 0, 0)
            };
            tab.Controls.Add(lblHeader);

            var pnlSearch = new Panel
            {
                Dock = DockStyle.Top,
                Height = 48,
                BackColor = White,
                Padding = new Padding(20, 8, 20, 8)
            };

            txtSearch = new TextBox
            {
                Font = new Font("Segoe UI", 12),
                Width = 350,
                Left = 20,
                Top = 8
            };
            txtSearch.TextChanged += (s, e) =>
            {
                _searchQuery = txtSearch.Text.Trim().ToLower();
                _page = 1;
                LoadMembersPage();
            };
            pnlSearch.Controls.Add(txtSearch);

            var btnSearch = CreateButton("Search", 380, 6, 100, 35);
            btnSearch.Click += (s, e) =>
            {
                _searchQuery = txtSearch.Text.Trim().ToLower();
                _page = 1;
                LoadMembersPage();
            };
            pnlSearch.Controls.Add(btnSearch);

            var btnClear = CreateButton("Clear", 490, 6, 90, 35);
            btnClear.BackColor = Color.Gray;
            btnClear.Click += (s, e) => { txtSearch.Text = ""; };
            pnlSearch.Controls.Add(btnClear);
            tab.Controls.Add(pnlSearch);

            lblSearchStatus = new Label
            {
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.Gray,
                BackColor = White,
                AutoSize = false,
                Dock = DockStyle.Top,
                Height = 24,
                Padding = new Padding(20, 0, 0, 0)
            };
            tab.Controls.Add(lblSearchStatus);

            var pnlBottom = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 90,
                BackColor = White
            };

            var btnViewFull = CreateButton("OPEN FULL RECORD", 20, 8, 180, 35);
            btnViewFull.Click += (s, e) => ShowSelectedProfile();
            pnlBottom.Controls.Add(btnViewFull);

            var pnlPager = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 40,
                BackColor = White
            };
            btnPrev = CreateButton("← Previous", 20, 4, 110, 32);
            btnPrev.BackColor = LightBlue;
            btnPrev.ForeColor = Blue;
            btnPrev.Click += (s, e) => { if (_page > 1) { _page--; LoadMembersPage(); } };
            pnlPager.Controls.Add(btnPrev);

            lblPage = new Label
            {
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.Gray,
                AutoSize = true,
                Left = 145,
                Top = 9
            };
            pnlPager.Controls.Add(lblPage);

            btnNext = CreateButton("Next →", 260, 4, 110, 32);
            btnNext.BackColor = LightBlue;
            btnNext.ForeColor = Blue;
            btnNext.Click += (s, e) =>
            {
                int totalPages = Math.Max(1, (int)Math.Ceiling(_totalMembers / (double)PageSize));
                if (_page < totalPages) { _page++; LoadMembersPage(); }
            };
            pnlPager.Controls.Add(btnNext);
            pnlBottom.Controls.Add(pnlPager);
            tab.Controls.Add(pnlBottom);

            dgvMembers = new DataGridView
            {
                Dock = DockStyle.Fill,
                BackgroundColor = White,
                BorderStyle = BorderStyle.None,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                MultiSelect = false,
                ReadOnly = true,
                AllowUserToAddRows = false,
                Font = new Font("Segoe UI", 10)
            };
            dgvMembers.DoubleClick += DgvMembers_DoubleClick;
            tab.Controls.Add(dgvMembers);
        }

        private void LoadMembersPage()
        {
            if (dgvMembers == null) return;

            var dt = new DataTable();
            dt.Columns.Add("id");
            dt.Columns.Add("Member ID");
            dt.Columns.Add("Name");
            dt.Columns.Add("Phone");
            dt.Columns.Add("Status");

            int total = 0;
            using (var conn = Connection.GetConnection())
            {
                string where = "WHERE status='Active'";
                string like = "";
                if (!string.IsNullOrEmpty(_searchQuery))
                {
                    where += " AND (LOWER(full_name) LIKE @q OR LOWER(member_number) LIKE @q OR LOWER(phone) LIKE @q)";
                    like = $"%{_searchQuery}%";
                }

                using (var countCmd = conn.CreateCommand())
                {
                    countCmd.CommandText = $"SELECT COUNT(*) FROM members {where}";
                    if (!string.IsNullOrEmpty(_searchQuery))
                        countCmd.Parameters.AddWithValue("@q", like);
                    total = Convert.ToInt32(countCmd.ExecuteScalar());
                }

                int totalPages = Math.Max(1, (int)Math.Ceiling(total / (double)PageSize));
                if (_page > totalPages) _page = totalPages;
                int offset = (_page - 1) * PageSize;

                using (var cmd = conn.CreateCommand())
                {
                    cmd.CommandText = $"SELECT id, member_number, full_name, phone, status FROM members {where} ORDER BY full_name LIMIT {PageSize} OFFSET {offset}";
                    if (!string.IsNullOrEmpty(_searchQuery))
                        cmd.Parameters.AddWithValue("@q", like);
                    using var reader = cmd.ExecuteReader();
                    while (reader.Read())
                    {
                        dt.Rows.Add(
                            reader["id"]?.ToString() ?? "",
                            reader["member_number"]?.ToString() ?? "",
                            reader["full_name"]?.ToString() ?? "",
                            reader["phone"]?.ToString() ?? "",
                            reader["status"]?.ToString() ?? "");
                    }
                }
            }

            _totalMembers = total;
            dgvMembers.DataSource = dt;
            if (dgvMembers.Columns.Contains("id"))
                dgvMembers.Columns["id"].Visible = false;

            int start = total == 0 ? 0 : (_page - 1) * PageSize + 1;
            int end = Math.Min(_page * PageSize, total);
            lblSearchStatus.Text = $"Showing {start}-{end} of {total}";
            int pages = Math.Max(1, (int)Math.Ceiling(total / (double)PageSize));
            lblPage.Text = $"Page {_page} of {pages}";
            btnPrev.Enabled = _page > 1;
            btnNext.Enabled = _page < pages;
        }

        private void DgvMembers_DoubleClick(object? sender, EventArgs e)
        {
            if (dgvMembers.CurrentRow == null) return;
            string memberId = dgvMembers.CurrentRow.Cells["id"].Value?.ToString() ?? "";
            if (string.IsNullOrEmpty(memberId)) return;
            _shownMemberId = memberId;
            ShowProfile(memberId);
            tabControl.SelectedIndex = 2;
        }

        private void ShowSelectedProfile()
        {
            if (dgvMembers.CurrentRow == null) return;
            string memberId = dgvMembers.CurrentRow.Cells["id"].Value?.ToString() ?? "";
            if (string.IsNullOrEmpty(memberId)) return;

            var currentUser = new Dictionary<string, object>
            {
                { "id", _userId },
                { "role", "Administrator" }
            };
            var detailForm = new MemberDetailForm(memberId, currentUser);
            detailForm.ShowDialog();
            LoadMembersPage();
        }

        private void BuildProfileTab(TabPage tab)
        {
            var panel = new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = White,
                AutoScroll = true,
                Padding = new Padding(20)
            };

            var lblHeader = new Label
            {
                Text = "Member Profile",
                Font = new Font("Segoe UI", 16, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(20, 15)
            };
            panel.Controls.Add(lblHeader);

            lblProfName = new Label
            {
                Text = "No member selected",
                Font = new Font("Segoe UI", 14, FontStyle.Bold),
                ForeColor = Color.FromArgb(51, 51, 51),
                AutoSize = true,
                Location = new Point(20, 55)
            };
            panel.Controls.Add(lblProfName);

            lblProfId = new Label
            {
                Text = "",
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.Gray,
                AutoSize = true,
                Location = new Point(20, 85)
            };
            panel.Controls.Add(lblProfId);

            int y = 120;
            foreach (string field in new[] { "Phone", "Address", "Status", "Date Joined", "DOB",
                "Gender", "Occupation", "Email", "Next of Kin", "NOK Phone", "ID Type", "ID Number", "Photo" })
            {
                var row = new Panel { Location = new Point(20, y), Size = new Size(600, 26), BackColor = White };
                row.Controls.Add(new Label
                {
                    Text = field + ":",
                    Font = new Font("Segoe UI", 11, FontStyle.Bold),
                    ForeColor = Blue,
                    Width = 130,
                    Location = new Point(0, 0)
                });
                var val = new Label
                {
                    Text = "--",
                    Font = new Font("Segoe UI", 11),
                    ForeColor = Color.FromArgb(51, 51, 51),
                    AutoSize = true,
                    Location = new Point(135, 0)
                };
                row.Controls.Add(val);
                _detailLabels[field] = val;
                panel.Controls.Add(row);
                y += 28;
            }

            var divider = new Panel { Location = new Point(20, y), Size = new Size(600, 2), BackColor = LightBlue };
            panel.Controls.Add(divider);
            y += 14;

            panel.Controls.Add(new Label
            {
                Text = "Financial Summary",
                Font = new Font("Segoe UI", 14, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(20, y)
            });
            y += 32;

            foreach (var (display, key) in new[] { ("Total Paid", "total_paid"), ("Savings", "total_savings"),
                ("Shares", "total_shares"), ("Active Loan", "active_loan"), ("Loan Paid", "loan_paid"),
                ("Outstanding", "outstanding"), ("Minutes Owed", "minutes_owed"), ("Fines Owed", "fines_owed"),
                ("Other Charges Owed", "other_owed"), ("Charges Paid", "charges_paid") })
            {
                var row = new Panel { Location = new Point(20, y), Size = new Size(600, 26), BackColor = White };
                row.Controls.Add(new Label
                {
                    Text = display + ":",
                    Font = new Font("Segoe UI", 11, FontStyle.Bold),
                    ForeColor = Blue,
                    Width = 170,
                    Location = new Point(0, 0)
                });
                var val = new Label
                {
                    Text = Helpers.FormatCurrency(0),
                    Font = new Font("Segoe UI", 11),
                    ForeColor = Color.FromArgb(51, 51, 51),
                    AutoSize = true,
                    Location = new Point(175, 0)
                };
                row.Controls.Add(val);
                _financeLabels[key] = val;
                panel.Controls.Add(row);
                y += 28;
            }
            y += 10;

            btnViewBooklet = CreateButton("View Booklet", 20, y, 130, 38);
            btnViewBooklet.Enabled = false;
            btnViewBooklet.Click += (s, e) => NavigateTo("SAVINGS");
            panel.Controls.Add(btnViewBooklet);

            btnRecordSavings = CreateButton("Record Savings", 160, y, 150, 38);
            btnRecordSavings.Enabled = false;
            btnRecordSavings.Click += (s, e) => OpenRecordSavingsDialog();
            panel.Controls.Add(btnRecordSavings);

            btnRecordRepayment = CreateButton("Record Repayment", 320, y, 160, 38);
            btnRecordRepayment.Enabled = false;
            btnRecordRepayment.Click += (s, e) => OpenRecordRepaymentDialog();
            panel.Controls.Add(btnRecordRepayment);

            btnRecordPayment = CreateButton("Record Payment", 490, y, 150, 38);
            btnRecordPayment.BackColor = Color.FromArgb(230, 81, 0);
            btnRecordPayment.Enabled = false;
            btnRecordPayment.Click += (s, e) => OpenRecordPaymentDialog();
            panel.Controls.Add(btnRecordPayment);

            tab.Controls.Add(panel);
        }

        private void NavigateTo(string section)
        {
            var main = FindForm();
            if (main == null) return;
            var method = main.GetType().GetMethod("Nav_Click",
                System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
            method?.Invoke(main, new object[] { section });
        }

        private void ShowProfile(string memberId)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT * FROM members WHERE id=@id";
            cmd.Parameters.AddWithValue("@id", memberId);
            using var reader = cmd.ExecuteReader();
            if (!reader.Read()) return;

            lblProfName.Text = GetStr(reader, "full_name");
            lblProfId.Text = "Member ID: " + GetStr(reader, "member_number");
            SetDetail("Phone", GetStr(reader, "phone"));
            SetDetail("Address", GetStr(reader, "address"));
            SetDetail("Status", GetStr(reader, "status"));
            SetDetail("Date Joined", GetStr(reader, "date_joined"));
            SetDetail("DOB", GetStr(reader, "date_of_birth"));
            SetDetail("Gender", GetStr(reader, "gender"));
            SetDetail("Occupation", GetStr(reader, "occupation"));
            SetDetail("Email", GetStr(reader, "email"));
            SetDetail("Next of Kin", GetStr(reader, "next_of_kin"));
            SetDetail("NOK Phone", GetStr(reader, "next_of_kin_phone"));
            SetDetail("ID Type", GetStr(reader, "id_type"));
            SetDetail("ID Number", GetStr(reader, "id_number"));
            string photo = GetStr(reader, "photo_path");
            SetDetail("Photo", string.IsNullOrEmpty(photo) ? "--" : Path.GetFileName(photo));

            var summary = TransactionEngine.GetMemberFinancialSummary(memberId);
            double savings = Convert.ToDouble(summary["TotalSavings"]);
            double shares = Convert.ToDouble(summary["TotalShares"]);
            double activeLoan = Convert.ToDouble(summary["ActiveLoanAmount"]);
            double repaid = Convert.ToDouble(summary["TotalRepaid"]);
            double outstanding = TransactionEngine.GetMemberOutstanding(memberId);
            var owed = TransactionEngine.GetMemberChargesOwed(memberId);
            double chargesPaid = owed["ChargesPaid"];
            double totalPaid = savings + shares + repaid + chargesPaid;

            SetFinance("total_paid", totalPaid);
            SetFinance("total_savings", savings);
            SetFinance("total_shares", shares);
            SetFinance("active_loan", activeLoan);
            SetFinance("loan_paid", repaid);
            SetFinance("outstanding", outstanding);
            SetFinance("minutes_owed", owed["MinutesOwed"]);
            SetFinance("fines_owed", owed["FinesOwed"]);
            SetFinance("other_owed", owed["OtherOwed"]);
            SetFinance("charges_paid", chargesPaid);

            btnViewBooklet.Enabled = true;
            btnRecordSavings.Enabled = true;
            btnRecordRepayment.Enabled = true;
            btnRecordPayment.Enabled = true;
        }

        private void SetDetail(string field, string value)
        {
            if (_detailLabels.TryGetValue(field, out var lbl))
                lbl.Text = string.IsNullOrEmpty(value) ? "--" : value;
        }

        private void SetFinance(string key, double amount)
        {
            if (_financeLabels.TryGetValue(key, out var lbl))
                lbl.Text = Helpers.FormatCurrency(amount);
        }

        private void OpenRecordSavingsDialog()
        {
            if (string.IsNullOrEmpty(_shownMemberId)) return;
            using var dlg = new Form
            {
                Text = "Record Savings",
                Size = new Size(370, 220),
                StartPosition = FormStartPosition.CenterParent,
                FormBorderStyle = FormBorderStyle.FixedDialog,
                MaximizeBox = false,
                MinimizeBox = false
            };
            dlg.Controls.Add(new Label { Text = "Amount:", Font = new Font("Segoe UI", 12), AutoSize = true, Location = new Point(25, 25) });
            var txtAmt = new TextBox { Font = new Font("Segoe UI", 12), Width = 280, Location = new Point(25, 55) };
            dlg.Controls.Add(txtAmt);
            var btnSave = CreateButton("Save", 25, 105, 120, 38);
            btnSave.Click += (s, e) =>
            {
                var (valid, amount) = Validators.ValidateAmount(txtAmt.Text);
                if (!valid) { MessageBox.Show("Enter a valid amount greater than zero.", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
                string txnId = TransactionEngine.RecordSavings(_shownMemberId!, amount, "Cash", "", _userId, Helpers.TodayStr());
                MessageBox.Show($"Savings recorded.\nTransaction: {txnId}", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                dlg.Close();
                ShowProfile(_shownMemberId!);
                LoadMembersPage();
            };
            dlg.Controls.Add(btnSave);
            dlg.AcceptButton = btnSave;
            dlg.ShowDialog(this);
        }

        private void OpenRecordRepaymentDialog()
        {
            if (string.IsNullOrEmpty(_shownMemberId)) return;

            var loans = new List<(string id, string number, double outstanding)>();
            using (var conn = Connection.GetConnection())
            using (var cmd = conn.CreateCommand())
            {
                cmd.CommandText = @"SELECT l.id, l.applied_date, l.total_payable,
                    COALESCE((SELECT SUM(amount) FROM loan_repayments WHERE loan_id=l.id), 0) AS repaid
                    FROM loans l WHERE l.member_id=@mid AND l.status IN ('Approved','Disbursed') ORDER BY l.applied_date DESC";
                cmd.Parameters.AddWithValue("@mid", _shownMemberId);
                using var reader = cmd.ExecuteReader();
                while (reader.Read())
                {
                    double total = Convert.ToDouble(reader["total_payable"]);
                    double repaid = Convert.ToDouble(reader["repaid"]);
                    double outstanding = total - repaid;
                    if (outstanding < 0) outstanding = 0;
                    loans.Add((reader["id"]!.ToString()!, reader["applied_date"]!.ToString()!, outstanding));
                }
            }

            if (loans.Count == 0)
            {
                MessageBox.Show("This member has no active loans.", "No Loans", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            using var dlg = new Form
            {
                Text = "Record Loan Repayment",
                Size = new Size(430, 300),
                StartPosition = FormStartPosition.CenterParent,
                FormBorderStyle = FormBorderStyle.FixedDialog,
                MaximizeBox = false,
                MinimizeBox = false
            };
            dlg.Controls.Add(new Label { Text = "Select Loan:", Font = new Font("Segoe UI", 12, FontStyle.Bold), ForeColor = Blue, AutoSize = true, Location = new Point(25, 15) });
            var cmbLoans = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 360, Location = new Point(25, 45) };
            foreach (var l in loans)
                cmbLoans.Items.Add($"{l.number} — Outstanding: {Helpers.FormatCurrency(l.outstanding)}");
            cmbLoans.SelectedIndex = 0;
            dlg.Controls.Add(cmbLoans);
            dlg.Controls.Add(new Label { Text = "Amount:", Font = new Font("Segoe UI", 12), AutoSize = true, Location = new Point(25, 85) });
            var txtAmt = new TextBox { Font = new Font("Segoe UI", 12), Width = 360, Location = new Point(25, 115) };
            dlg.Controls.Add(txtAmt);
            var btnSave = CreateButton("Record Repayment", 25, 165, 170, 38);
            btnSave.Click += (s, e) =>
            {
                if (cmbLoans.SelectedIndex < 0) { MessageBox.Show("Select a loan.", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
                var (valid, amount) = Validators.ValidateAmount(txtAmt.Text);
                if (!valid) { MessageBox.Show("Enter a valid amount greater than zero.", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
                string loanId = loans[cmbLoans.SelectedIndex].id;
                string txnId = TransactionEngine.RecordRepayment(loanId, amount, _userId, Helpers.TodayStr());
                MessageBox.Show($"Repayment recorded.\nTransaction: {txnId}", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                dlg.Close();
                ShowProfile(_shownMemberId!);
            };
            dlg.Controls.Add(btnSave);
            dlg.AcceptButton = btnSave;
            dlg.ShowDialog(this);
        }

        private void OpenRecordPaymentDialog()
        {
            if (string.IsNullOrEmpty(_shownMemberId)) return;
            using var dlg = new Form
            {
                Text = "Record Payment",
                Size = new Size(430, 460),
                StartPosition = FormStartPosition.CenterParent,
                FormBorderStyle = FormBorderStyle.FixedDialog,
                MaximizeBox = false,
                MinimizeBox = false
            };
            dlg.Controls.Add(new Label { Text = "Category:", Font = new Font("Segoe UI", 12, FontStyle.Bold), ForeColor = Blue, AutoSize = true, Location = new Point(25, 15) });
            var cmbCat = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 360, Location = new Point(25, 45) };
            cmbCat.Items.AddRange(new object[] { "Minutes", "Shares", "Other" });
            cmbCat.SelectedIndex = 0;
            dlg.Controls.Add(cmbCat);
            dlg.Controls.Add(new Label { Text = "Amount (₦):", Font = new Font("Segoe UI", 12), AutoSize = true, Location = new Point(25, 85) });
            var txtAmt = new TextBox { Font = new Font("Segoe UI", 12), Width = 360, Location = new Point(25, 115) };
            dlg.Controls.Add(txtAmt);
            dlg.Controls.Add(new Label { Text = "Tag / Description (for Other):", Font = new Font("Segoe UI", 12), AutoSize = true, Location = new Point(25, 155) });
            var txtTag = new TextBox { Font = new Font("Segoe UI", 12), Width = 360, Location = new Point(25, 185) };
            dlg.Controls.Add(txtTag);
            dlg.Controls.Add(new Label { Text = "Payment Method:", Font = new Font("Segoe UI", 12), AutoSize = true, Location = new Point(25, 225) });
            var cmbMethod = new ComboBox { DropDownStyle = ComboBoxStyle.DropDownList, Width = 360, Location = new Point(25, 255) };
            cmbMethod.Items.AddRange(new object[] { "Cash", "Bank Transfer", "Mobile" });
            cmbMethod.SelectedIndex = 0;
            dlg.Controls.Add(cmbMethod);

            var btnSave = CreateButton("Record Payment", 25, 305, 170, 40);
            btnSave.BackColor = Color.FromArgb(230, 81, 0);
            btnSave.Click += (s, e) =>
            {
                var (valid, amount) = Validators.ValidateAmount(txtAmt.Text);
                if (!valid) { MessageBox.Show("Amount must be greater than zero.", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
                string category = cmbCat.SelectedItem!.ToString()!;
                string method = cmbMethod.SelectedItem!.ToString()!;
                string today = Helpers.TodayStr();
                string txnId;
                if (category == "Minutes")
                {
                    txnId = TransactionEngine.RecordChargePayment(_shownMemberId!, amount, "Minutes Levy", _userId, today);
                }
                else if (category == "Shares")
                {
                    double price = 1000;
                    string priceStr = Schema.GetSetting("share_price");
                    if (!string.IsNullOrEmpty(priceStr)) double.TryParse(priceStr, out price);
                    int count = (int)(amount / price);
                    if (count < 1) { MessageBox.Show($"Amount is less than one share ({Helpers.FormatCurrency(price)}).", "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
                    TransactionEngine.RecordShare(_shownMemberId!, count, count * price, _userId, today);
                    txnId = $"{count} share(s)";
                }
                else
                {
                    txnId = TransactionEngine.RecordOtherPayment(_shownMemberId!, amount, txtTag.Text.Trim(), _userId, today);
                }
                MessageBox.Show($"Payment recorded.\nTransaction: {txnId}", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                dlg.Close();
                ShowProfile(_shownMemberId!);
                LoadMembersPage();
            };
            dlg.Controls.Add(btnSave);
            dlg.AcceptButton = btnSave;
            dlg.ShowDialog(this);
        }

        private static string GetStr(IDataRecord reader, string column)
        {
            object val = reader[column];
            return val == null || val == DBNull.Value ? "" : val.ToString()!;
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
