# Payroll-system --CLI Application
This is a command line Payroll system  built using Python. Payroll system supports HR, Project Managers, and Employees providing the following functionalities:

 Authentication & Security:
Secure login with bcrypt password hashing
First-time login password reset enforcement
Role-based access control (RBAC) for HR, Project Managers, and Employees
Session tracking & forced logout detection

 Employee Management:
Onboard Employees & HR Users (by HR only)
Assign Reporting Managers
Capture Employee Details (Name, Email, Designation, IRD Number, Bank Details, Nationality, Region, Ethnicity)
Default Shift Assignment (General Shift: 9 AM - 5 PM)
Offboard Employees (Remove from the system)

Time Tracking:
Clock-In & Clock-Out for employees
Tracks daily login/logout times
Prevents early logout without manager approval
Detects forced logouts (e.g., system crashes, Ctrl+C interrupts)

Payroll Processing:
Weekly payroll processing (HR manually triggers it)
Salary breakdown includes:
Regular pay (calculated based on hourly rate)
Overtime pay (1.5x hourly rate for extra hours)
Holiday pay (based on public, Māori, and regional holidays)
Māori Bonus (5% additional earnings for Māori employees)
Night shift allowance (For employees working night shifts)
Tax deductions (15%)
Annual Salary Hike (Automatically applied at year-end under development)

Payslip Generation:
Automatic PDF payslip generation
Displays salary breakdown in a clean, tabular format
Includes IRD Number & Bank Details
Supports Māori Language for Māori employees
Company Name highlighted in payslip
Payslip emailed automatically to employees

Leave Management:
Employees can apply for leave (Start date, end date, reason)
HR & Project Managers can approve/reject leave requests
Managers receive email notifications for leave requests
Employees receive email notifications for approvals/rejections

Shift Management:
Employees can view their shift schedules
Project Managers & HR can assign shifts
Night shifts are tracked for payroll calculations

Payroll History & Reporting:
Employees can view their last 3 weeks' payroll history
HR & Project Managers can view payroll reports for all employees
Tax deductions are properly displayed in reports

Holiday Calendar Management:
HR can add/remove public & company-specific holidays
Includes all New Zealand & Māori holidays
Holiday pay is calculated based on region, nationality, and ethnicity

Email Notifications:
Payslip Emails - Sent automatically after payroll processing
Leave Approval/Rejection Emails - Sent to employees
Leave Request Notifications - Sent to managers
Payroll Processed Notifications - Sent to HR

Additional Features:
User-friendly CLI interface
Auto-detection of invalid inputs
Error handling for database connectivity & email issues
Secure password management using bcrypt
Efficient SQL queries for faster payroll processing

Project Structure:

 payroll-system/
│── 📄 cli.py               # Main CLI entry point
│── 📄 db.py                # Database connection & authentication
│── 📄 payroll.py           # Payroll processing & payslip generation
│── 📄 shift_leave.py       # Shift & leave management
│── 📄 hr.py                # HR functionalities (Onboarding, Offboarding)
│── 📄 holiday_calendar.py  # Holiday management
│── 📄 email_service.py     # Email handling for notifications
│── 📄 config.ini           # Configuration file (database, email settings)
│── 📄 requirements.txt     # Required Python packages
│── 📄 README.md            # Project documentation

Installation & Setup:
1.Clone Repository from GIT:
git clone https://github.com/kiran260889/Payroll-system.git
cd payroll-system
2.Install Dependencies:
pip install -r requirements.txt
3.No need to create Database as it AWS clould

How to use:
Please use as below when you are the first user to the system.
python cli.py --login
Enter User ID:1
Enter Password:admin123

Flow of the Application:
1.On Board a HR to the Application then remove id 1 from database using the below command
delete from users where id=1;
2.Now the HR will do all the onboarding process of the emplyoees.

Role-Based Main Menu Navigation:
Upon successful login, users access a menu based on their role:

Role	             Accessible Features
Employee	        Time Tracking, Payslips, Leave Requests, Shift Viewing, Logout
Project Manager 	Approve/Reject Leaves, Assign Shifts, View Reports, Logout
HR	                Onboard/Offboard Employees, Process Payroll, Approve Leaves, ManageHolidays,Logout

Users select an option, triggering respective functionalities.

For Delatiled documentation please refer to the user_documentation.






