from db import get_db_connection

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

class PayrollHistory:
    def get_last_three_weeks_pay(self, emp_id):
        """Retrieve payroll history for the last three weeks."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT week_start_date, final_salary FROM payroll
            WHERE user_id = %s ORDER BY week_start_date DESC LIMIT 3
        """, (emp_id,))
        
        pay_history = cur.fetchall()
        cur.close()
        conn.close()

        if pay_history:
            history = "\n Last 3 Weeks' Pay:\n"
            for record in pay_history:
                history += f"• Week starting {record[0]}: ${record[1]:.2f}\n"
            return history
        else:
            return "No payroll history available."
