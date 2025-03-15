import psycopg2
from db import get_db_connection

def get_employees_reporting_to_pm(pm_id):
    """Fetch all employees reporting to the given Project Manager."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT user_id, name FROM users WHERE reporting_project_manager = %s
    """, (pm_id,))

    employees = cur.fetchall()
    cur.close()
    conn.close()

    return employees

def assign_shift(pm_id):
    """Allow a Project Manager to assign a shift to an employee."""
    employees = get_employees_reporting_to_pm(pm_id)

    if not employees:
        return "❌ No employees found reporting to you."

    print("\n📋 Employees Reporting to You:")
    for emp in employees:
        print(f"   - Employee ID: {emp[0]}, Name: {emp[1]}")

    emp_id = input("Enter Employee ID to assign a shift: ").strip()

    # Validate Employee ID
    if not any(str(emp[0]) == emp_id for emp in employees):
        return "❌ Invalid Employee ID. Please select from the list."

    shift_code = input("Enter Shift Code (M, G, S, N): ").strip().upper()

    # Validate Shift Code
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT shift_code FROM shifts WHERE shift_code = %s", (shift_code,))
    valid_shift = cur.fetchone()
    
    if not valid_shift:
        cur.close()
        conn.close()
        return "❌ Invalid Shift Code. Please enter a valid shift (M, G, S, N)."

    # Assign shift with week start and end date
    cur.execute("""
        INSERT INTO employee_shifts (user_id, shift_code, week_start_date, week_end_date)
        VALUES (%s, %s, CURRENT_DATE, CURRENT_DATE + INTERVAL '6 days')
        ON CONFLICT (user_id, week_start_date) 
        DO UPDATE SET shift_code = EXCLUDED.shift_code, week_end_date = EXCLUDED.week_end_date;
    """, (emp_id, shift_code))

    conn.commit()
    cur.close()
    conn.close()

    return f"✅ Shift {shift_code} assigned to Employee ID {emp_id}."
