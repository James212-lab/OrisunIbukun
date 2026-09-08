using System;
using System.Collections.Generic;
using Microsoft.Data.Sqlite;
using OrisunIbukun.Database;
using OrisunIbukun.Utils;

namespace OrisunIbukun.Engine
{
    public static class TransactionEngine
    {
public static string RegisterMember(string fullName, string phone, string address, double entranceFee, string dateJoined, string recordedBy,
            string dateOfBirth = "", string gender = "", string occupation = "", string email = "",
            string nextOfKin = "", string nextOfKinPhone = "", string idType = "", string idNumber = "")
        {
            using var conn = Connection.GetConnection();
            using var transaction = conn.BeginTransaction();

            string memberId = Helpers.GenerateId("mem");
            string memberNumber = "M" + DateTime.Now.ToString("yyyyMMddHHmmss").Substring(2);

            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"INSERT INTO members (id, member_number, full_name, phone, address, entrance_fee, date_joined,
                    date_of_birth, gender, occupation, email, next_of_kin, next_of_kin_phone, id_type, id_number)
                    VALUES (@id, @mnum, @fname, @phone, @addr, @efee, @djoin,
                    @dob, @gender, @occ, @email, @nok, @nokp, @idtype, @idnum)";
                cmd.Parameters.AddWithValue("@id", memberId);
                cmd.Parameters.AddWithValue("@mnum", memberNumber);
                cmd.Parameters.AddWithValue("@fname", fullName);
                cmd.Parameters.AddWithValue("@phone", phone ?? "");
                cmd.Parameters.AddWithValue("@addr", address ?? "");
                cmd.Parameters.AddWithValue("@efee", entranceFee);
                cmd.Parameters.AddWithValue("@djoin", dateJoined);
                cmd.Parameters.AddWithValue("@dob", dateOfBirth ?? "");
                cmd.Parameters.AddWithValue("@gender", gender ?? "");
                cmd.Parameters.AddWithValue("@occ", occupation ?? "");
                cmd.Parameters.AddWithValue("@email", email ?? "");
                cmd.Parameters.AddWithValue("@nok", nextOfKin ?? "");
                cmd.Parameters.AddWithValue("@nokp", nextOfKinPhone ?? "");
                cmd.Parameters.AddWithValue("@idtype", idType ?? "");
                cmd.Parameters.AddWithValue("@idnum", idNumber ?? "");
                cmd.ExecuteNonQuery();
            }

            if (entranceFee > 0)
            {
                string txId = Helpers.GenerateId("txn");
                using (var cmd = conn.CreateCommand())
                {
                    cmd.Transaction = transaction;
                    cmd.CommandText = @"INSERT INTO transactions (id, member_id, type, amount, description, recorded_by, transaction_date) 
                        VALUES (@id, @mid, 'Entrance Fee', @amt, 'Entrance fee payment', @rec, @date)";
                    cmd.Parameters.AddWithValue("@id", txId);
                    cmd.Parameters.AddWithValue("@mid", memberId);
                    cmd.Parameters.AddWithValue("@amt", entranceFee);
                    cmd.Parameters.AddWithValue("@rec", recordedBy);
                    cmd.Parameters.AddWithValue("@date", dateJoined);
                    cmd.ExecuteNonQuery();
                }
            }

