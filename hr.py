import bcrypt
import datetime
from db import get_db_connection
from email_service import send_email

class HR:
    def onboard_employee(self):
        """Onboard a new employee with IRD number and bank details"""
        conn = get_db_connection()
        cur = conn.cursor()

        print("\n🔹 Employee Onboarding")
        
        name = input("Enter Employee Name: ").strip()
        email = input("Enter Employee Email: ").strip()
        designation = input("Enter Employee Designation (Employee/Project Manager/HR): ").strip()
        salary = float(input("Enter Employee Annual Salary: ").strip())

        # ✅ Collect IRD Number and Bank Details
        ird_number = input("Enter Employee IRD Number: ").strip()
        bank_name = input("Enter Employee Bank Name: ").strip()
        bank_account = input("Enter Employee Bank Account Number: ").strip()

        # ✅ Ask for Nationality, Region, and Ethnicity
        nationality = input("Enter Employee Nationality (e.g., New Zealand, Australia, USA): ").strip()
        region = input("Enter Employee Region (e.g., Auckland, Wellington, Sydney): ").strip()
        ethnicity = input("Enter Employee Ethnicity (e.g., Māori, Pākehā, Pacific Islander, Asian): ").strip()

        # ✅ Generate and Hash Default Password
        password = "CarRental123"
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # ✅ Assign Reporting Manager
        cur.execute("SELECT user_id, name FROM users WHERE designation IN ('Project Manager', 'HR')")
        managers = cur.fetchall()

        print("\n🔹 Available Reporting Managers:")
        for manager in managers:
            print(f"ID: {manager[0]}, Name: {manager[1]}")

        reporting_manager_id = input("Enter Reporting Manager ID from the list above (or leave blank for default HR): ").strip()
        reporting_manager_id = int(reporting_manager_id) if reporting_manager_id.isdigit() else None

        # ✅ Get Reporting Manager Name
        reporting_manager_name = "HR Department"  # Default if no manager is assigned
        if reporting_manager_id:
            cur.execute("SELECT name FROM users WHERE user_id = %s", (reporting_manager_id,))
            manager_record = cur.fetchone()
            if manager_record:
                reporting_manager_name = manager_record[0]

        # ✅ Insert Employee Data and Retrieve New User ID
        cur.execute("""
            INSERT INTO users (name, email, password_hash, designation, nationality, region, ethnicity, annual_salary, 
                              reporting_project_manager, ird_number, bank_name, bank_account)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING user_id;
        """, (name, email, hashed_password, designation, nationality, region, ethnicity, salary, 
              reporting_manager_id, ird_number, bank_name, bank_account))

        new_user_id = cur.fetchone()[0]  # ✅ Get the inserted user ID

        conn.commit()  # ✅ Ensure the user is committed before inserting the shift

        # ✅ Assign Default Shift "G" (General Shift: 9 AM - 5 PM)
        week_start = datetime.date.today()
        week_end = week_start + datetime.timedelta(days=6)  # Assign for the entire week
        cur.execute("""
            INSERT INTO employee_shifts (user_id, shift_code, week_start_date, week_end_date, assigned_by)
            VALUES (%s, 'G', %s, %s, %s)
        """, (new_user_id, week_start, week_end, reporting_manager_id or "HR"))

        conn.commit()

        # ✅ Send onboarding email with IRD & Bank Details
        subject = "🎉 Welcome to the Company!"
        body = f"""
        Kia ora {name},

        You have been successfully onboarded. Your initial login details are:
        - Email: {email}
        - Default Password: {password}
        - Designation: {designation}
        - Nationality: {nationality}
        - Region: {region}
        - Ethnicity: {ethnicity}
        - IRD Number: {ird_number}
        - Bank Name: {bank_name}
        - Bank Account: {bank_account}
        - Reporting Manager: {reporting_manager_name}

        Please log in and update your password.

        Best Regards,
        HR Team
        """
        send_email(email, subject, body)

        cur.close()
        conn.close()
        return f"✅ {name} has been onboarded successfully!"
    def offboard_employee(self):
        """HR removes an employee from the system."""
        print("\n🔹 Offboard Employee")
        emp_id = input("Enter Employee ID to remove: ").strip()

        conn = get_db_connection()
        cur = conn.cursor()

        # Check if employee exists
        cur.execute("SELECT name, email FROM users WHERE user_id = %s", (emp_id,))
        employee = cur.fetchone()

        if not employee:
            print("❌ Error: Employee ID not found.")
            return "❌ Error: Employee not found."

        name, email = employee

        # Delete employee
        cur.execute("DELETE FROM users WHERE user_id = %s", (emp_id,))
        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ Employee {name} (ID: {emp_id}) offboarded successfully.")

        # ✅ Send Offboarding Email
        subject = "🚀 Offboarding Notice"
        body = f"""
        Dear {name},

        Your offboarding process has been completed.
        If you need any further information, please contact HR.

        Regards,  
        HR Team  
        Car Rental Payroll System
        """
        send_email(email, subject, body)

        return f"✅ Offboarding email sent to {name} at {email}."
