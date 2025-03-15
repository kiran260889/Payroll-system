import argparse
import signal
import sys
import getpass
import bcrypt
from db import get_user_designation, authenticate_user, get_db_connection
from shift_management import assign_shift
from hr import HR
from payroll import PayrollSystem
from shift_leave import ShiftManagement, LeaveManagement, PayrollHistory
from holiday_calendar import HolidayCalendar
from time_tracking import start_time_tracking, end_time_tracking, setup_signal_handler, handle_forced_logout

current_user_id = None  

def signal_handler(sig, frame):
    """Handle Ctrl+C (forced logout) and log out the user properly."""
    if current_user_id:
        print("\n Forced logout detected! Logging out...")
        handle_forced_logout(current_user_id)  # Ensure proper logout tracking
    sys.exit(0)

def get_menu(role):
    """Generate menu options based on user role."""
    menu = {
        '1': "Time Tracking",
        '2': "Shift Schedule",
        '3': "Last 3 Weeks' Pay",
        '4': "Holiday Calendar",
        '5': "Apply for Leave",
        '0': "Logout"
    }

    if role == "Admin":
        menu = {'1': "Onboard HR", '0': "Logout"}
    elif role == "Project Manager":
        menu.update({
            '6': "Assign Shifts",
            '7': "Approve/Reject Leave Requests"
        })
    elif role == "HR":
        menu.update({
            '6': "Assign Shifts",
            '7': "Approve/Reject Leave Requests",
            '8': "Onboard Employee",
            '9': "Offboard Employee",
            '10': "Process Payroll & Send Payslips",
            '11': "Add Holiday",
            '12': "Delete Holiday",
            '13': "View Holiday Calendar"
        })
    
    return menu

def main():
    global current_user_id
    parser = argparse.ArgumentParser(description="Payroll System CLI")
    parser.add_argument("--login", action="store_true", help="User logs in")

    args = parser.parse_args()

    if args.login:
        print("\n Login to the Payroll System")
        user_id = input("Enter your User ID: ").strip()

        if not user_id.isdigit():
            print("Error: User ID must be a number.")
            return
        
        user_id = int(user_id)  # Convert input to integer
        password = getpass.getpass("Enter your password: ")  # Secure password input

        conn = get_db_connection()
        cur = conn.cursor()

        # Authenticate user
        cur.execute("SELECT user_id, designation FROM users WHERE user_id = %s", (user_id,))
        user = cur.fetchone()

        if not user:
            print("Invalid User ID. Try again.")
            return
        
        authenticated_user_id, designation = user

        if authenticated_user_id:
            print(f"\n Logged in as {designation} (User ID: {user_id})")

            # Setup Ctrl + C signal handler
            setup_signal_handler(user_id)

            shift_mgmt = ShiftManagement()
            payroll_hist = PayrollHistory()
            holiday_cal = HolidayCalendar()
            leave_mgmt = LeaveManagement()
            hr = HR()
            payroll = PayrollSystem()

            menu = get_menu(designation)

            while True:
                print("\n MAIN MENU")
                for key, value in menu.items():
                    print(f"{key}. {value}")

                choice = input("Enter your choice: ")
                if choice == '0':
                    print("\n Logging out...")
                    print(end_time_tracking(user_id))
                    break
                elif choice == '1':
                    print(start_time_tracking(user_id))  # Start time tracking
                elif choice == '2':
                    print(shift_mgmt.view_shift_schedule(user_id))
                elif choice == '3':
                    print(payroll_hist.get_last_three_weeks_pay(user_id))
                elif choice == '4':
                    print(holiday_cal.view_holiday_calendar(user_id))
                elif choice == '5':
                    emp_id = user_id
                    start_date = input("Enter Start Date (YYYY-MM-DD): ")
                    end_date = input("Enter End Date (YYYY-MM-DD): ")
                    reason = input("Enter Leave Reason: ")
                    print(leave_mgmt.apply_leave(emp_id, start_date, end_date, reason))
                elif choice == '6' and designation == "Project Manager":
                    print(assign_shift(user_id))
                elif choice == '7' and designation in ["Project Manager", "HR"]:
                    print(leave_mgmt.process_leave_request(user_id))  # ✅ **No more Employee ID input**
                elif choice == '8' and designation == "HR":
                    print(hr.onboard_employee())  
                elif choice == '9' and designation == "HR":
                    print(hr.offboard_employee())  
                elif choice == '10' and designation == "HR":
                    print(payroll.process_weekly_payroll(user_id))
                elif choice == '11' and designation == "HR":
                    print(holiday_cal.add_holiday())
                elif choice == '12' and designation == "HR":
                    print(holiday_cal.delete_holiday())
                elif choice == '13' and designation == "HR":
                    print(holiday_cal.view_holiday_calendar(user_id))
                elif choice == '14': 
                    print(end_time_tracking(user_id))  #  Manual logout tracking
                else:
                    print("Invalid option. Try again.")

        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
