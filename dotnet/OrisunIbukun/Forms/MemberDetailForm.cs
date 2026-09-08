using System;
using System.Collections.Generic;
using System.Data;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Printing;
using System.Globalization;
using System.IO;
using System.Text.Json;
using System.Windows.Forms;
using Microsoft.Data.Sqlite;
using OrisunIbukun.Database;
using OrisunIbukun.Engine;
using OrisunIbukun.Utils;

namespace OrisunIbukun.Forms
{
    public class MemberDetailForm : Form
    {
        private static readonly Color Blue = Color.FromArgb(21, 101, 192);
        private static readonly Color LightBlue = Color.FromArgb(227, 242, 253);
        private static readonly Color White = Color.White;

        private readonly string _memberId;
        private readonly Dictionary<string, object> _currentUser;

        private PictureBox photoPictureBox;
        private Label lblMemberName;
        private Label lblMemberNumber;
        private Label lblMemberId;
        private Label lblStatus;
        private Label lblPhone;
        private Label lblDateJoined;
        private Label lblEntranceFee;
        private Label lblMeetingsAttended;

        private TabControl tabControl;
        private TextBox txtFullName;
        private TextBox txtPhone;
        private TextBox txtAddress;
        private DateTimePicker dtpDob;
        private ComboBox cmbGender;
        private TextBox txtOccupation;
        private TextBox txtEmail;
        private ComboBox cmbIdType;
        private TextBox txtIdNumber;
        private TextBox txtNextOfKin;
        private TextBox txtNextOfKinPhone;
        private TextBox txtNotes;
        private Button btnEditProfile;
        private Button btnSaveProfile;

        private Label lblTotalSavings;
        private Label lblTotalShares;
        private Label lblShareCount;
        private Label lblActiveLoanAmount;
        private Label lblTotalRepaid;
        private Label lblOutstandingBalance;

        private DataGridView dgvSavingsShares;
        private DataGridView dgvTransactions;
        private DataGridView dgvLoans;
        private DataGridView dgvRepayments;
        private DataGridView dgvDocuments;
        private DataGridView dgvForms;
        private Button btnUploadDocument;
        private Button btnViewDocument;
        private Button btnDeleteDocument;
        private Button btnNewForm;
        private Button btnPrintProfile;
        private ComboBox cmbDocType;
        private Label lblRepaymentHistoryTitle;

        public MemberDetailForm(string memberId, Dictionary<string, object> currentUser)
        {
            _memberId = memberId;
            _currentUser = currentUser;
            InitializeComponents();
            LoadMemberData();
        }

