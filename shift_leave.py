from db import get_db_connection
import datetime
from email_service import send_email

class ShiftManagement:
    def view_shift_schedule(self, emp_id):
        """Retrieve the shift schedule for an employee."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT week_start_date, week_end_date, shift_code FROM employee_shifts 
            WHERE user_id = %s ORDER BY week_start_date DESC LIMIT 1
        """, (emp_id,))
        
        shift = cur.fetchone()
        cur.close()
        conn.close()

        if shift:
            return f"Shift Schedule: {shift[0]} to {shift[1]}, Shift Code: {shift[2]}"
        else:
            return "No shift assigned for the current week."

class LeaveManagement:
    def apply_leave(self, emp_id, start_date, end_date, reason):
        """Employee applies for leave."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO leave_requests (user_id, start_date, end_date, reason, status) 
            VALUES (%s, %s, %s, %s, 'Pending')
        """, (emp_id, start_date, end_date, reason))
        
        conn.commit()
        cur.close()
        conn.close()

        return f"Leave request submitted for {start_date} to {end_date}."

    
    def view_pending_leaves(self, approver_id):
        """Fetch all pending leave requests for HR/PM to approve."""
        conn = get_db_connection()
        cur = conn.cursor()

        # Ensure correct column names are used (Primary key is `leave_id`)
        cur.execute("""
            SELECT lr.leave_id, u.user_id, u.name, lr.start_date, lr.end_date, lr.reason, lr.status
            FROM leave_requests lr
            JOIN users u ON lr.user_id = u.user_id
            WHERE lr.status = 'Pending'
            AND u.reporting_project_manager = %s
            ORDER BY lr.start_date ASC;
        """, (approver_id,))

        leave_requests = cur.fetchall()
        cur.close()
        conn.close()

        if not leave_requests:
            return [], " No pending leave requests."

        #  Format output for display
        leave_list = "\n **Pending Leave Requests:**\n"
        for leave in leave_requests:
            leave_id, user_id, name, start_date, end_date, reason, status = leave
            leave_list += f"""
            ------------------------------------
            **Leave ID**: {leave_id}
            **Employee**: {name} (ID: {user_id})
            **Leave Dates**: {start_date} to {end_date}
            **Reason**: {reason}
            **Status**: {status}
            ------------------------------------
            """

        return leave_list, leave_requests

    def process_leave_request(self, approver_id):
        """HR/PM can approve/reject leave requests without entering Employee ID manually."""
        leave_list, leave_requests = self.view_pending_leaves(approver_id)

        if not leave_requests:
            return leave_list  # No pending requests

        print(leave_list)

        #  Select leave request to process
        leave_id = input("Enter the Leave ID to Approve/Reject: ").strip()
        if not leave_id.isdigit():
            return "Invalid Leave ID."

        leave_id = int(leave_id)
        decision = input("Approve (A) / Reject (R): ").strip().upper()

        if decision not in ["A", "R"]:
            return "Invalid input. Enter 'A' to approve or 'R' to reject."

        status = "Approved" if decision == "A" else "Rejected"

        # Update leave request in database
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("UPDATE leave_requests SET status = %s WHERE leave_id = %s", (status, leave_id))

        #  Fetch Employee Email to Send Notification
        cur.execute("""
            SELECT u.email, u.name, lr.start_date, lr.end_date
            FROM users u 
            JOIN leave_requests lr ON u.user_id = lr.user_id 
            WHERE lr.leave_id = %s
        """, (leave_id,))
        employee_data = cur.fetchone()

        if not employee_data:
            return "Employee not found for this leave request."

        employee_email, employee_name, start_date, end_date = employee_data

        conn.commit()
        cur.close()
        conn.close()

        #  Send Email Notification to Employee
        subject = f"🏝 Leave Request {status}"
        body = f"""
        Hello {employee_name},

        Your leave request (ID: {leave_id}) for **{start_date} to {end_date}** has been **{status}**.

        Regards,  
        Payroll System
        """
        send_email(employee_email, subject, body)

        return f"Leave request {status} successfully. Email sent to {employee_email}."
class PayrollHistory:
    def get_last_three_weeks_pay(self, emp_id):
        """Retrieve payroll history for the last three weeks for HR, PM, and Employees."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT week_start_date, week_end_date, total_hours, total_earnings, tax_deductions, final_salary 
            FROM payroll
            WHERE user_id = %s 
            AND week_start_date >= %s
            ORDER BY week_start_date DESC LIMIT 3
        """, (emp_id, datetime.date.today() - datetime.timedelta(weeks=3)))

        pay_history = cur.fetchall()
        cur.close()
        conn.close()

        if not pay_history:
            return "No payroll history available for the last 3 weeks."

        #  Format Payroll Data
        history = f" **Payroll History for User ID: {emp_id}**\n"
        for record in pay_history:
            week_start, week_end, total_hours, total_earnings, tax_deductions, final_salary = record
            history += f"""
            ------------------------------------
             **Week:** {week_start} - {week_end}
             **Total Hours Worked:** {total_hours:.2f} hrs
             **Total Earnings:** ${total_earnings:.2f}
             **Tax Deductions (15%)**: ${tax_deductions:.2f}
             **Final Salary (After Tax):** ${final_salary:.2f}
            ------------------------------------
            """
        return history
