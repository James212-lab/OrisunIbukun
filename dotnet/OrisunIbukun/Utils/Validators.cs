using System;

namespace OrisunIbukun.Utils
{
    public static class Validators
    {
        public static (bool valid, double amount) ValidateAmount(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
                return (false, 0);

            string cleaned = value.Replace("₦", "").Replace(",", "").Trim();
            if (double.TryParse(cleaned, out double amount) && amount > 0)
                return (true, amount);

            return (false, 0);
        }

        public static (bool valid, string error) ValidateRequired(string value, string fieldName)
        {
            if (string.IsNullOrWhiteSpace(value))
                return (false, $"{fieldName} is required");
            return (true, "");
        }

        public static (bool valid, string error) ValidateDate(string value, string fieldName)
        {
            if (string.IsNullOrWhiteSpace(value))
                return (false, $"{fieldName} is required");
            if (!DateTime.TryParse(value, out _))
                return (false, $"{fieldName} must be a valid date");
            return (true, "");
        }

        public static (bool valid, string error) ValidatePin(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
                return (false, "PIN is required");
            string pin = value.Trim();
            if (pin.Length < 4 || pin.Length > 6 || !IsAllDigits(pin))
                return (false, "PIN must be 4-6 digits");
            return (true, "");
        }

        public static (bool valid, string error) ValidatePhone(string value, string fieldName = "Phone")
        {
            if (string.IsNullOrWhiteSpace(value))
                return (true, "");
            int digits = 0;
            foreach (char c in value.Trim())
                if (char.IsDigit(c)) digits++;
            if (digits < 7)
                return (false, $"{fieldName} must contain at least 7 digits");
            return (true, "");
        }

        public static (bool valid, string error) ValidateName(string value, string fieldName = "Full Name")
        {
            if (string.IsNullOrWhiteSpace(value))
                return (false, $"{fieldName} is required");
            string name = value.Trim();
            if (name.Length < 2)
                return (false, $"{fieldName} must be at least 2 characters");
            foreach (char c in name)
            {
                if (!(char.IsLetter(c) || char.IsDigit(c) || c == ' ' || c == '.' || c == '-' || c == '\'' || c == ','))
                    return (false, $"{fieldName} contains invalid characters");
            }
            return (true, "");
        }

        public static (bool valid, string error) ValidateEmail(string value)
        {
            if (string.IsNullOrWhiteSpace(value))
                return (true, "");
            string email = value.Trim().ToLower();
            int at = email.IndexOf('@');
            if (at <= 0 || at != email.LastIndexOf('@') || !email.Substring(at).Contains("."))
                return (false, "Invalid email address");
            return (true, "");
        }

        private static bool IsAllDigits(string value)
        {
            if (value.Length == 0) return false;
            foreach (char c in value)
                if (!char.IsDigit(c)) return false;
            return true;
        }
    }
}