        private void InitializeComponents()
        {
            this.Text = "Member Details";
            this.Size = new Size(1200, 780);
            this.MinimumSize = new Size(940, 640);
            this.StartPosition = FormStartPosition.CenterScreen;
            this.BackColor = LightBlue;

            var pnlTop = new Panel
            {
                Dock = DockStyle.Top,
                Height = 118,
                BackColor = Blue,
                Padding = new Padding(16, 12, 16, 8)
            };

            lblMemberName = new Label
            {
                Text = "Member Name",
                Font = new Font("Segoe UI", 18, FontStyle.Bold),
                ForeColor = White,
                AutoSize = true,
                Location = new Point(16, 10)
            };
            pnlTop.Controls.Add(lblMemberName);

            lblMemberNumber = new Label
            {
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.FromArgb(207, 224, 246),
                AutoSize = true,
                Location = new Point(18, 48)
            };
            pnlTop.Controls.Add(lblMemberNumber);

            lblStatus = new Label
            {
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                ForeColor = White,
                BackColor = Color.SeaGreen,
                AutoSize = true,
                Padding = new Padding(8, 4, 8, 4),
                TextAlign = ContentAlignment.MiddleCenter
            };
            pnlTop.Controls.Add(lblStatus);

            var btnClose = new Button
            {
                Text = "Close",
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(30, 70, 120),
                ForeColor = Color.White,
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                Width = 90,
                Height = 34,
                Cursor = Cursors.Hand,
                Anchor = AnchorStyles.Top | AnchorStyles.Right
            };
            btnClose.FlatAppearance.BorderSize = 0;
            btnClose.Click += (s, e) => this.Close();
            pnlTop.Controls.Add(btnClose);

            btnPrintProfile = new Button
            {
                Text = "Print",
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(30, 70, 120),
                ForeColor = Color.White,
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                Width = 90,
                Height = 34,
                Cursor = Cursors.Hand,
                Anchor = AnchorStyles.Top | AnchorStyles.Right
            };
            btnPrintProfile.FlatAppearance.BorderSize = 0;
            btnPrintProfile.Click += BtnPrintProfile_Click;
            pnlTop.Controls.Add(btnPrintProfile);

            pnlTop.Resize += (s, e) =>
            {
                btnClose.Location = new Point(pnlTop.ClientSize.Width - btnClose.Width - 16, 34);
                btnPrintProfile.Location = new Point(btnClose.Left - btnPrintProfile.Width - 8, 34);
                lblMemberName.Location = new Point(16, 28);
                lblMemberNumber.Location = new Point(18, 62);
                lblStatus.Location = new Point(18, 82);
            };

            this.Controls.Add(pnlTop);

            var pnlLeft = new Panel
            {
                Dock = DockStyle.Left,
                Width = 252,
                BackColor = White,
                Padding = new Padding(20)
            };

            photoPictureBox = new PictureBox
            {
                Size = new Size(190, 190),
                Location = new Point(20, 18),
                BorderStyle = BorderStyle.FixedSingle,
                SizeMode = PictureBoxSizeMode.StretchImage,
                BackColor = Blue,
                Cursor = Cursors.Hand
            };
            photoPictureBox.Click += PhotoPictureBox_Click;
            pnlLeft.Controls.Add(photoPictureBox);

            var lblQuickTitle = new Label
            {
                Text = "QUICK FACTS",
                Font = new Font("Segoe UI", 9, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(20, 225)
            };
            pnlLeft.Controls.Add(lblQuickTitle);

            lblMemberId = new Label
            {
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.Black,
                AutoSize = true,
                Location = new Point(20, 252)
            };
            pnlLeft.Controls.Add(lblMemberId);

            lblPhone = new Label
            {
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.Black,
                AutoSize = true,
                Location = new Point(20, 278)
            };
            pnlLeft.Controls.Add(lblPhone);

            lblDateJoined = new Label
            {
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.Black,
                AutoSize = true,
                Location = new Point(20, 304)
            };
            pnlLeft.Controls.Add(lblDateJoined);

            lblEntranceFee = new Label
            {
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.Black,
                AutoSize = true,
                Location = new Point(20, 330)
            };
            pnlLeft.Controls.Add(lblEntranceFee);

            lblMeetingsAttended = new Label
            {
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.Black,
                AutoSize = true,
                Location = new Point(20, 356)
            };
            pnlLeft.Controls.Add(lblMeetingsAttended);

            this.Controls.Add(pnlLeft);

            tabControl = new TabControl
            {
                Dock = DockStyle.Fill,
                Font = new Font("Segoe UI", 10)
            };

            TabPage tabProfile = new TabPage("Profile Details (KYC)");
            InitializeProfileTab(tabProfile);
            tabControl.TabPages.Add(tabProfile);

            TabPage tabFinancial = new TabPage("Financial Summary");
            InitializeFinancialTab(tabFinancial);
            tabControl.TabPages.Add(tabFinancial);

            TabPage tabSavingsShares = new TabPage("Savings & Shares Booklet");
            InitializeSavingsSharesTab(tabSavingsShares);
            tabControl.TabPages.Add(tabSavingsShares);

            TabPage tabLoans = new TabPage("Loan Details");
            InitializeLoansTab(tabLoans);
            tabControl.TabPages.Add(tabLoans);

            TabPage tabTransactions = new TabPage("All Transactions");
            InitializeTransactionsTab(tabTransactions);
            tabControl.TabPages.Add(tabTransactions);

            TabPage tabDocuments = new TabPage("Documents");
            InitializeDocumentsTab(tabDocuments);
            tabControl.TabPages.Add(tabDocuments);

            TabPage tabForms = new TabPage("Digital Forms");
            InitializeFormsTab(tabForms);
            tabControl.TabPages.Add(tabForms);

            this.Controls.Add(tabControl);
        }

        private void InitializeProfileTab(TabPage tab)
        {
            tab.BackColor = White;
            var panel = new Panel
            {
                Dock = DockStyle.Fill,
                BackColor = White,
                AutoScroll = true,
                Padding = new Padding(12)
            };

            var lblInfo = new Label
            {
                Text = "Personal / KYC Information",
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                ForeColor = Blue,
                AutoSize = true,
                Location = new Point(20, 12)
            };
            panel.Controls.Add(lblInfo);

            int labelX = 20;
            int controlX = 200;
            int width = 330;
            int yPos = 50;
            int spacing = 38;

            txtFullName = AddEditorField(panel, "Full Name:", ref yPos, labelX, controlX, width, spacing);
            txtPhone = AddEditorField(panel, "Phone:", ref yPos, labelX, controlX, width, spacing);
            txtAddress = AddEditorField(panel, "Address:", ref yPos, labelX, controlX, width, spacing);

            panel.Controls.Add(new Label
            {
                Text = "Date of Birth:",
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.FromArgb(90, 90, 90),
                AutoSize = true,
                Location = new Point(labelX, yPos + 3)
            });
            dtpDob = new DateTimePicker
            {
                Location = new Point(controlX, yPos),
                Size = new Size(width, 25),
                Format = DateTimePickerFormat.Short,
                Enabled = false
            };
            panel.Controls.Add(dtpDob);
            yPos += spacing;

            panel.Controls.Add(new Label
            {
                Text = "Gender:",
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.FromArgb(90, 90, 90),
                AutoSize = true,
                Location = new Point(labelX, yPos + 3)
            });
            cmbGender = new ComboBox
            {
                Location = new Point(controlX, yPos),
                Size = new Size(width, 25),
                DropDownStyle = ComboBoxStyle.DropDownList,
                Enabled = false
            };
            cmbGender.Items.AddRange(new object[] { "Male", "Female", "M", "F" });
            panel.Controls.Add(cmbGender);
            yPos += spacing;

            txtOccupation = AddEditorField(panel, "Occupation:", ref yPos, labelX, controlX, width, spacing);
            txtEmail = AddEditorField(panel, "Email:", ref yPos, labelX, controlX, width, spacing);

            panel.Controls.Add(new Label
            {
                Text = "ID Type:",
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.FromArgb(90, 90, 90),
                AutoSize = true,
                Location = new Point(labelX, yPos + 3)
            });
            cmbIdType = new ComboBox
            {
                Location = new Point(controlX, yPos),
                Size = new Size(width, 25),
                DropDownStyle = ComboBoxStyle.DropDownList,
                Enabled = false
            };
            cmbIdType.Items.AddRange(new object[] { "", "NIN", "Voter's Card", "Driver's License", "Passport", "Other" });
            panel.Controls.Add(cmbIdType);
            yPos += spacing;

            txtIdNumber = AddEditorField(panel, "ID Number:", ref yPos, labelX, controlX, width, spacing);
            txtNextOfKin = AddEditorField(panel, "Next of Kin:", ref yPos, labelX, controlX, width, spacing);
            txtNextOfKinPhone = AddEditorField(panel, "Next of Kin Phone:", ref yPos, labelX, controlX, width, spacing);

            yPos += 12;
            panel.Controls.Add(new Label
            {
                Text = "Notes:",
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.FromArgb(90, 90, 90),
                AutoSize = true,
                Location = new Point(labelX, yPos)
            });
            txtNotes = new TextBox
            {
                Location = new Point(controlX, yPos),
                Size = new Size(width, 80),
                Multiline = true,
                ScrollBars = ScrollBars.Vertical,
                Enabled = false
            };
            panel.Controls.Add(txtNotes);
            yPos += 100;

            btnEditProfile = new Button
            {
                Text = "Edit",
                FlatStyle = FlatStyle.Flat,
                BackColor = Blue,
                ForeColor = Color.White,
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                Width = 110,
                Height = 36,
                Location = new Point(controlX, yPos),
                Cursor = Cursors.Hand
            };
            btnEditProfile.FlatAppearance.BorderSize = 0;
            btnEditProfile.Click += BtnEditProfile_Click;
            panel.Controls.Add(btnEditProfile);

            btnSaveProfile = new Button
            {
                Text = "Save",
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.SeaGreen,
                ForeColor = Color.White,
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                Width = 110,
                Height = 36,
                Location = new Point(controlX + 125, yPos),
                Enabled = false,
                Cursor = Cursors.Hand
            };
            btnSaveProfile.FlatAppearance.BorderSize = 0;
            btnSaveProfile.Click += BtnSaveProfile_Click;
            panel.Controls.Add(btnSaveProfile);

            tab.Controls.Add(panel);
        }

        private static string GetStoredString(IDataRecord reader, string column)
        {
            object val = reader[column];
            return val == null || val == DBNull.Value ? "" : val.ToString();
        }

        private static double GetStoredDouble(IDataRecord reader, string column)
        {
            object val = reader[column];
            if (val == null || val == DBNull.Value) return 0;
            double d;
            return double.TryParse(val.ToString(), NumberStyles.Any, CultureInfo.InvariantCulture, out d) ? d : 0;
        }

        private TextBox AddEditorField(Panel panel, string labelText, ref int y, int labelX, int controlX, int width, int spacing)
        {
            panel.Controls.Add(new Label
            {
                Text = labelText,
                Font = new Font("Segoe UI", 11),
                ForeColor = Color.FromArgb(90, 90, 90),
                AutoSize = true,
                Location = new Point(labelX, y + 3)
            });

            var txt = new TextBox
            {
                Location = new Point(controlX, y),
                Size = new Size(width, 25),
                Enabled = false
            };
            panel.Controls.Add(txt);
            y += spacing;
            return txt;
        }

        private void InitializeFinancialTab(TabPage tab)
        {
            tab.BackColor = White;
            int yPos = 20;
            int labelX = 30;
            int valueX = 280;

            AddSummaryRow(tab, "Total Savings:", ref yPos, labelX, valueX, out lblTotalSavings, Color.FromArgb(0, 120, 60));
            AddSummaryRow(tab, "Total Shares (value):", ref yPos, labelX, valueX, out lblTotalShares, Color.FromArgb(0, 120, 60));
            AddSummaryRow(tab, "Share Count:", ref yPos, labelX, valueX, out lblShareCount, Color.FromArgb(21, 101, 192));
            AddSummaryRow(tab, "Active Loan Balance:", ref yPos, labelX, valueX, out lblActiveLoanAmount, Color.Red);
            AddSummaryRow(tab, "Total Repaid:", ref yPos, labelX, valueX, out lblTotalRepaid, Color.SeaGreen);
            AddSummaryRow(tab, "Outstanding Balance:", ref yPos, labelX, valueX, out lblOutstandingBalance, Color.Red);
        }

        private void AddSummaryRow(TabPage tab, string labelText, ref int yPos, int labelX, int valueX, out Label valueLabel, Color valueColor)
        {
            tab.Controls.Add(new Label
            {
                Text = labelText,
                Location = new Point(labelX, yPos),
                AutoSize = true,
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                ForeColor = Color.FromArgb(60, 60, 60)
            });
            valueLabel = new Label
            {
                Text = "₦0.00",
                Location = new Point(valueX, yPos),
                AutoSize = true,
                Font = new Font("Segoe UI", 12, FontStyle.Bold),
                ForeColor = valueColor
            };
            tab.Controls.Add(valueLabel);
            yPos += 52;
        }

        private void InitializeSavingsSharesTab(TabPage tab)
        {
            tab.BackColor = White;
            var lblNote = new Label
            {
                Text = "Savings & shares recorded with running balance",
                Dock = DockStyle.Top,
                Height = 30,
                Font = new Font("Segoe UI", 9, FontStyle.Italic),
                ForeColor = Color.Gray,
                Padding = new Padding(10, 6, 0, 0)
            };
            tab.Controls.Add(lblNote);

            dgvSavingsShares = CreateGrid();
            dgvSavingsShares.Dock = DockStyle.Fill;
            tab.Controls.Add(dgvSavingsShares);
        }

        private void InitializeLoansTab(TabPage tab)
        {
            tab.BackColor = White;
            dgvLoans = CreateGrid();
            dgvLoans.Dock = DockStyle.Top;
            dgvLoans.Height = 300;
            dgvLoans.SelectionChanged += DgvLoans_SelectionChanged;
            tab.Controls.Add(dgvLoans);

            lblRepaymentHistoryTitle = new Label
            {
                Text = "Repayment History",
                Dock = DockStyle.Top,
                Height = 30,
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                ForeColor = Blue,
                Padding = new Padding(10, 6, 0, 0)
            };
            tab.Controls.Add(lblRepaymentHistoryTitle);

            dgvRepayments = CreateGrid();
            dgvRepayments.Dock = DockStyle.Fill;
            tab.Controls.Add(dgvRepayments);
        }

        private void InitializeTransactionsTab(TabPage tab)
        {
            tab.BackColor = White;
            dgvTransactions = CreateGrid();
            dgvTransactions.Dock = DockStyle.Fill;
            tab.Controls.Add(dgvTransactions);
        }

        private void InitializeDocumentsTab(TabPage tab)
        {
            tab.BackColor = White;
            dgvDocuments = CreateGrid();
            dgvDocuments.Dock = DockStyle.Fill;
            tab.Controls.Add(dgvDocuments);

            var pnlBottom = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 48,
                BackColor = White,
                Padding = new Padding(10, 7, 10, 5)
            };

            cmbDocType = new ComboBox
            {
                DropDownStyle = ComboBoxStyle.DropDownList,
                Width = 190,
                Height = 28,
                Location = new Point(10, 9),
                Font = new Font("Segoe UI", 10)
            };
            cmbDocType.Items.AddRange(new object[] { "ID Card", "Passport / Photo", "Next of Kin", "Address Proof", "Guarantor", "Bank Details", "Other" });
            cmbDocType.SelectedIndex = 0;
            pnlBottom.Controls.Add(cmbDocType);

            btnUploadDocument = CreateSmallButton("Upload", Color.Blue, 215, 8);
            btnUploadDocument.Click += BtnUploadDocument_Click;
            pnlBottom.Controls.Add(btnUploadDocument);

            btnViewDocument = CreateSmallButton("View", Color.FromArgb(80, 130, 200), 325, 8);
            btnViewDocument.Click += BtnViewDocument_Click;
            pnlBottom.Controls.Add(btnViewDocument);

            btnDeleteDocument = CreateSmallButton("Delete", Color.Firebrick, 435, 8);
            btnDeleteDocument.Click += BtnDeleteDocument_Click;
            pnlBottom.Controls.Add(btnDeleteDocument);

            tab.Controls.Add(pnlBottom);
        }