            transaction.Commit();
            return memberId;
        }

        public static string RecordSavings(string memberId, double amount, string method, string notes, string recordedBy, string savingsDate, double shareSplitPercent = 50)
        {
            using var conn = Connection.GetConnection();
            using var transaction = conn.BeginTransaction();

            double shareAmount = amount * shareSplitPercent / 100.0;
            double savingsAmount = amount - shareAmount;

            double currentSavingsBalance = 0;
            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM savings WHERE member_id=@mid";
                cmd.Parameters.AddWithValue("@mid", memberId);
                currentSavingsBalance = Convert.ToDouble(cmd.ExecuteScalar());
            }

            int currentShareCount = 0;
            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = "SELECT COALESCE(SUM(shares_count), 0) FROM shares WHERE member_id=@mid";
                cmd.Parameters.AddWithValue("@mid", memberId);
                currentShareCount = Convert.ToInt32(cmd.ExecuteScalar());
            }

            double sharePrice = 1000;
            var priceStr = Schema.GetSetting("share_price");
            if (!string.IsNullOrEmpty(priceStr)) double.TryParse(priceStr, out sharePrice);

            int sharesToAdd = shareAmount > 0 ? Math.Max(1, (int)(shareAmount / sharePrice)) : 0;
            double actualShareAmount = sharesToAdd * sharePrice;
            double actualSavingsAmount = amount - actualShareAmount;

            string savingId = Helpers.GenerateId("svg");
            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"INSERT INTO savings (id, member_id, amount, balance, method, notes, recorded_by, savings_date) 
                    VALUES (@id, @mid, @amt, @bal, @method, @notes, @rec, @date)";
                cmd.Parameters.AddWithValue("@id", savingId);
                cmd.Parameters.AddWithValue("@mid", memberId);
                cmd.Parameters.AddWithValue("@amt", actualSavingsAmount);
                cmd.Parameters.AddWithValue("@bal", currentSavingsBalance + actualSavingsAmount);
                cmd.Parameters.AddWithValue("@method", method);
                cmd.Parameters.AddWithValue("@notes", notes ?? "");
                cmd.Parameters.AddWithValue("@rec", recordedBy);
                cmd.Parameters.AddWithValue("@date", savingsDate);
                cmd.ExecuteNonQuery();
            }

            string txId1 = Helpers.GenerateId("txn");
            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"INSERT INTO transactions (id, member_id, type, amount, description, recorded_by, transaction_date) 
                    VALUES (@id, @mid, 'Savings', @amt, @desc, @rec, @date)";
                cmd.Parameters.AddWithValue("@id", txId1);
                cmd.Parameters.AddWithValue("@mid", memberId);
                cmd.Parameters.AddWithValue("@amt", actualSavingsAmount);
                cmd.Parameters.AddWithValue("@desc", $"Savings deposit via {method}");
                cmd.Parameters.AddWithValue("@rec", recordedBy);
                cmd.Parameters.AddWithValue("@date", savingsDate);
                cmd.ExecuteNonQuery();
            }

            if (sharesToAdd > 0)
            {
                string shareId = Helpers.GenerateId("shr");
                using (var cmd = conn.CreateCommand())
                {
                    cmd.Transaction = transaction;
                    cmd.CommandText = @"INSERT INTO shares (id, member_id, shares_count, amount, recorded_by, share_date) 
                        VALUES (@id, @mid, @cnt, @amt, @rec, @date)";
                    cmd.Parameters.AddWithValue("@id", shareId);
                    cmd.Parameters.AddWithValue("@mid", memberId);
                    cmd.Parameters.AddWithValue("@cnt", sharesToAdd);
                    cmd.Parameters.AddWithValue("@amt", actualShareAmount);
                    cmd.Parameters.AddWithValue("@rec", recordedBy);
                    cmd.Parameters.AddWithValue("@date", savingsDate);
                    cmd.ExecuteNonQuery();
                }

                string txId2 = Helpers.GenerateId("txn");
                using (var cmd = conn.CreateCommand())
                {
                    cmd.Transaction = transaction;
                    cmd.CommandText = @"INSERT INTO transactions (id, member_id, type, amount, description, recorded_by, transaction_date) 
                        VALUES (@id, @mid, 'Shares', @amt, @desc, @rec, @date)";
                    cmd.Parameters.AddWithValue("@id", txId2);
                    cmd.Parameters.AddWithValue("@mid", memberId);
                    cmd.Parameters.AddWithValue("@amt", actualShareAmount);
                    cmd.Parameters.AddWithValue("@desc", $"Auto-allocated {sharesToAdd} share(s) from savings");
                    cmd.Parameters.AddWithValue("@rec", recordedBy);
                    cmd.Parameters.AddWithValue("@date", savingsDate);
                    cmd.ExecuteNonQuery();
                }
            }

            transaction.Commit();
            return savingId;
        }

        public static string RecordShare(string memberId, int sharesCount, double amount, string recordedBy, string shareDate)
        {
            using var conn = Connection.GetConnection();
            using var transaction = conn.BeginTransaction();

            string shareId = Helpers.GenerateId("shr");

            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"INSERT INTO shares (id, member_id, shares_count, amount, recorded_by, share_date) 
                    VALUES (@id, @mid, @cnt, @amt, @rec, @date)";
                cmd.Parameters.AddWithValue("@id", shareId);
                cmd.Parameters.AddWithValue("@mid", memberId);
                cmd.Parameters.AddWithValue("@cnt", sharesCount);
                cmd.Parameters.AddWithValue("@amt", amount);
                cmd.Parameters.AddWithValue("@rec", recordedBy);
                cmd.Parameters.AddWithValue("@date", shareDate);
                cmd.ExecuteNonQuery();
            }

            string txId = Helpers.GenerateId("txn");
            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"INSERT INTO transactions (id, member_id, type, amount, description, recorded_by, transaction_date) 
                    VALUES (@id, @mid, 'Shares', @amt, @desc, @rec, @date)";
                cmd.Parameters.AddWithValue("@id", txId);
                cmd.Parameters.AddWithValue("@mid", memberId);
                cmd.Parameters.AddWithValue("@amt", amount);
                cmd.Parameters.AddWithValue("@desc", $"Purchased {sharesCount} share(s)");
                cmd.Parameters.AddWithValue("@rec", recordedBy);
                cmd.Parameters.AddWithValue("@date", shareDate);
                cmd.ExecuteNonQuery();
            }

            transaction.Commit();
            return shareId;
        }

        public static string CreateLoan(string memberId, double amount, double interestRate, string purpose, string appliedDate)
        {
            using var conn = Connection.GetConnection();
            using var transaction = conn.BeginTransaction();

            double totalPayable = amount + (amount * interestRate / 100);
            string loanId = Helpers.GenerateId("lon");

            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"INSERT INTO loans (id, member_id, amount, interest_rate, total_payable, purpose, status, applied_date) 
                    VALUES (@id, @mid, @amt, @int, @total, @purpose, 'Pending', @date)";
                cmd.Parameters.AddWithValue("@id", loanId);
                cmd.Parameters.AddWithValue("@mid", memberId);
                cmd.Parameters.AddWithValue("@amt", amount);
                cmd.Parameters.AddWithValue("@int", interestRate);
                cmd.Parameters.AddWithValue("@total", totalPayable);
                cmd.Parameters.AddWithValue("@purpose", purpose ?? "");
                cmd.Parameters.AddWithValue("@date", appliedDate);
                cmd.ExecuteNonQuery();
            }

            transaction.Commit();
            return loanId;
        }

        public static void ApproveLoan(string loanId, string approvedBy)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"UPDATE loans SET status='Approved', approved_by=@user, approved_date=@date WHERE id=@id AND status='Pending'";
            cmd.Parameters.AddWithValue("@id", loanId);
            cmd.Parameters.AddWithValue("@user", approvedBy);
            cmd.Parameters.AddWithValue("@date", Helpers.TodayStr());
            cmd.ExecuteNonQuery();
        }

        public static void DisburseLoan(string loanId, string disbursedBy)
        {
            using var conn = Connection.GetConnection();
            using var transaction = conn.BeginTransaction();

            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"UPDATE loans SET status='Disbursed', disbursed_by=@user, disbursed_date=@date WHERE id=@id AND status='Approved'";
                cmd.Parameters.AddWithValue("@id", loanId);
                cmd.Parameters.AddWithValue("@user", disbursedBy);
                cmd.Parameters.AddWithValue("@date", Helpers.TodayStr());
                cmd.ExecuteNonQuery();
            }

            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = "SELECT member_id, amount FROM loans WHERE id=@id";
                cmd.Parameters.AddWithValue("@id", loanId);
                using var reader = cmd.ExecuteReader();
                if (reader.Read())
                {
                    string memberId = reader.GetString(0);
                    double amount = reader.GetDouble(1);
                    reader.Close();

                    string txId = Helpers.GenerateId("txn");
                    using var txCmd = conn.CreateCommand();
                    txCmd.Transaction = transaction;
                    txCmd.CommandText = @"INSERT INTO transactions (id, member_id, type, amount, description, recorded_by, transaction_date) 
                        VALUES (@id, @mid, 'Loan Disbursement', @amt, 'Loan disbursed', @rec, @date)";
                    txCmd.Parameters.AddWithValue("@id", txId);
                    txCmd.Parameters.AddWithValue("@mid", memberId);
                    txCmd.Parameters.AddWithValue("@amt", amount);
                    txCmd.Parameters.AddWithValue("@rec", disbursedBy);
                    txCmd.Parameters.AddWithValue("@date", Helpers.TodayStr());
                    txCmd.ExecuteNonQuery();
                }
            }

            transaction.Commit();
        }

        public static string RecordRepayment(string loanId, double amount, string recordedBy, string paymentDate)
        {
            using var conn = Connection.GetConnection();
            using var transaction = conn.BeginTransaction();

            string repaymentId = Helpers.GenerateId("rep");

            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"INSERT INTO loan_repayments (id, loan_id, amount, recorded_by, payment_date) 
                    VALUES (@id, @lid, @amt, @rec, @date)";
                cmd.Parameters.AddWithValue("@id", repaymentId);
                cmd.Parameters.AddWithValue("@lid", loanId);
                cmd.Parameters.AddWithValue("@amt", amount);
                cmd.Parameters.AddWithValue("@rec", recordedBy);
                cmd.Parameters.AddWithValue("@date", paymentDate);
                cmd.ExecuteNonQuery();
            }

            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = "SELECT member_id FROM loans WHERE id=@id";
                cmd.Parameters.AddWithValue("@id", loanId);
                var memberId = cmd.ExecuteScalar()?.ToString() ?? "";

                string txId = Helpers.GenerateId("txn");
                cmd.CommandText = @"INSERT INTO transactions (id, member_id, type, amount, description, recorded_by, transaction_date) 
                    VALUES (@id, @mid, 'Loan Repayment', @amt, 'Loan repayment', @rec, @date)";
                cmd.Parameters.Clear();
                cmd.Parameters.AddWithValue("@id", txId);
                cmd.Parameters.AddWithValue("@mid", memberId);
                cmd.Parameters.AddWithValue("@amt", amount);
                cmd.Parameters.AddWithValue("@rec", recordedBy);
                cmd.Parameters.AddWithValue("@date", paymentDate);
                cmd.ExecuteNonQuery();
            }

            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"UPDATE loans SET status='Completed' WHERE id=@id AND 
                    (SELECT COALESCE(SUM(amount),0) FROM loan_repayments WHERE loan_id=@id) >= total_payable";
                cmd.Parameters.AddWithValue("@id", loanId);
                cmd.ExecuteNonQuery();
            }

            transaction.Commit();
            return repaymentId;
        }

        public static void ReverseTransaction(string transactionId, string reversedBy, string reason)
        {
            using var conn = Connection.GetConnection();
            using var transaction = conn.BeginTransaction();

            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"INSERT INTO transaction_reversals (id, transaction_id, reversed_by, reason) 
                    VALUES (@id, @tid, @rev, @reason)";
                cmd.Parameters.AddWithValue("@id", Helpers.GenerateId("rev"));
                cmd.Parameters.AddWithValue("@tid", transactionId);
                cmd.Parameters.AddWithValue("@rev", reversedBy);
                cmd.Parameters.AddWithValue("@reason", reason);
                cmd.ExecuteNonQuery();
            }

            transaction.Commit();
        }

        public static Dictionary<string, object> GetMemberFinancialSummary(string memberId)
        {
            var summary = new Dictionary<string, object>();

            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();

            cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM savings WHERE member_id=@mid";
            cmd.Parameters.AddWithValue("@mid", memberId);
            summary["TotalSavings"] = Convert.ToDouble(cmd.ExecuteScalar());

            cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM shares WHERE member_id=@mid";
            summary["TotalShares"] = Convert.ToDouble(cmd.ExecuteScalar());

            cmd.CommandText = "SELECT COALESCE(SUM(shares_count), 0) FROM shares WHERE member_id=@mid";
            summary["SharesCount"] = Convert.ToInt32(cmd.ExecuteScalar());

            cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM loans WHERE member_id=@mid AND status IN ('Approved','Disbursed')";
            summary["ActiveLoanAmount"] = Convert.ToDouble(cmd.ExecuteScalar());

            cmd.CommandText = @"SELECT COALESCE(SUM(lr.amount), 0) FROM loan_repayments lr 
                INNER JOIN loans l ON lr.loan_id=l.id WHERE l.member_id=@mid";
            summary["TotalRepaid"] = Convert.ToDouble(cmd.ExecuteScalar());

            cmd.CommandText = "SELECT COUNT(*) FROM attendance WHERE member_id=@mid AND status='Present'";
            summary["MeetingsAttended"] = Convert.ToInt32(cmd.ExecuteScalar());

            return summary;
        }

        public static Dictionary<string, object> GetMonthlySummary(string month, string year)
        {
            var summary = new Dictionary<string, object>();
            string prefix = $"{year}-{month.PadLeft(2, '0')}";

            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();

            cmd.CommandText = "SELECT COUNT(*) FROM members WHERE status='Active'";
            summary["TotalMembers"] = Convert.ToInt32(cmd.ExecuteScalar());

            cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM savings WHERE savings_date LIKE @pfx || '%'";
            cmd.Parameters.AddWithValue("@pfx", prefix);
            summary["MonthlySavings"] = Convert.ToDouble(cmd.ExecuteScalar());

            cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM shares WHERE share_date LIKE @pfx || '%'";
            summary["MonthlyShares"] = Convert.ToDouble(cmd.ExecuteScalar());

            cmd.CommandText = "SELECT COUNT(*) FROM loans WHERE applied_date LIKE @pfx || '%'";
            summary["LoansApplied"] = Convert.ToInt32(cmd.ExecuteScalar());

            cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM loan_repayments WHERE payment_date LIKE @pfx || '%'";
            summary["LoanRepayments"] = Convert.ToDouble(cmd.ExecuteScalar());

            cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE expense_date LIKE @pfx || '%'";
            summary["Expenses"] = Convert.ToDouble(cmd.ExecuteScalar());

            cmd.CommandText = "SELECT COALESCE(SUM(amount), 0) FROM headquarters_remittances WHERE remittance_date LIKE @pfx || '%'";
            summary["Remittances"] = Convert.ToDouble(cmd.ExecuteScalar());

            return summary;
        }

        public static string CreateMeeting(string meetingDate, string notes, string createdBy)
        {
            using var conn = Connection.GetConnection();
            using var transaction = conn.BeginTransaction();

            int meetingNum = 1;
            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = "SELECT COALESCE(MAX(meeting_number), 0) + 1 FROM meetings";
                meetingNum = Convert.ToInt32(cmd.ExecuteScalar());
            }

            string meetingId = Helpers.GenerateId("mtg");
            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"INSERT INTO meetings (id, meeting_number, meeting_date, notes, created_by) 
                    VALUES (@id, @num, @date, @notes, @creator)";
                cmd.Parameters.AddWithValue("@id", meetingId);
                cmd.Parameters.AddWithValue("@num", meetingNum);
                cmd.Parameters.AddWithValue("@date", meetingDate);
                cmd.Parameters.AddWithValue("@notes", notes ?? "");
                cmd.Parameters.AddWithValue("@creator", createdBy);
                cmd.ExecuteNonQuery();
            }

            transaction.Commit();
            return meetingId;
        }

        public static void ClearMeetingAttendance(string meetingId)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "DELETE FROM attendance WHERE meeting_id=@mid";
            cmd.Parameters.AddWithValue("@mid", meetingId);
            cmd.ExecuteNonQuery();
        }

        public static void UpdateMeetingNotes(string meetingId, string notes)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "UPDATE meetings SET notes=@notes WHERE id=@id";
            cmd.Parameters.AddWithValue("@id", meetingId);
            cmd.Parameters.AddWithValue("@notes", notes ?? "");
            cmd.ExecuteNonQuery();
        }

        public static void RecordAttendance(string meetingId, string memberId, string status)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"INSERT OR REPLACE INTO attendance (id, meeting_id, member_id, status) 
                VALUES (@id, @mid, @memid, @status)";
            cmd.Parameters.AddWithValue("@id", Helpers.GenerateId("att"));
            cmd.Parameters.AddWithValue("@mid", meetingId);
            cmd.Parameters.AddWithValue("@memid", memberId);
            cmd.Parameters.AddWithValue("@status", status);
            cmd.ExecuteNonQuery();
        }

        public static string RecordRemittance(double amount, string description, string remittedBy, string recordedBy, string remittanceDate)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            string remId = Helpers.GenerateId("rem");
            cmd.CommandText = @"INSERT INTO headquarters_remittances (id, amount, description, remitted_by, recorded_by, remittance_date) 
                VALUES (@id, @amt, @desc, @rem, @rec, @date)";
            cmd.Parameters.AddWithValue("@id", remId);
            cmd.Parameters.AddWithValue("@amt", amount);
            cmd.Parameters.AddWithValue("@desc", description ?? "");
            cmd.Parameters.AddWithValue("@rem", remittedBy);
            cmd.Parameters.AddWithValue("@rec", recordedBy);
            cmd.Parameters.AddWithValue("@date", remittanceDate);
            cmd.ExecuteNonQuery();
            return remId;
        }

        public static string RecordExpense(double amount, string description, string category, string approvedBy, string recordedBy, string expenseDate)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            string expId = Helpers.GenerateId("exp");
            cmd.CommandText = @"INSERT INTO expenses (id, description, amount, category, approved_by, recorded_by, expense_date) 
                VALUES (@id, @desc, @amt, @cat, @app, @rec, @date)";
            cmd.Parameters.AddWithValue("@id", expId);
            cmd.Parameters.AddWithValue("@desc", description);
            cmd.Parameters.AddWithValue("@amt", amount);
            cmd.Parameters.AddWithValue("@cat", category ?? "");
            cmd.Parameters.AddWithValue("@app", approvedBy ?? "");
            cmd.Parameters.AddWithValue("@rec", recordedBy);
            cmd.Parameters.AddWithValue("@date", expenseDate);
            cmd.ExecuteNonQuery();
            return expId;
        }

        public static void UpdateMemberPhoto(string memberId, string photoPath)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "UPDATE members SET photo_path=@photo, updated_at=datetime('now') WHERE id=@id";
            cmd.Parameters.AddWithValue("@id", memberId);
            cmd.Parameters.AddWithValue("@photo", photoPath);
            cmd.ExecuteNonQuery();
        }

        public static void UpdateMemberDetails(string memberId, string fullName, string phone, string address,
            string dateOfBirth, string gender, string occupation, string nextOfKin, string nextOfKinPhone, string notes,
            string email = "", string idType = "", string idNumber = "")
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"UPDATE members SET full_name=@fname, phone=@phone, address=@addr,
                date_of_birth=@dob, gender=@gender, occupation=@occ,
                next_of_kin=@nok, next_of_kin_phone=@nokp, notes=@notes,
                email=@email, id_type=@idtype, id_number=@idnum, updated_at=datetime('now') WHERE id=@id";
            cmd.Parameters.AddWithValue("@id", memberId);
            cmd.Parameters.AddWithValue("@fname", fullName);
            cmd.Parameters.AddWithValue("@phone", phone ?? "");
            cmd.Parameters.AddWithValue("@addr", address ?? "");
            cmd.Parameters.AddWithValue("@dob", dateOfBirth ?? "");
            cmd.Parameters.AddWithValue("@gender", gender ?? "");
            cmd.Parameters.AddWithValue("@occ", occupation ?? "");
            cmd.Parameters.AddWithValue("@nok", nextOfKin ?? "");
            cmd.Parameters.AddWithValue("@nokp", nextOfKinPhone ?? "");
            cmd.Parameters.AddWithValue("@notes", notes ?? "");
            cmd.Parameters.AddWithValue("@email", email ?? "");
            cmd.Parameters.AddWithValue("@idtype", idType ?? "");
            cmd.Parameters.AddWithValue("@idnum", idNumber ?? "");
            cmd.ExecuteNonQuery();
        }

        public static string UploadDocument(string memberId, string docType, string fileName, string filePath, long fileSize, string uploadedBy)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            string docId = Helpers.GenerateId("doc");
            cmd.CommandText = @"INSERT INTO member_documents (id, member_id, doc_type, file_name, file_path, file_size, uploaded_by) 
                VALUES (@id, @mid, @dtype, @fname, @fpath, @fsize, @uploader)";
            cmd.Parameters.AddWithValue("@id", docId);
            cmd.Parameters.AddWithValue("@mid", memberId);
            cmd.Parameters.AddWithValue("@dtype", docType);
            cmd.Parameters.AddWithValue("@fname", fileName);
            cmd.Parameters.AddWithValue("@fpath", filePath);
            cmd.Parameters.AddWithValue("@fsize", fileSize);
            cmd.Parameters.AddWithValue("@uploader", uploadedBy);
            cmd.ExecuteNonQuery();
            return docId;
        }

        public static string SaveDigitalForm(string memberId, string formType, string formData, string createdBy)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            string formId = Helpers.GenerateId("frm");
            cmd.CommandText = @"INSERT INTO digital_forms (id, member_id, form_type, form_data, status, created_by) 
                VALUES (@id, @mid, @ftype, @fdata, 'Active', @creator)";
            cmd.Parameters.AddWithValue("@id", formId);
            cmd.Parameters.AddWithValue("@mid", memberId);
            cmd.Parameters.AddWithValue("@ftype", formType);
            cmd.Parameters.AddWithValue("@fdata", formData);
            cmd.Parameters.AddWithValue("@creator", createdBy);
            cmd.ExecuteNonQuery();
            return formId;
        }

        public static List<Dictionary<string, object>> GetMemberDocuments(string memberId)
        {
            var docs = new List<Dictionary<string, object>>();
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT * FROM member_documents WHERE member_id=@mid ORDER BY uploaded_at DESC";
            cmd.Parameters.AddWithValue("@mid", memberId);
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                var doc = new Dictionary<string, object>();
                for (int i = 0; i < reader.FieldCount; i++)
                    doc[reader.GetName(i)] = reader.GetValue(i);
                docs.Add(doc);
            }
            return docs;
        }

        public static List<Dictionary<string, object>> GetMemberDigitalForms(string memberId)
        {
            var forms = new List<Dictionary<string, object>>();
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT * FROM digital_forms WHERE member_id=@mid ORDER BY created_at DESC";
            cmd.Parameters.AddWithValue("@mid", memberId);
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                var form = new Dictionary<string, object>();
                for (int i = 0; i < reader.FieldCount; i++)
                    form[reader.GetName(i)] = reader.GetValue(i);
                forms.Add(form);
            }
            return forms;
        }

        public static void DeleteDocument(string docId)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "DELETE FROM member_documents WHERE id=@id";
            cmd.Parameters.AddWithValue("@id", docId);
            cmd.ExecuteNonQuery();
        }

        public static void UpdateMemberStatus(string memberId, string status)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "UPDATE members SET status=@status, updated_at=datetime('now') WHERE id=@id";
            cmd.Parameters.AddWithValue("@id", memberId);
            cmd.Parameters.AddWithValue("@status", status);
            cmd.ExecuteNonQuery();
        }

        public static double GetMemberOutstanding(string memberId)
        {
            using var conn = Connection.GetConnection();
            double payable, repaid;
            using (var cmd = conn.CreateCommand())
            {
                cmd.CommandText = "SELECT COALESCE(SUM(total_payable), 0) FROM loans WHERE member_id=@mid AND status IN ('Approved','Disbursed')";
                cmd.Parameters.AddWithValue("@mid", memberId);
                payable = Convert.ToDouble(cmd.ExecuteScalar());
            }
            using (var cmd = conn.CreateCommand())
            {
                cmd.CommandText = @"SELECT COALESCE(SUM(lr.amount), 0) FROM loan_repayments lr
                    INNER JOIN loans l ON lr.loan_id=l.id
                    WHERE l.member_id=@mid AND l.status IN ('Approved','Disbursed')";
                cmd.Parameters.AddWithValue("@mid", memberId);
                repaid = Convert.ToDouble(cmd.ExecuteScalar());
            }
            double outstanding = payable - repaid;
            return outstanding > 0 ? outstanding : 0;
        }

        public static double GetMemberOutstandingTotal()
        {
            using var conn = Connection.GetConnection();
            double payable, repaid;
            using (var cmd = conn.CreateCommand())
            {
                cmd.CommandText = "SELECT COALESCE(SUM(total_payable), 0) FROM loans WHERE status IN ('Approved','Disbursed')";
                payable = Convert.ToDouble(cmd.ExecuteScalar());
            }
            using (var cmd = conn.CreateCommand())
            {
                cmd.CommandText = @"SELECT COALESCE(SUM(lr.amount), 0) FROM loan_repayments lr
                    INNER JOIN loans l ON lr.loan_id=l.id WHERE l.status IN ('Approved','Disbursed')";
                repaid = Convert.ToDouble(cmd.ExecuteScalar());
            }
            double outstanding = payable - repaid;
            return outstanding > 0 ? outstanding : 0;
        }

        public static void LogAudit(string userId, string action, string details)
        {
            try
            {
                using var conn = Connection.GetConnection();
                using var cmd = conn.CreateCommand();
                cmd.CommandText = @"INSERT INTO audit_logs (id, user_id, action, new_value, created_at)
                    VALUES (@id, @uid, @action, @details, datetime('now'))";
                cmd.Parameters.AddWithValue("@id", Helpers.GenerateId("aud"));
                cmd.Parameters.AddWithValue("@uid", userId ?? "");
                cmd.Parameters.AddWithValue("@action", action);
                cmd.Parameters.AddWithValue("@details", details ?? "");
                cmd.ExecuteNonQuery();
            }
            catch { }
        }

        public static void UpdateLastLogin(string userId)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "UPDATE users SET last_login=datetime('now') WHERE id=@id";
            cmd.Parameters.AddWithValue("@id", userId);
            cmd.ExecuteNonQuery();
        }

        public static void AddGuarantor(string loanId, string memberId, double guaranteeAmount = 0)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"INSERT INTO loan_guarantors (id, loan_id, member_id, guarantee_amount) VALUES (@id, @lid, @mid, @amt)";
            cmd.Parameters.AddWithValue("@id", Helpers.GenerateId("grt"));
            cmd.Parameters.AddWithValue("@lid", loanId);
            cmd.Parameters.AddWithValue("@mid", memberId);
            cmd.Parameters.AddWithValue("@amt", guaranteeAmount);
            cmd.ExecuteNonQuery();
        }

        private static void CreateCharge(SqliteConnection conn, Microsoft.Data.Sqlite.SqliteTransaction transaction,
            string memberId, string meetingId, string chargeType, string description, double amount, string createdBy)
        {
            if (amount <= 0) return;
            using var check = conn.CreateCommand();
            check.Transaction = transaction;
            check.CommandText = @"SELECT COUNT(*) FROM member_charges
                WHERE member_id=@mid AND charge_type=@ctype
                AND ((meeting_id IS NULL AND @mtg IS NULL) OR meeting_id=@mtg)";
            check.Parameters.AddWithValue("@mid", memberId);
            check.Parameters.AddWithValue("@ctype", chargeType);
            check.Parameters.AddWithValue("@mtg", string.IsNullOrEmpty(meetingId) ? DBNull.Value : (object)meetingId);
            if (Convert.ToInt32(check.ExecuteScalar()) > 0) return;

            using var cmd = conn.CreateCommand();
            cmd.Transaction = transaction;
            cmd.CommandText = @"INSERT INTO member_charges (id, charge_id, member_id, meeting_id, charge_type, description, amount, created_by)
                VALUES (@id, @cid, @mid, @mtg, @ctype, @desc, @amt, @creator)";
            cmd.Parameters.AddWithValue("@id", Helpers.GenerateId("chg"));
            cmd.Parameters.AddWithValue("@cid", "CHG-" + DateTime.Now.ToString("yyyyMMddHHmmss") + "-" + new Random().Next(1000, 9999));
            cmd.Parameters.AddWithValue("@mid", memberId);
            cmd.Parameters.AddWithValue("@mtg", string.IsNullOrEmpty(meetingId) ? DBNull.Value : (object)meetingId);
            cmd.Parameters.AddWithValue("@ctype", chargeType);
            cmd.Parameters.AddWithValue("@desc", description ?? "");
            cmd.Parameters.AddWithValue("@amt", amount);
            cmd.Parameters.AddWithValue("@creator", createdBy ?? "");
            cmd.ExecuteNonQuery();
        }

        public static int ApplyAbsenceFines(string meetingId, double fineAmount, string createdBy)
        {
            if (fineAmount <= 0) return 0;
            int count = 0;
            using var conn = Connection.GetConnection();
            using var transaction = conn.BeginTransaction();
            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = "SELECT member_id FROM attendance WHERE meeting_id=@mtg AND status='Absent'";
                cmd.Parameters.AddWithValue("@mtg", meetingId);
                using var reader = cmd.ExecuteReader();
                var absent = new List<string>();
                while (reader.Read()) absent.Add(reader.GetString(0));
                reader.Close();
                foreach (var mid in absent)
                {
                    CreateCharge(conn, transaction, mid, meetingId, "Absence Fine", "Absence fine", fineAmount, createdBy);
                    count++;
                }
            }
            transaction.Commit();
            return count;
        }

        public static int ApplyMinutesLevy(string meetingId, double amount, string createdBy)
        {
            if (amount <= 0) return 0;
            int count = 0;
            using var conn = Connection.GetConnection();
            using var transaction = conn.BeginTransaction();
            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = "SELECT member_id FROM attendance WHERE meeting_id=@mtg AND status='Absent'";
                cmd.Parameters.AddWithValue("@mtg", meetingId);
                using var reader = cmd.ExecuteReader();
                var absent = new List<string>();
                while (reader.Read()) absent.Add(reader.GetString(0));
                reader.Close();
                foreach (var mid in absent)
                {
                    CreateCharge(conn, transaction, mid, meetingId, "Minutes Levy", "Minutes levy", amount, createdBy);
                    count++;
                }
            }
            transaction.Commit();
            return count;
        }

        public static string RecordChargePayment(string memberId, double amount, string chargeType, string recordedBy, string paymentDate)
        {
            using var conn = Connection.GetConnection();
            using var transaction = conn.BeginTransaction();

            double remaining = amount;
            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"SELECT id, amount, amount_paid FROM member_charges
                    WHERE member_id=@mid AND charge_type=@ctype AND status != 'Paid'
                    ORDER BY created_at ASC";
                cmd.Parameters.AddWithValue("@mid", memberId);
                cmd.Parameters.AddWithValue("@ctype", chargeType);
                using var reader = cmd.ExecuteReader();
                var charges = new List<(string id, double owed)>();
                while (reader.Read())
                {
                    double owed = Convert.ToDouble(reader["amount"]) - Convert.ToDouble(reader["amount_paid"]);
                    if (owed > 0) charges.Add((reader["id"].ToString()!, owed));
                }
                reader.Close();

                foreach (var (id, owed) in charges)
                {
                    if (remaining <= 0) break;
                    double pay = Math.Min(remaining, owed);
                    using var upd = conn.CreateCommand();
                    upd.Transaction = transaction;
                    upd.CommandText = @"UPDATE member_charges SET amount_paid = amount_paid + @pay,
                        status = CASE WHEN amount_paid + @pay >= amount THEN 'Paid' ELSE 'Partial' END
                        WHERE id=@id";
                    upd.Parameters.AddWithValue("@pay", pay);
                    upd.Parameters.AddWithValue("@id", id);
                    upd.ExecuteNonQuery();
                    remaining -= pay;
                }
            }

            double applied = amount - remaining;
            string txId = Helpers.GenerateId("txn");
            using (var cmd = conn.CreateCommand())
            {
                cmd.Transaction = transaction;
                cmd.CommandText = @"INSERT INTO transactions (id, member_id, type, amount, description, recorded_by, transaction_date)
                    VALUES (@id, @mid, 'Charge Payment', @amt, @desc, @rec, @date)";
                cmd.Parameters.AddWithValue("@id", txId);
                cmd.Parameters.AddWithValue("@mid", memberId);
                cmd.Parameters.AddWithValue("@amt", applied);
                cmd.Parameters.AddWithValue("@desc", $"{chargeType} payment");
                cmd.Parameters.AddWithValue("@rec", recordedBy);
                cmd.Parameters.AddWithValue("@date", paymentDate);
                cmd.ExecuteNonQuery();
            }

            transaction.Commit();
            return txId;
        }

        public static string RecordOtherPayment(string memberId, double amount, string tag, string recordedBy, string paymentDate)
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            string txId = Helpers.GenerateId("txn");
            cmd.CommandText = @"INSERT INTO transactions (id, member_id, type, amount, description, recorded_by, transaction_date)
                VALUES (@id, @mid, 'Other', @amt, @desc, @rec, @date)";
            cmd.Parameters.AddWithValue("@id", txId);
            cmd.Parameters.AddWithValue("@mid", memberId);
            cmd.Parameters.AddWithValue("@amt", amount);
            cmd.Parameters.AddWithValue("@desc", string.IsNullOrWhiteSpace(tag) ? "Other payment" : tag);
            cmd.Parameters.AddWithValue("@rec", recordedBy);
            cmd.Parameters.AddWithValue("@date", paymentDate);
            cmd.ExecuteNonQuery();
            return txId;
        }

        public static Dictionary<string, double> GetMemberChargesOwed(string memberId)
        {
            var result = new Dictionary<string, double>
            {
                { "MinutesOwed", 0 }, { "FinesOwed", 0 }, { "OtherOwed", 0 }, { "ChargesPaid", 0 }, { "TotalOwed", 0 }
            };
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = @"SELECT charge_type, COALESCE(SUM(amount - amount_paid), 0) AS owed,
                COALESCE(SUM(amount_paid), 0) AS paid FROM member_charges
                WHERE member_id=@mid AND status != 'Paid' GROUP BY charge_type";
            cmd.Parameters.AddWithValue("@mid", memberId);
            using var reader = cmd.ExecuteReader();
            while (reader.Read())
            {
                string type = reader["charge_type"]?.ToString() ?? "";
                double owed = Convert.ToDouble(reader["owed"]);
                double paid = Convert.ToDouble(reader["paid"]);
                result["ChargesPaid"] += paid;
                result["TotalOwed"] += owed;
                if (type == "Minutes Levy") result["MinutesOwed"] += owed;
                else if (type == "Absence Fine") result["FinesOwed"] += owed;
                else result["OtherOwed"] += owed;
            }
            return result;
        }

        public static double GetTotalChargesOwed()
        {
            using var conn = Connection.GetConnection();
            using var cmd = conn.CreateCommand();
            cmd.CommandText = "SELECT COALESCE(SUM(amount - amount_paid), 0) FROM member_charges WHERE status != 'Paid'";
            return Convert.ToDouble(cmd.ExecuteScalar());
        }
    }
}
