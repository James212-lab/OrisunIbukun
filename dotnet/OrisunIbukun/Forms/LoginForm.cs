using System;
using System.Drawing;
using System.Windows.Forms;
using OrisunIbukun.Database;
using OrisunIbukun.Utils;

namespace OrisunIbukun.Forms
{
    public class LoginForm : Form
    {
        private static readonly Color Blue = Color.FromArgb(21, 101, 192);
        private static readonly Color LightBlue = Color.FromArgb(227, 242, 253);
        private static readonly Color White = Color.White;

        private TextBox txtUsername = null!;
        private TextBox txtPin = null!;
        private Label lblError = null!;

        public LoginForm()
        {
            InitializeComponent();
            ShowInitialPin();
        }

        private void ShowInitialPin()
        {
            try
            {
                string pin = Schema.GetSetting("initial_admin_pin");
                if (!string.IsNullOrEmpty(pin))
                {
                    MessageBox.Show(this,
                        $"Initial admin account created.\n\nUsername:  admin\nPIN:  {pin}\n\nPlease note this PIN and change it in Settings after logging in.",
                        "First-Time Setup", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    using var conn = Connection.GetConnection();
                    using var cmd = conn.CreateCommand();
                    cmd.CommandText = "DELETE FROM settings WHERE key='initial_admin_pin'";
                    cmd.ExecuteNonQuery();
                }
            }
            catch { }
        }

        private void InitializeComponent()
        {
            SuspendLayout();

            BackColor = LightBlue;
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;
            ClientSize = new Size(450, 420);

            var panelTop = new Panel
            {
                Dock = DockStyle.Top,
                Height = 120,
                BackColor = Blue
            };

            var lblTitle = new Label
            {
                Text = "ORISUN IBUKUN",
                ForeColor = White,
                Font = new Font("Segoe UI", 22, FontStyle.Bold),
                AutoSize = false,
                Width = 450,
                Height = 60,
                TextAlign = ContentAlignment.MiddleCenter,
                Top = 15,
                Left = 0
            };

            var lblSubtitle = new Label
            {
                Text = "Owode Unit – Offline Cooperative Management System",
                ForeColor = White,
                Font = new Font("Segoe UI", 10),
                AutoSize = false,
                Width = 450,
                Height = 30,
                TextAlign = ContentAlignment.MiddleCenter,
                Top = 75,
                Left = 0
            };

            panelTop.Controls.Add(lblTitle);
            panelTop.Controls.Add(lblSubtitle);

            var lblUser = new Label
            {
                Text = "Username",
                Font = new Font("Segoe UI", 11),
                ForeColor = Blue,
                AutoSize = true,
                Top = 145,
                Left = 50
            };

            txtUsername = new TextBox
            {
                Font = new Font("Segoe UI", 13),
                Width = 340,
                Height = 35,
                Top = 175,
                Left = 50,
                Text = "admin"
            };

            var lblPin = new Label
            {
                Text = "PIN",
                Font = new Font("Segoe UI", 11),
                ForeColor = Blue,
                AutoSize = true,
                Top = 220,
                Left = 50
            };

            txtPin = new TextBox
            {
                Font = new Font("Segoe UI", 13),
                Width = 340,
                Height = 35,
                Top = 250,
                Left = 50,
                UseSystemPasswordChar = true
            };

            var btnLogin = new Button
            {
                Text = "LOGIN",
                Font = new Font("Segoe UI", 14, FontStyle.Bold),
                BackColor = Blue,
                ForeColor = White,
                FlatStyle = FlatStyle.Flat,
                Width = 340,
                Height = 50,
                Top = 305,
                Left = 50,
                Cursor = Cursors.Hand
            };
            btnLogin.FlatAppearance.BorderSize = 0;
            btnLogin.Click += BtnLogin_Click;

            lblError = new Label
            {
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.Red,
                AutoSize = true,
                Top = 365,
                Left = 50,
                Text = ""
            };

            Controls.Add(panelTop);
            Controls.Add(lblUser);
            Controls.Add(txtUsername);
            Controls.Add(lblPin);
            Controls.Add(txtPin);
            Controls.Add(btnLogin);
            Controls.Add(lblError);

            ResumeLayout(false);
            PerformLayout();
        }

        private void BtnLogin_Click(object? sender, EventArgs e)
        {
            lblError.Text = "";

            if (string.IsNullOrWhiteSpace(txtUsername.Text))
            {
                lblError.Text = "Please enter username";
                return;
            }

            if (string.IsNullOrWhiteSpace(txtPin.Text))
            {
                lblError.Text = "Please enter PIN";
                return;
            }

            string pinHash = Helpers.HashPin(txtPin.Text.Trim());

            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT id, full_name, role FROM users WHERE username=@u AND pin_hash=@p AND is_active=1";
            cmd.Parameters.AddWithValue("@u", txtUsername.Text.Trim());
            cmd.Parameters.AddWithValue("@p", pinHash);

            using var reader = cmd.ExecuteReader();
            if (reader.Read())
            {
                string userId = reader.GetString(0);
                string fullName = reader.GetString(1);
                string role = reader.GetString(2);

                Engine.TransactionEngine.UpdateLastLogin(userId);
                Engine.TransactionEngine.LogAudit(userId, "Login", $"User {txtUsername.Text.Trim()} logged in");

                var mainForm = new MainForm(userId, fullName, role);
                mainForm.FormClosed += (s, args) => Close();
                mainForm.Show();
                Hide();
            }
            else
            {
                lblError.Text = "Invalid username or PIN";
            }
        }
    }
}
