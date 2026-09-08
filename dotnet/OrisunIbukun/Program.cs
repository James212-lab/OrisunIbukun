using System;
using System.IO;
using System.Threading;
using System.Windows.Forms;

namespace OrisunIbukun
{
    static class Program
    {
        private static Mutex? _instanceMutex;

        [STAThread]
        static void Main()
        {
            try
            {
                _instanceMutex = new Mutex(true, "OrisunIbukun_OwodeUnit_SingleInstance", out bool isFirst);
                if (!isFirst)
                {
                    MessageBox.Show("ORISUN IBUKUN is already running.\n\nPlease use the open window (check the taskbar) instead of starting a new one.",
                        "Already Running", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    return;
                }

                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                Application.SetHighDpiMode(HighDpiMode.SystemAware);
                Application.ThreadException += (s, e) =>
                {
                    string log = WriteCrashLog(e.Exception.ToString());
                    MessageBox.Show($"An unexpected error occurred.\n\n{e.Exception.Message}\n\nDetails saved to:\n{log}",
                        "Application Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                };

                Database.Schema.Create();
                Database.Migration.Run();

                if (!ValidateStartup())
                {
                    MessageBox.Show("Database schema validation failed. Please check the crash log and restart.",
                        "Database Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    return;
                }

                Application.Run(new Forms.LoginForm());
            }
            catch (Exception ex)
            {
                string log = WriteCrashLog(ex.ToString());
                MessageBox.Show($"Failed to start application:\n\n{ex.Message}\n\nDetails saved to:\n{log}",
                    "Application Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private static bool ValidateStartup()
        {
            try
            {
                string[] criticalTables = {
                    "users", "roles", "members", "meetings", "attendance",
                    "transactions", "savings", "shares", "loans", "loan_repayments",
                    "expenses", "headquarters_remittances", "audit_logs", "backups", "settings"
                };
                using var conn = Database.Connection.GetConnection();
                using var cmd = conn.CreateCommand();
                foreach (var table in criticalTables)
                {
                    cmd.CommandText = "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=@t";
                    cmd.Parameters.Clear();
                    cmd.Parameters.AddWithValue("@t", table);
                    if (Convert.ToInt32(cmd.ExecuteScalar()) == 0)
                        return false;
                }
                return true;
            }
            catch
            {
                return false;
            }
        }

        public static string WriteCrashLog(string text)
        {
            try
            {
                string dir = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "OrisunIbukun");
                Directory.CreateDirectory(dir);
                string logPath = Path.Combine(dir, "crash.log");
                File.AppendAllText(logPath, $"\n===== {DateTime.Now:yyyy-MM-ddTHH:mm:ss} =====\n{text}\n");
                return logPath;
            }
            catch
            {
                return "";
            }
        }
    }
}
