using System;
using System.Security.Cryptography;
using System.Text;

namespace OrisunIbukun.Utils
{
    public static class Helpers
    {
        public static string GenerateId(string prefix)
        {
            return $"{prefix}_{DateTime.Now:yyyyMMddHHmmssfff}_{new Random().Next(1000, 9999)}";
        }

        public static string HashPin(string pin)
        {
            using var sha256 = SHA256.Create();
            byte[] bytes = sha256.ComputeHash(Encoding.UTF8.GetBytes(pin));
            var sb = new StringBuilder();
            foreach (byte b in bytes)
                sb.Append(b.ToString("x2"));
            return sb.ToString();
        }

        public static string FormatCurrency(double amount)
        {
            string currency = Database.Schema.GetSetting("currency");
            if (string.IsNullOrEmpty(currency)) currency = "₦";
            if (amount < 0) return $"-{currency}{Math.Abs(amount):N0}";
            return $"{currency}{amount:N0}";
        }

        public static string TodayStr()
        {
            return DateTime.Now.ToString("yyyy-MM-dd");
        }

        public static string NowStr()
        {
            return DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
        }
    }
}
