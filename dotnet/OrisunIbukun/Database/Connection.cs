using System;
using System.IO;
using Microsoft.Data.Sqlite;

namespace OrisunIbukun.Database
{
    public static class Connection
    {
        private static string? _dbPath;
        private static readonly object _lock = new object();

        public static string DbPath
        {
            get
            {
                if (_dbPath == null)
                {
                    string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
                    string dir = Path.Combine(appData, "OrisunIbukun");
                    if (!Directory.Exists(dir))
                        Directory.CreateDirectory(dir);
                    _dbPath = Path.Combine(dir, "orisun_ibukun.db");
                }
                return _dbPath;
            }
        }

        public static SqliteConnection GetConnection()
        {
            var connection = new SqliteConnection($"Data Source={DbPath}");
            connection.Open();

            using (var cmd = connection.CreateCommand())
            {
                cmd.CommandText = "PRAGMA journal_mode=WAL; PRAGMA foreign_keys=ON;";
                cmd.ExecuteNonQuery();
            }

            return connection;
        }
    }
}
