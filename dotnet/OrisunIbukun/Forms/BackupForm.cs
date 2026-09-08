using System;
using System.Drawing;
using System.Windows.Forms;
using OrisunIbukun.Engine;
using OrisunIbukun.Utils;

namespace OrisunIbukun.Forms
{
    public class BackupForm : UserControl
    {
        private static readonly Color Blue = Color.FromArgb(21, 101, 192);
        private static readonly Color LightBlue = Color.FromArgb(227, 242, 253);
        private static readonly Color White = Color.White;

        private readonly string _userId;
        private Label lblStatus = null!;
        private DataGridView dgvBackups = null!;
        private Label lblMsg = null!;

        public BackupForm(string userId)
        {
            _userId = userId;
            BackColor = LightBlue;
            InitializeForm();
            LoadBackups();
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
                Text = "Backup & Restore",
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
                Height = 110,
                BackColor = LightBlue
            };

            lblStatus = new Label
            {
                Text = "",
                Font = new Font("Segoe UI", 10),
                ForeColor = Color.FromArgb(50, 50, 50),
                AutoSize = true,
                Top = 5,
                Left = 15
            };
            pnlButtons.Controls.Add(lblStatus);

            var btnBackup = CreateButton("BACK UP NOW", 15, 35, 200, 45);
            btnBackup.Click += BtnBackup_Click;
            pnlButtons.Controls.Add(btnBackup);

            var btnRefresh = CreateButton("REFRESH", 225, 35, 100, 45);
            btnRefresh.Click += (s, e) => LoadBackups();
            pnlButtons.Controls.Add(btnRefresh);

            var btnRestore = CreateButton("RESTORE SELECTED", 335, 35, 180, 45);
            btnRestore.Click += BtnRestore_Click;
            btnRestore.BackColor = Color.FromArgb(183, 28, 28);
            pnlButtons.Controls.Add(btnRestore);
            Controls.Add(pnlButtons);

            dgvBackups = new DataGridView
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
            Controls.Add(dgvBackups);

            lblMsg = new Label
            {
                Dock = DockStyle.Bottom,
                Font = new Font("Segoe UI", 10),
                Height = 30,
                BackColor = LightBlue
            };
            Controls.Add(lblMsg);
        }

        private void BtnBackup_Click(object? sender, EventArgs e)
        {
            var btn = (Button)sender!;
            btn.Enabled = false;
            string oldText = btn.Text;
            btn.Text = "Backing up...";
            try
            {
                string path = BackupEngine.CreateBackup(_userId);
                TransactionEngine.LogAudit(_userId, "Backup", $"Manual backup created: {path}");
                lblMsg.ForeColor = Color.Green;
                lblMsg.Text = $"Backup created: {path}";
                lblStatus.Text = $"Last Backup: {DateTime.Now:yyyy-MM-dd HH:mm:ss}";
                LoadBackups();
            }
            catch (Exception ex)
            {
                lblMsg.ForeColor = Color.Red;
                lblMsg.Text = $"Backup failed: {ex.Message}";
            }
            finally
            {
                btn.Enabled = true;
                btn.Text = oldText;
            }
        }

        private void BtnRestore_Click(object? sender, EventArgs e)
        {
            if (dgvBackups.CurrentRow == null)
            {
                lblMsg.ForeColor = Color.Red;
                lblMsg.Text = "Select a backup to restore";
                return;
            }

            string path = dgvBackups.CurrentRow.Cells["file_path"].Value?.ToString() ?? "";
            if (string.IsNullOrEmpty(path) || !System.IO.File.Exists(path))
            {
                lblMsg.ForeColor = Color.Red;
                lblMsg.Text = "Backup file not found on disk";
                return;
            }

            var (valid, error) = BackupEngine.ValidateBackup(path);
            if (!valid)
            {
                lblMsg.ForeColor = Color.Red;
                lblMsg.Text = "Restore blocked: " + error;
                MessageBox.Show("This backup cannot be restored.\n\n" + error, "Incompatible Backup",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            var confirm = MessageBox.Show(
                "Are you sure you want to restore this backup?\n\nA safety backup of the current data will be created first, then ALL current data will be replaced.\nYou will need to restart the application after restore.",
                "Confirm Restore", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);
            if (confirm != DialogResult.Yes) return;

            try
            {
                string safety = BackupEngine.CreateBackup(_userId);
                BackupEngine.RestoreBackup(path);
                TransactionEngine.LogAudit(_userId, "Restore", $"Database restored from {path}. Safety backup: {safety}");
                lblMsg.ForeColor = Color.Green;
                lblMsg.Text = "Database restored successfully! Please restart the application.";
                if (MessageBox.Show("Database restored. Restart the application now?", "Success",
                    MessageBoxButtons.YesNo, MessageBoxIcon.Information) == DialogResult.Yes)
                {
                    Application.Restart();
                }
            }
            catch (Exception ex)
            {
                lblMsg.ForeColor = Color.Red;
                lblMsg.Text = $"Restore failed: {ex.Message}";
            }
        }

        private void LoadBackups()
        {
            var backups = BackupEngine.ListBackups();
            var dt = new System.Data.DataTable();
            dt.Columns.Add("id", typeof(string));
            dt.Columns.Add("filename", typeof(string));
            dt.Columns.Add("file_size", typeof(string));
            dt.Columns.Add("created_at", typeof(string));
            dt.Columns.Add("file_path", typeof(string));

            string latest = "";
            foreach (var b in backups)
            {
                string size = b.ContainsKey("file_size") ? $"{Convert.ToInt64(b["file_size"]) / 1024} KB" : "0 KB";
                dt.Rows.Add(b["id"], b["filename"], size, b["created_at"], b["file_path"]);
                if (string.IsNullOrEmpty(latest) && b.ContainsKey("created_at") && b["created_at"] != null)
                    latest = b["created_at"]!.ToString()!;
            }

            dgvBackups.DataSource = dt;
            if (dgvBackups.Columns.Contains("id")) dgvBackups.Columns["id"].Visible = false;
            if (dgvBackups.Columns.Contains("file_path")) dgvBackups.Columns["file_path"].Visible = false;
            lblStatus.Text = string.IsNullOrEmpty(latest) ? "Last Backup: Never" : $"Last Backup: {latest}";
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
