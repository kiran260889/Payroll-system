import datetime
from db import get_db_connection
from email_service import send_email

class PayrollSystem:
    def process_weekly_payroll(self, hr_id):
        """HR manually processes payroll at the end of the week."""
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())  
        week_end = today  

        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT user_id, hourly_rate, ethnicity, email FROM users WHERE designation = 'Employee'")
        employees = cur.fetchall()

        for employee in employees:
            user_id, hourly_rate, ethnicity, email = employee
            total_hours = 40  
            base_salary = total_hours * hourly_rate
            overtime_hours = max(total_hours - 40, 0)
            overtime_pay = overtime_hours * (hourly_rate * 1.5)
            holiday_pay = 0  

            # Māori 5% additional pay
            maori_bonus = base_salary * 0.05 if ethnicity == "Māori" else 0

            # Night shift allowance
            cur.execute("SELECT COUNT(*) FROM employee_shifts WHERE user_id = %s AND shift_code = 'N'", (user_id,))
            night_shift_days = cur.fetchone()[0]
            night_shift_allowance = night_shift_days * 0.25

            total_earnings = base_salary + overtime_pay + holiday_pay + maori_bonus + night_shift_allowance
            tax_deductions = total_earnings * 0.15  
            final_salary = total_earnings - tax_deductions

            cur.execute("""
                INSERT INTO payroll (user_id, total_hours, hourly_rate, overtime_hours, overtime_pay, holiday_pay, maori_bonus, night_shift_days, night_shift_allowance, total_earnings, tax_deductions, final_salary, week_start_date, week_end_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (user_id, total_hours, hourly_rate, overtime_hours, overtime_pay, holiday_pay, maori_bonus, night_shift_days, night_shift_allowance, total_earnings, tax_deductions, final_salary, week_start, week_end))

        conn.commit()
        cur.close()
        conn.close()
        return "Payroll processed successfully. HR must now generate payslips."
