import datetime
from db import get_db_connection
from email_service import send_email

def start_time_tracking(user_id):
    """Record login time when an employee logs in."""
    conn = get_db_connection()
    cur = conn.cursor()
    login_time = datetime.datetime.now()

    cur.execute(
        "INSERT INTO time_tracking (user_id, login_time) VALUES (%s, %s) RETURNING record_id",
        (user_id, login_time)
    )
    record_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return record_id

def end_time_tracking(user_id):
    """Prompt for logout reason, track early logout minutes, and notify PM."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT reason_id, reason FROM logout_reasons")
    reasons = cur.fetchall()

    print("\n Select a reason for logging out early:")
    for reason in reasons:
        print(f"{reason[0]}. {reason[1]}")
    
    reason_id = int(input("\nEnter the reason number: "))
    logout_time = datetime.datetime.now()

    cur.execute(
        "UPDATE time_tracking SET logout_time = %s, logout_reason_id = %s WHERE user_id = %s AND logout_time IS NULL",
        (logout_time, reason_id, user_id)
    )

    conn.commit()
    cur.close()
    conn.close()

    return "Logout recorded successfully."
