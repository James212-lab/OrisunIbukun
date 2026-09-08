using System;
using System.Collections.Generic;
using System.IO;
using Microsoft.Data.Sqlite;
using OrisunIbukun.Database;
using OrisunIbukun.Utils;

namespace OrisunIbukun.Engine
{
    public static class BackupEngine
    {
        private static string BackupDir
        {
            get
            {
                string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
                string dir = Path.Combine(appData, "OrisunIbukun", "backups");
                if (!Directory.Exists(dir))
                    Directory.CreateDirectory(dir);
                return dir;
            }
        }

        public static string CreateBackup(string createdBy)
        {
            string timestamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
            string backupFile = Path.Combine(BackupDir, $"orisun_ibukun_{timestamp}.db");
            string sourceDb = Connection.DbPath;

            if (!File.Exists(sourceDb))
                throw new Exception("Database file not found");

            File.Copy(sourceDb, backupFile, true);

            var fileInfo = new FileInfo(backupFile);
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"INSERT INTO backups (id, filename, file_path, file_size, created_by) 
                VALUES (@id, @fname, @fpath, @fsize, @creator)";
            cmd.Parameters.AddWithValue("@id", Helpers.GenerateId("bkp"));
            cmd.Parameters.AddWithValue("@fname", Path.GetFileName(backupFile));
            cmd.Parameters.AddWithValue("@fpath", backupFile);
            cmd.Parameters.AddWithValue("@fsize", fileInfo.Length);
            cmd.Parameters.AddWithValue("@creator", createdBy);
            cmd.ExecuteNonQuery();

            return backupFile;
        }

        public static List<Dictionary<string, object>> ListBackups()
        {
            var backups = new List<Dictionary<string, object>>();
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"SELECT b.*, u.full_name as created_by_name FROM backups b 
                LEFT JOIN users u ON b.created_by=u.id ORDER BY b.created_at DESC";
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                var item = new Dictionary<string, object>();
                for (int i = 0; i < reader.FieldCount; i++)
                    item[reader.GetName(i)] = reader.GetValue(i);
                backups.Add(item);
            }
            return backups;
        }

        public static void RestoreBackup(string backupPath)
        {
            if (!File.Exists(backupPath))
                throw new Exception("Backup file not found");

            string targetDb = Connection.DbPath;
            File.Copy(backupPath, targetDb, true);
        }

        public static (bool ok, string error) ValidateBackup(string backupPath)
        {
            try
            {
                if (!File.Exists(backupPath))
                    return (false, "Backup file not found");
                using var conn = new SqliteConnection($"Data Source={backupPath};Mode=ReadOnly");
                conn.Open();
                string[] requiredTables = { "members", "transactions", "users", "savings", "shares", "loans" };
                foreach (var table in requiredTables)
                {
                    using var cmd = conn.CreateCommand();
                    cmd.CommandText = "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=@t";
                    cmd.Parameters.AddWithValue("@t", table);
                    if (Convert.ToInt32(cmd.ExecuteScalar()) == 0)
                        return (false, $"Backup is incompatible: table '{table}' is missing. This backup was made by a different app version.");
                }
                var requiredColumns = new (string table, string column)[]
                {
                    ("members", "member_number"),
                    ("transactions", "transaction_date"),
                    ("transactions", "type"),
                    ("loans", "total_payable"),
                };
                foreach (var (table, column) in requiredColumns)
                {
                    using var cmd = conn.CreateCommand();
                    cmd.CommandText = $"SELECT COUNT(*) FROM pragma_table_info(@t) WHERE name=@c";
                    cmd.Parameters.AddWithValue("@t", table);
                    cmd.Parameters.AddWithValue("@c", column);
                    if (Convert.ToInt32(cmd.ExecuteScalar()) == 0)
                        return (false, $"Backup is incompatible: '{table}.{column}' is missing. This backup was made by a different app version.");
                }
                return (true, "");
            }
            catch (Exception ex)
            {
                return (false, ex.Message);
            }
        }
    }
}