        private void InitializeFormsTab(TabPage tab)
        {
            tab.BackColor = White;
            dgvForms = CreateGrid();
            dgvForms.Dock = DockStyle.Fill;
            tab.Controls.Add(dgvForms);

            btnNewForm = new Button
            {
                Text = "New Digital Form",
                Dock = DockStyle.Bottom,
                Height = 42,
                BackColor = Blue,
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 10, FontStyle.Bold),
                Cursor = Cursors.Hand,
                Margin = new Padding(10)
            };
            btnNewForm.FlatAppearance.BorderSize = 0;
            btnNewForm.Click += BtnNewForm_Click;
            tab.Controls.Add(btnNewForm);
        }

        private DataGridView CreateGrid()
        {
            return new DataGridView
            {
                AllowUserToAddRows = false,
                ReadOnly = true,
                AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill,
                SelectionMode = DataGridViewSelectionMode.FullRowSelect,
                BackgroundColor = White,
                BorderStyle = BorderStyle.None,
                Font = new Font("Segoe UI", 10),
                ColumnHeadersDefaultCellStyle = new DataGridViewCellStyle
                {
                    BackColor = LightBlue,
                    ForeColor = Blue,
                    Font = new Font("Segoe UI", 10, FontStyle.Bold)
                }
            };
        }

