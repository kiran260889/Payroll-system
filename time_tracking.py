import psycopg2
import datetime
import signal
import sys
import select
from db import get_db_connection
from email_service import send_email

predefined_reasons = [
    "Personal Emergency",
    "Medical Issue",
    "Technical Issues",
    "Unexpected Work Commitment",
    "Other"
]

def get_employee_shift(user_id):
    """Fetch the employee's assigned shift timings from the database."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT es.shift_code, s.shift_start, s.shift_end
        FROM employee_shifts es
        JOIN shifts s ON es.shift_code = s.shift_code
        WHERE es.user_id = %s AND es.week_start_date <= CURRENT_DATE
        ORDER BY es.week_start_date DESC LIMIT 1
    """, (user_id,))

    shift = cur.fetchone()
    cur.close()
    conn.close()

    if shift:
        return shift[0], shift[1], shift[2]  # shift_code, shift_start, shift_end
    return None, None, None

def start_time_tracking(user_id):
    """Start tracking time, but only if within shift hours."""
    conn = get_db_connection()
    cur = conn.cursor()

    current_time = datetime.datetime.now().time()
    shift_code, shift_start, shift_end = get_employee_shift(user_id)

    if not shift_code or not shift_start or not shift_end:
        return "No shift assigned. Time tracking is not allowed."

    # Prevent logging in after shift hours
    if current_time > shift_end:
        return f"You cannot start time tracking after your shift ends at {shift_end.strftime('%I:%M %p')}."

    # Check if already logged in today
    current_date = datetime.date.today()
    cur.execute("""
        SELECT login_time FROM time_tracking
        WHERE user_id = %s AND DATE(login_time) = %s AND logout_time IS NULL
    """, (user_id, current_date))

    existing_session = cur.fetchone()

    if existing_session:
        return f"Time tracking already started for today ({current_date})."

    # Ask for reason if late
    late_reason = None
    if current_time > shift_start:
        print("You are logging in late! Please select a reason:")
        for idx, reason in enumerate(predefined_reasons, 1):
            print(f"{idx}. {reason}")

        choice = input("Enter your choice (1-5): ").strip()
        late_reason = predefined_reasons[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= len(predefined_reasons) else "Other"

    # Insert login record
    login_time = datetime.datetime.now()
    cur.execute("""
        INSERT INTO time_tracking (user_id, login_time, late_reason) 
        VALUES (%s, %s, %s)
    """, (user_id, login_time, late_reason))

    conn.commit()
    cur.close()
    conn.close()

    return f"Time tracking started at {login_time.strftime('%Y-%m-%d %H:%M:%S')}. Late reason recorded: {late_reason if late_reason else 'N/A'}."
def end_time_tracking(user_id):
    """Stop time tracking, ask for early logout reason if needed, and calculate total work hours."""
    conn = get_db_connection()
    cur = conn.cursor()

    current_date = datetime.date.today()

    # Fetch the latest login for today
    cur.execute("""
        SELECT track_id, login_time FROM time_tracking
        WHERE user_id = %s AND DATE(login_time) = %s AND logout_time IS NULL
        ORDER BY login_time DESC LIMIT 1
    """, (user_id, current_date))

    last_login = cur.fetchone()

    if not last_login:
        return "No active session found for today. Please start time tracking first."

    track_id, login_time = last_login
    logout_time = datetime.datetime.now()
    
    # Fetch shift details
    cur.execute("""
        SELECT es.shift_code, s.shift_start, s.shift_end, u.reporting_project_manager
        FROM employee_shifts es
        JOIN shifts s ON es.shift_code = s.shift_code
        JOIN users u ON es.user_id = u.user_id
        WHERE es.user_id = %s AND es.week_start_date <= CURRENT_DATE
        ORDER BY es.week_start_date DESC LIMIT 1
    """, (user_id,))

    shift_data = cur.fetchone()
    
    if not shift_data:
        return "No shift assigned. Logout not recorded."

    shift_code, shift_start, shift_end, reporting_pm = shift_data
    early_logout_reason = None

    # If logging out before shift end, ask for a reason
    if logout_time.time() < shift_end:
        print("\n You are logging out early! Please select a reason:")
        for idx, reason in enumerate(predefined_reasons, 1):
            print(f"{idx}. {reason}")

        choice = input("Enter your choice (1-5): ").strip()
        early_logout_reason = predefined_reasons[int(choice) - 1] if choice.isdigit() and 1 <= int(choice) <= len(predefined_reasons) else "Other"

    # Store logout and reason in the database
    cur.execute("""
        UPDATE time_tracking 
        SET logout_time = %s, early_logout_reason = %s 
        WHERE track_id = %s
    """, (logout_time, early_logout_reason, track_id))

    conn.commit()

    # Fetch PM Email
    cur.execute("SELECT email FROM users WHERE user_id = %s", (reporting_pm,))
    pm_email = cur.fetchone()

    cur.close()
    conn.close()

    # Send Email to Reporting Manager
    if early_logout_reason and pm_email:
        subject = "Employee Early Logout Alert"
        body = f"""
        Hello,

        Employee ID: {user_id} has logged out early from their shift ({shift_code}).
        Logout Reason: {early_logout_reason}
        Logout Time: {logout_time.strftime('%Y-%m-%d %H:%M:%S')}

        Please review the reason and take necessary actions.

        Best Regards,
        Payroll System
        """
        send_email(pm_email[0], subject, body)

    return f"Logout recorded. Early logout reason: {early_logout_reason if early_logout_reason else 'N/A'}."

def handle_forced_logout(user_id):
    """Handle forced logout when user presses Ctrl + C and ask for logout reason."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Fetch shift details
    cur.execute("""
        SELECT es.shift_code, s.shift_start, s.shift_end, u.reporting_project_manager
        FROM employee_shifts es
        JOIN shifts s ON es.shift_code = s.shift_code
        JOIN users u ON es.user_id = u.user_id
        WHERE es.user_id = %s AND es.week_start_date <= CURRENT_DATE
        ORDER BY es.week_start_date DESC LIMIT 1
    """, (user_id,))

    shift_data = cur.fetchone()

    if not shift_data:
        print("\n You have successfully logged out.")
        sys.exit(0)

    shift_code, shift_start, shift_end, reporting_pm = shift_data
    logout_time = datetime.datetime.now()
    early_logout_reason = "Other"

    print("\n You are logging out early! Please select a reason:")
    for idx, reason in enumerate(predefined_reasons, 1):
        print(f"{idx}. {reason}")

    try:
        # Use `sys.stdin.read(1)` to avoid "re-enter readline" error
        sys.stdout.flush()  # Ensure prompt is visible
        if sys.stdin in select.select([sys.stdin], [], [], 10)[0]:  # Wait up to 10 seconds for input
            choice = sys.stdin.read(1).strip()
            if choice.isdigit() and 1 <= int(choice) <= len(predefined_reasons):
                early_logout_reason = predefined_reasons[int(choice) - 1]
    except Exception as e:
        print(f"\n Input Error: {e}. Defaulting to 'Other'.")

    # Store logout reason
    cur.execute("""
        UPDATE time_tracking 
        SET logout_time = %s, early_logout_reason = %s 
        WHERE user_id = %s AND logout_time IS NULL
    """, (logout_time, early_logout_reason, user_id))

    conn.commit()

    # Fetch PM Email
    cur.execute("SELECT email FROM users WHERE user_id = %s", (reporting_pm,))
    pm_email = cur.fetchone()

    cur.close()
    conn.close()

    # Send Email to Reporting Manager
    if pm_email:
        subject = "Employee Early Logout Alert"
        body = f"""
        Hello,

        Employee ID: {user_id} has logged out early from their shift ({shift_code}).
        Logout Reason: {early_logout_reason}
        Logout Time: {logout_time.strftime('%Y-%m-%d %H:%M:%S')}

        Please review the reason and take necessary actions.

        Best Regards,
        Payroll System
        """
        send_email(pm_email[0], subject, body)

    print(f"Early logout recorded with reason: {early_logout_reason}.")
    print(f"Notification sent to Reporting Manager.")

    sys.exit(0)       
# Register signal handler for Ctrl + C
def setup_signal_handler(user_id):
    """Setup signal handler to capture Ctrl + C logout event."""
    def signal_handler(sig, frame):
        handle_forced_logout(user_id)

    signal.signal(signal.SIGINT, signal_handler)
