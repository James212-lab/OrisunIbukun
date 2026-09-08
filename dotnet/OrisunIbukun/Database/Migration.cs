using Microsoft.Data.Sqlite;

namespace OrisunIbukun.Database
{
    public static class Migration
    {
        public static void Run()
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();

            AddColumnIfMissing(cmd, "members", "date_of_birth", "TEXT");
            AddColumnIfMissing(cmd, "members", "gender", "TEXT");
            AddColumnIfMissing(cmd, "members", "occupation", "TEXT");
            AddColumnIfMissing(cmd, "members", "next_of_kin", "TEXT");
            AddColumnIfMissing(cmd, "members", "next_of_kin_phone", "TEXT");
            AddColumnIfMissing(cmd, "members", "status", "TEXT DEFAULT 'Active'");
            AddColumnIfMissing(cmd, "members", "photo_path", "TEXT");
            AddColumnIfMissing(cmd, "members", "notes", "TEXT");
            AddColumnIfMissing(cmd, "members", "email", "TEXT");
            AddColumnIfMissing(cmd, "members", "id_type", "TEXT");
            AddColumnIfMissing(cmd, "members", "id_number", "TEXT");

            AddColumnIfMissing(cmd, "users", "is_active", "INTEGER NOT NULL DEFAULT 1");
            AddColumnIfMissing(cmd, "users", "last_login", "TEXT");

            AddColumnIfMissing(cmd, "loan_guarantors", "guarantee_amount", "REAL NOT NULL DEFAULT 0");
        }

        private static void AddColumnIfMissing(SqliteCommand cmd, string table, string column, string dataType)
        {
            cmd.CommandText = $"PRAGMA table_info({table})";
            using var reader = cmd.ExecuteReader();
            bool exists = false;
            while (reader.Read())
            {
                if (reader.IsDBNull(1) ? false : reader.GetString(1) == column)
                {
                    exists = true;
                    break;
                }
            }
            reader.Close();

            if (!exists)
            {
                cmd.CommandText = $"ALTER TABLE {table} ADD COLUMN {column} {dataType}";
                cmd.ExecuteNonQuery();
            }
        }
    }
}