        private Button CreateSmallButton(string text, Color color, int x, int y)
        {
            var btn = new Button
            {
                Text = text,
                FlatStyle = FlatStyle.Flat,
                BackColor = color,
                ForeColor = Color.White,
                Font = new Font("Segoe UI", 9, FontStyle.Bold),
                Width = 100,
                Height = 32,
                Location = new Point(x, y),
                Cursor = Cursors.Hand
            };
            btn.FlatAppearance.BorderSize = 0;
            return btn;
        }

        private void LoadMemberData()
        {
            try
            {
                using (var conn = Connection.GetConnection())
                {
                    conn.Open();

                    using (var cmd = conn.CreateCommand())
                    {
                        cmd.CommandText = "SELECT * FROM members WHERE id = @id";
                        cmd.Parameters.AddWithValue("@id", _memberId);
                        using (var reader = cmd.ExecuteReader())
                        {
                            if (reader.Read())
                            {
                                lblMemberName.Text = GetStoredString(reader, "full_name");
                                lblMemberNumber.Text = "No. " + GetStoredString(reader, "member_number");
                                lblMemberId.Text = "ID: " + _memberId;

                                string status = GetStoredString(reader, "status");
                                lblStatus.Text = status;
lblStatus.BackColor = status == "Active" ? Color.SeaGreen : Color.Firebrick;

                                txtFullName.Text = GetStoredString(reader, "full_name");
                                txtPhone.Text = GetStoredString(reader, "phone");
                                txtAddress.Text = GetStoredString(reader, "address");
                                string dob = GetStoredString(reader, "date_of_birth");
                                if (!string.IsNullOrEmpty(dob))
                                {
                                    try { dtpDob.Value = DateTime.Parse(dob); }
                                    catch { dtpDob.Value = DateTime.Today; }
                                }
                                cmbGender.Text = GetStoredString(reader, "gender");
                                txtOccupation.Text = GetStoredString(reader, "occupation");
                                txtEmail.Text = GetStoredString(reader, "email");
                                cmbIdType.Text = GetStoredString(reader, "id_type");
                                txtIdNumber.Text = GetStoredString(reader, "id_number");
                                txtNextOfKin.Text = GetStoredString(reader, "next_of_kin");
                                txtNextOfKinPhone.Text = GetStoredString(reader, "next_of_kin_phone");
                                txtNotes.Text = GetStoredString(reader, "notes");

                                lblPhone.Text = "Phone: " + GetStoredString(reader, "phone");
                                lblDateJoined.Text = "Joined: " + GetStoredString(reader, "date_joined");
                                lblEntranceFee.Text = "Entrance Fee: " + Helpers.FormatCurrency(GetStoredDouble(reader, "entrance_fee"));

                                string photoPath = GetStoredString(reader, "photo_path");
                                if (!string.IsNullOrEmpty(photoPath) && File.Exists(photoPath))
                                {
                                    try { photoPictureBox.Image = Image.FromFile(photoPath); }
                                    catch { DrawPhotoPlaceholder(); }
                                }
                                else
                                {
                                    DrawPhotoPlaceholder();
                                }
                            }
                        }
                    }

                    var summary = TransactionEngine.GetMemberFinancialSummary(_memberId);
                    lblTotalSavings.Text = Helpers.FormatCurrency(Convert.ToDouble(summary["TotalSavings"]));
                    lblTotalShares.Text = Helpers.FormatCurrency(Convert.ToDouble(summary["TotalShares"]));
                    lblShareCount.Text = summary["SharesCount"].ToString();
                    lblActiveLoanAmount.Text = Helpers.FormatCurrency(Convert.ToDouble(summary["ActiveLoanAmount"]));
                    lblTotalRepaid.Text = Helpers.FormatCurrency(Convert.ToDouble(summary["TotalRepaid"]));

                    lblMeetingsAttended.Text = "Meetings Attended: " + summary["MeetingsAttended"];
                    lblOutstandingBalance.Text = Helpers.FormatCurrency(ComputeOutstandingBalance());

                    LoadBooklet();
                    LoadTransactions();
                    LoadLoans();
                    LoadDocuments();
                    LoadForms();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error loading member data: " + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private double ComputeOutstandingBalance()
        {
            double activePayable = 0;
            using (var conn = Connection.GetConnection())
            {
                conn.Open();
                using (var cmd = conn.CreateCommand())
                {
                    cmd.CommandText = "SELECT COALESCE(SUM(total_payable), 0) FROM loans WHERE member_id=@mid AND status IN ('Approved','Disbursed')";
                    cmd.Parameters.AddWithValue("@mid", _memberId);
                    activePayable = Convert.ToDouble(cmd.ExecuteScalar());
                }

                double repaid = 0;
                using (var cmd = conn.CreateCommand())
                {
                    cmd.CommandText = @"SELECT COALESCE(SUM(lr.amount), 0) FROM loan_repayments lr
                        INNER JOIN loans l ON lr.loan_id=l.id
                        WHERE l.member_id=@mid AND l.status IN ('Approved','Disbursed')";
                    cmd.Parameters.AddWithValue("@mid", _memberId);
                    repaid = Convert.ToDouble(cmd.ExecuteScalar());
                }
                double outstanding = activePayable - repaid;
                return outstanding > 0 ? outstanding : 0;
            }
        }

        private void LoadBooklet()
        {
            var rows = new List<(string date, string type, string details, double amount, double balance)>();
            double running = 0;

            using (var conn = Connection.GetConnection())
            {
                conn.Open();

                using (var cmd = conn.CreateCommand())
                {
                    cmd.CommandText = "SELECT transaction_date, type, amount, description FROM transactions WHERE member_id=@mid AND type IN ('Savings','Shares') ORDER BY transaction_date ASC, created_at ASC";
                    cmd.Parameters.AddWithValue("@mid", _memberId);
                    using (var reader = cmd.ExecuteReader())
                    {
                        while (reader.Read())
                        {
                            running += GetStoredDouble(reader, "amount");
                            rows.Add((GetStoredString(reader, "transaction_date"),
                                GetStoredString(reader, "type"),
                                GetStoredString(reader, "description"),
                                GetStoredDouble(reader, "amount"),
                                running));
                        }
                    }
                }
            }

            var dt = new DataTable();
            dt.Columns.Add("Date");
            dt.Columns.Add("Type");
            dt.Columns.Add("Description");
            dt.Columns.Add("Amount");
            dt.Columns.Add("Balance");

            foreach (var r in rows)
                dt.Rows.Add(r.date, r.type, r.details, Helpers.FormatCurrency(r.amount), Helpers.FormatCurrency(r.balance));

            dgvSavingsShares.DataSource = dt;
        }

        private void LoadTransactions()
        {
            var dt = new DataTable();
            dt.Columns.Add("Date");
            dt.Columns.Add("Type");
            dt.Columns.Add("Description");
            dt.Columns.Add("Amount");

            try
            {
                using (var conn = Connection.GetConnection())
                {
                    conn.Open();
                    using (var cmd = conn.CreateCommand())
                    {
                        cmd.CommandText = "SELECT transaction_date, type, description, amount FROM transactions WHERE member_id=@mid ORDER BY transaction_date DESC, created_at DESC";
                        cmd.Parameters.AddWithValue("@mid", _memberId);
                        using (var reader = cmd.ExecuteReader())
                        {
                            while (reader.Read())
                            {
                                dt.Rows.Add(
                                    GetStoredString(reader, "transaction_date"),
                                    GetStoredString(reader, "type"),
                                    GetStoredString(reader, "description"),
                                    Helpers.FormatCurrency(GetStoredDouble(reader, "amount")));
                            }
                        }
                    }
                }
            }
            catch { }

            dgvTransactions.DataSource = dt;
        }

        private void LoadLoans()
        {
            var dt = new DataTable();
            dt.Columns.Add("Loan ID");
            dt.Columns.Add("Amount");
            dt.Columns.Add("Interest %");
            dt.Columns.Add("Total Payable");
            dt.Columns.Add("Repaid");
            dt.Columns.Add("Outstanding");
            dt.Columns.Add("Status");
            dt.Columns.Add("Applied Date");
            dt.Columns.Add("Purpose");

            try
            {
                using (var conn = Connection.GetConnection())
                {
                    conn.Open();
                    using (var cmd = conn.CreateCommand())
                    {
                        cmd.CommandText = @"SELECT l.id, l.amount, l.interest_rate, l.total_payable, l.status, l.applied_date, l.purpose,
                            COALESCE((SELECT SUM(lr.amount) FROM loan_repayments lr WHERE lr.loan_id=l.id), 0) AS repaid
                            FROM loans l WHERE l.member_id=@mid ORDER BY l.applied_date DESC";
                        cmd.Parameters.AddWithValue("@mid", _memberId);
                        using (var reader = cmd.ExecuteReader())
                        {
                            while (reader.Read())
                            {
                                double totalPayable = GetStoredDouble(reader, "total_payable");
                                double repaid = GetStoredDouble(reader, "repaid");
                                double outstanding = totalPayable - repaid;
                                if (outstanding < 0) outstanding = 0;

                                dt.Rows.Add(
                                    GetStoredString(reader, "id"),
                                    Helpers.FormatCurrency(GetStoredDouble(reader, "amount")),
                                    GetStoredDouble(reader, "interest_rate").ToString("N2"),
                                    Helpers.FormatCurrency(totalPayable),
                                    Helpers.FormatCurrency(repaid),
                                    Helpers.FormatCurrency(outstanding),
                                    GetStoredString(reader, "status"),
                                    GetStoredString(reader, "applied_date"),
                                    GetStoredString(reader, "purpose"));
                            }
                        }
                    }
                }
            }
            catch { }

            dgvLoans.DataSource = dt;
        }

        private void DgvLoans_SelectionChanged(object sender, EventArgs e)
        {
            if (dgvLoans.CurrentRow == null) return;
            var loanId = dgvLoans.CurrentRow.Cells["Loan ID"].Value;
            if (loanId == null) return;
            LoadRepayments(loanId.ToString());
        }

        private void LoadRepayments(string loanId)
        {
            var dt = new DataTable();
            dt.Columns.Add("Date");
            dt.Columns.Add("Amount");
            dt.Columns.Add("Recorded By");
            dt.Columns.Add("Recorded At");

            try
            {
                using (var conn = Connection.GetConnection())
                {
                    conn.Open();
                    using (var cmd = conn.CreateCommand())
                    {
                        cmd.CommandText = "SELECT payment_date, amount, recorded_by, created_at FROM loan_repayments WHERE loan_id=@id ORDER BY payment_date DESC";
                        cmd.Parameters.AddWithValue("@id", loanId);
                        using (var reader = cmd.ExecuteReader())
                        {
                            while (reader.Read())
                            {
                                dt.Rows.Add(
                                    GetStoredString(reader, "payment_date"),
                                    Helpers.FormatCurrency(GetStoredDouble(reader, "amount")),
                                    GetStoredString(reader, "recorded_by"),
                                    GetStoredString(reader, "created_at"));
                            }
                        }
                    }
                }
            }
            catch { }

            dgvRepayments.DataSource = dt;
        }

        private void LoadDocuments()
        {
            var dt = new DataTable();
            dt.Columns.Add("Doc ID");
            dt.Columns.Add("Doc Type");
            dt.Columns.Add("File Name");
            dt.Columns.Add("Size");
            dt.Columns.Add("Uploaded At");
            dt.Columns.Add("File Path");

            try
            {
                using (var conn = Connection.GetConnection())
                {
                    conn.Open();
                    using (var cmd = conn.CreateCommand())
                    {
                        cmd.CommandText = "SELECT id, doc_type, file_name, file_size, file_path, uploaded_at FROM member_documents WHERE member_id=@mid ORDER BY uploaded_at DESC";
                        cmd.Parameters.AddWithValue("@mid", _memberId);
                        using (var reader = cmd.ExecuteReader())
                        {
                            while (reader.Read())
                            {
                                long size = reader["file_size"] == DBNull.Value ? 0 : Convert.ToInt64(reader["file_size"]);
                                string sizeStr = size > 1048576 ? (size / 1048576.0).ToString("N2") + " MB" : (size / 1024.0).ToString("N2") + " KB";
                                dt.Rows.Add(
                                    GetStoredString(reader, "id"),
                                    GetStoredString(reader, "doc_type"),
                                    GetStoredString(reader, "file_name"),
                                    sizeStr,
                                    GetStoredString(reader, "uploaded_at"),
                                    GetStoredString(reader, "file_path"));
                            }
                        }
                    }
                }
            }
            catch { }

            dgvDocuments.DataSource = dt;

            if (dgvDocuments.Columns.Contains("Doc ID")) dgvDocuments.Columns["Doc ID"].Visible = false;
            if (dgvDocuments.Columns.Contains("File Path")) dgvDocuments.Columns["File Path"].Visible = false;

            if (dgvDocuments.Columns.Contains("btnView"))
                dgvDocuments.Columns.Remove("btnView");
            if (dgvDocuments.Columns.Contains("btnDelete"))
                dgvDocuments.Columns.Remove("btnDelete");

            var colView = new DataGridViewButtonColumn
            {
                Name = "btnView",
                HeaderText = "View",
                Text = "View",
                UseColumnTextForButtonValue = true,
                AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill,
                FillWeight = 25
            };
            dgvDocuments.Columns.Add(colView);

            var colDelete = new DataGridViewButtonColumn
            {
                Name = "btnDelete",
                HeaderText = "Delete",
                Text = "Delete",
                UseColumnTextForButtonValue = true,
                AutoSizeMode = DataGridViewAutoSizeColumnMode.Fill,
                FillWeight = 25
            };
            dgvDocuments.Columns.Add(colDelete);

            dgvDocuments.CellContentClick -= DgvDocuments_CellContentClick;
            dgvDocuments.CellContentClick += DgvDocuments_CellContentClick;
        }

        private void DgvDocuments_CellContentClick(object sender, DataGridViewCellEventArgs e)
        {
            if (e.RowIndex < 0) return;
            if (dgvDocuments.Columns[e.ColumnIndex].Name == "btnView")
                BtnViewDocument_Click(sender, e);
            else if (dgvDocuments.Columns[e.ColumnIndex].Name == "btnDelete")
                BtnDeleteDocument_Click(sender, e);
        }

        private void LoadForms()
        {
            var dt = new DataTable();
            dt.Columns.Add("Form Type");
            dt.Columns.Add("Status");
            dt.Columns.Add("Created At");

            try
            {
                using (var conn = Connection.GetConnection())
                {
                    conn.Open();
                    using (var cmd = conn.CreateCommand())
                    {
                        cmd.CommandText = "SELECT form_type, status, created_at FROM digital_forms WHERE member_id=@mid ORDER BY created_at DESC";
                        cmd.Parameters.AddWithValue("@mid", _memberId);
                        using (var reader = cmd.ExecuteReader())
                        {
                            while (reader.Read())
                            {
                                dt.Rows.Add(
                                    GetStoredString(reader, "form_type"),
                                    GetStoredString(reader, "status"),
                                    GetStoredString(reader, "created_at"));
                            }
                        }
                    }
                }
            }
            catch { }

            dgvForms.DataSource = dt;
        }

        private void DrawPhotoPlaceholder()
        {
            using (var bmp = new Bitmap(photoPictureBox.Width, photoPictureBox.Height))
            using (var g = Graphics.FromImage(bmp))
            {
                g.Clear(Blue);
                g.DrawString("Click to\nupload photo", new Font("Segoe UI", 10), Brushes.White,
                    new RectangleF(0, (float)(photoPictureBox.Height / 2 - 22), photoPictureBox.Width, 60),
                    new StringFormat { Alignment = StringAlignment.Center });
                if (photoPictureBox.Image != null) photoPictureBox.Image.Dispose();
                photoPictureBox.Image = new Bitmap(bmp);
            }
        }

        private void PhotoPictureBox_Click(object sender, EventArgs e)
        {
            using (var ofd = new OpenFileDialog())
            {
                ofd.Filter = "Images|*.jpg;*.jpeg;*.png;*.bmp;*.gif";
                if (ofd.ShowDialog() == DialogResult.OK)
                {
                    string photosDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "OrisunIbukun", "photos");
                    Directory.CreateDirectory(photosDir);
                    string destPath = Path.Combine(photosDir, _memberId + Path.GetExtension(ofd.FileName));
                    File.Copy(ofd.FileName, destPath, true);

                    if (photoPictureBox.Image != null) photoPictureBox.Image.Dispose();
                    photoPictureBox.Image = Image.FromFile(destPath);

                    TransactionEngine.UpdateMemberPhoto(_memberId, destPath);
                }
            }
        }

        private void BtnEditProfile_Click(object sender, EventArgs e)
        {
            SetProfileEditMode(true);
        }

        private void BtnSaveProfile_Click(object sender, EventArgs e)
        {
            try
            {
                string dob = dtpDob.Value.ToString("yyyy-MM-dd");
                var (validEmail, emailErr) = Validators.ValidateEmail(txtEmail.Text);
                if (!validEmail) { MessageBox.Show(emailErr, "Validation", MessageBoxButtons.OK, MessageBoxIcon.Warning); return; }
                TransactionEngine.UpdateMemberDetails(_memberId, txtFullName.Text, txtPhone.Text, txtAddress.Text,
                    dob, cmbGender.Text, txtOccupation.Text,
                    txtNextOfKin.Text, txtNextOfKinPhone.Text, txtNotes.Text,
                    txtEmail.Text, cmbIdType.Text, txtIdNumber.Text);

                lblMemberName.Text = txtFullName.Text;
                lblPhone.Text = "Phone: " + txtPhone.Text;
                SetProfileEditMode(false);
                MessageBox.Show("Profile updated successfully.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error saving profile: " + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void SetProfileEditMode(bool editable)
        {
            txtFullName.Enabled = editable;
            txtPhone.Enabled = editable;
            txtAddress.Enabled = editable;
            dtpDob.Enabled = editable;
            cmbGender.Enabled = editable;
            txtOccupation.Enabled = editable;
            txtEmail.Enabled = editable;
            cmbIdType.Enabled = editable;
            txtIdNumber.Enabled = editable;
            txtNextOfKin.Enabled = editable;
            txtNextOfKinPhone.Enabled = editable;
            txtNotes.Enabled = editable;
            btnSaveProfile.Enabled = editable;
            btnEditProfile.Enabled = !editable;
        }

        private void BtnUploadDocument_Click(object sender, EventArgs e)
        {
            using (var ofd = new OpenFileDialog())
            {
                ofd.Filter = "All Files|*.*";
                if (ofd.ShowDialog() == DialogResult.OK)
                {
                    try
                    {
                        string docsDir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "OrisunIbukun", "documents");
                        Directory.CreateDirectory(docsDir);
                        string destPath = Path.Combine(docsDir, _memberId + "_" + Path.GetFileName(ofd.FileName));
                        File.Copy(ofd.FileName, destPath, true);

                        FileInfo fi = new FileInfo(destPath);
                        TransactionEngine.UploadDocument(_memberId, cmbDocType.SelectedItem?.ToString() ?? "General",
                            Path.GetFileName(ofd.FileName), destPath, fi.Length, _currentUser["id"].ToString());

                        LoadDocuments();
                        MessageBox.Show("Document uploaded successfully.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show("Error uploading document: " + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }
            }
        }

        private string GetSelectedDocFilePath()
        {
            if (dgvDocuments.CurrentRow == null) return "";
            var filePath = dgvDocuments.CurrentRow.Cells["File Path"].Value;
            return filePath?.ToString() ?? "";
        }

        private void BtnViewDocument_Click(object sender, EventArgs e)
        {
            string filePath = GetSelectedDocFilePath();
            if (string.IsNullOrEmpty(filePath) || !File.Exists(filePath))
            {
                MessageBox.Show("File not found on disk.", "Info", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            try
            {
                Process.Start(new ProcessStartInfo { FileName = filePath, UseShellExecute = true });
            }
            catch (Exception ex)
            {
                MessageBox.Show("Error opening document: " + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void BtnDeleteDocument_Click(object sender, EventArgs e)
        {
            if (dgvDocuments.CurrentRow == null) return;
            var docId = dgvDocuments.CurrentRow.Cells["Doc ID"].Value;
            if (docId == null) return;

            if (MessageBox.Show("Are you sure you want to delete this document?", "Confirm Delete",
                MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes)
            {
                try
                {
                    TransactionEngine.DeleteDocument(docId.ToString());
                    LoadDocuments();
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Error deleting document: " + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void BtnNewForm_Click(object sender, EventArgs e)
        {
            using (var formDialog = new Form())
            {
                formDialog.Text = "New Digital Form";
                formDialog.Size = new Size(400, 200);
                formDialog.StartPosition = FormStartPosition.CenterParent;
                formDialog.FormBorderStyle = FormBorderStyle.FixedDialog;
                formDialog.MaximizeBox = false;
                formDialog.MinimizeBox = false;

                var lblType = new Label { Text = "Form Type:", Location = new Point(20, 30), AutoSize = true };
                formDialog.Controls.Add(lblType);

                var cmbFormType = new ComboBox
                {
                    Location = new Point(120, 27),
                    Size = new Size(240, 25),
                    DropDownStyle = ComboBoxStyle.DropDownList
                };
                cmbFormType.Items.AddRange(new object[]
                {
                    "Registration Form",
                    "Withdrawal Form",
                    "Loan Application",
                    "Guarantor Form",
                    "Use of Loan Form"
                });
                cmbFormType.SelectedIndex = 0;
                formDialog.Controls.Add(cmbFormType);

                var btnOk = new Button
                {
                    Text = "Create",
                    Location = new Point(120, 80),
                    Size = new Size(100, 35),
                    BackColor = Blue,
                    ForeColor = Color.White,
                    DialogResult = DialogResult.OK
                };
                formDialog.Controls.Add(btnOk);

                var btnCancel = new Button
                {
                    Text = "Cancel",
                    Location = new Point(240, 80),
                    Size = new Size(100, 35),
                    DialogResult = DialogResult.Cancel
                };
                formDialog.Controls.Add(btnCancel);

                formDialog.AcceptButton = btnOk;
                formDialog.CancelButton = btnCancel;

                if (formDialog.ShowDialog() == DialogResult.OK)
                {
                    string formType = cmbFormType.SelectedItem.ToString();
                    OpenFormEditor(formType);
                }
            }
        }

        private void OpenFormEditor(string formType)
        {
            using (var editorForm = new Form())
            {
                editorForm.Text = formType + " - Editor";
                editorForm.Size = new Size(600, 500);
                editorForm.StartPosition = FormStartPosition.CenterParent;

                var lblTitle = new Label
                {
                    Text = formType + " - " + lblMemberName.Text,
                    Font = new Font("Segoe UI", 14, FontStyle.Bold),
                    ForeColor = Blue,
                    Location = new Point(20, 10),
                    AutoSize = true
                };
                editorForm.Controls.Add(lblTitle);

                var txtContent = new TextBox
                {
                    Location = new Point(20, 50),
                    Size = new Size(540, 350),
                    Multiline = true,
                    ScrollBars = ScrollBars.Vertical,
                    Font = new Font("Segoe UI", 10)
                };
                editorForm.Controls.Add(txtContent);

                var btnSave = new Button
                {
                    Text = "Save Form",
                    Location = new Point(20, 410),
                    Size = new Size(120, 35),
                    BackColor = Blue,
                    ForeColor = Color.White,
                    FlatStyle = FlatStyle.Flat
                };
                btnSave.Click += (s, ev) =>
                {
                    try
                    {
                        var formData = new Dictionary<string, string>
                        {
                            { "form_type", formType },
                            { "member_id", _memberId },
                            { "content", txtContent.Text },
                            { "created_date", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") }
                        };

                        string json = JsonSerializer.Serialize(formData);
                        TransactionEngine.SaveDigitalForm(_memberId, formType, json, _currentUser["id"].ToString());
                        LoadForms();
                        editorForm.Close();
                        MessageBox.Show("Form saved successfully.", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show("Error saving form: " + ex.Message, "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                };
                editorForm.Controls.Add(btnSave);

                editorForm.ShowDialog();
            }
        }

        private void BtnPrintProfile_Click(object sender, EventArgs e)
        {
            using (var pd = new PrintDocument())
            {
                pd.PrintPage += Pd_PrintPage;
                using (var ppd = new PrintPreviewDialog { Document = pd })
                {
                    ppd.ShowDialog(this);
                }
            }
        }

        private void Pd_PrintPage(object sender, PrintPageEventArgs e)
        {
            Graphics g = e.Graphics;
            float yPos = 20;
            float leftMargin = 20;

            g.DrawString("ORISUN IBUKUN COOPERATIVE", new Font("Segoe UI", 16, FontStyle.Bold), Brushes.Blue, leftMargin, yPos);
            yPos += 40;
            g.DrawString("Member Profile Report", new Font("Segoe UI", 12), Brushes.Black, leftMargin, yPos);
            yPos += 30;

            g.DrawLine(Pens.Blue, leftMargin, yPos, 780, yPos);
            yPos += 20;

            g.DrawString("Full Name: " + txtFullName.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Member Number: " + lblMemberNumber.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Member ID: " + _memberId, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Phone: " + txtPhone.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Address: " + txtAddress.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Date of Birth: " + dtpDob.Value.ToString("yyyy-MM-dd"), new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Gender: " + cmbGender.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Occupation: " + txtOccupation.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Email: " + txtEmail.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("ID: " + cmbIdType.Text + " " + txtIdNumber.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Next of Kin: " + txtNextOfKin.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Next of Kin Phone: " + txtNextOfKinPhone.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Date Joined: " + lblDateJoined.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Status: " + lblStatus.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 35;

            g.DrawLine(Pens.Blue, leftMargin, yPos, 780, yPos);
            yPos += 20;

            g.DrawString("Financial Summary", new Font("Segoe UI", 12, FontStyle.Bold), Brushes.Blue, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Total Savings: " + lblTotalSavings.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Total Shares: " + lblTotalShares.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Share Count: " + lblShareCount.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Active Loan: " + lblActiveLoanAmount.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Total Repaid: " + lblTotalRepaid.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
            yPos += 25;
            g.DrawString("Outstanding: " + lblOutstandingBalance.Text, new Font("Segoe UI", 10), Brushes.Black, leftMargin, yPos);
        }
    }
}