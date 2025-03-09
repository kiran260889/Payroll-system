import bcrypt
from db import get_db_connection
from email_service import send_email

class HR:
    def onboard_employee(self):
        """Interactive HR onboarding process for a new employee."""
        print("\n🚀 Onboard New Employee")

        # Step-by-step interactive input
        name = input("Enter Employee Name: ")
        designation = input("Enter Designation (Employee / HR / Project Manager): ")
        email = input("Enter Employee Email: ")
        password = input("Enter Temporary Password for Employee: ")  # ✅ Ask for password
        salary = float(input("Enter Annual Salary: "))
        ethnicity = input("Enter Ethnicity: ")

        # Fetch all managers (HR & Project Managers)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, name, designation FROM users WHERE designation IN ('HR', 'Project Manager')")
        managers = cur.fetchall()

        print("\n📋 Available Managers (HR & Project Managers):")
        if managers:
            for manager in managers:
                print(f"   - ID: {manager[0]}, Name: {manager[1]}, Role: {manager[2]}")
        else:
            print("   ❌ No managers found! Defaulting to first HR in the system.")

        # Default to the first HR if no managers exist
        cur.execute("SELECT user_id FROM users WHERE designation = 'HR' LIMIT 1")
        default_hr = cur.fetchone()
        default_pm_id = default_hr[0] if default_hr else None  

        pm_id = input("Enter Reporting Manager ID from the list above (or leave blank for default HR): ")

        if pm_id.strip() == "":
            pm_id = default_pm_id
        else:
            pm_id = int(pm_id)

        # Hash the password before storing it in the database
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # Insert employee into the database with password
        cur.execute("""
            INSERT INTO users (name, email, password_hash, designation, ethnicity, annual_salary, reporting_project_manager) 
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING user_id
        """, (name, email, hashed_password, designation, ethnicity, salary, pm_id))

        emp_id = cur.fetchone()[0]  # Get the auto-generated employee ID
        conn.commit()
        cur.close()
        conn.close()

        print(f"✅ Employee {name} added successfully with Employee ID: {emp_id}.")

        # Send Welcome Email
        subject = "Welcome to the Organization"
        body = f"""
        Dear {name},

        You have been successfully onboarded to the company.
        Your position: {designation}
        Your Employee ID: {emp_id}
        Your annual salary: ${salary}
        Reporting Manager ID: {pm_id if pm_id else 'HR'}
        
        Please log in using your temporary password: {password}
        (You will be asked to change it after first login.)

        Best Regards,
        HR Team
        """
        send_email(email, subject, body)

        return f"✅ Welcome email sent to {name} at {email}."
