from db import get_db_connection

class HolidayCalendar:
    def view_holiday_calendar(self, emp_id):
        """Fetch holidays applicable to an employee based on their ethnicity."""
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT holiday_name, holiday_date FROM holiday_calendar
            WHERE applicable_ethnicity = 'All' OR applicable_ethnicity = 
            (SELECT ethnicity FROM users WHERE user_id = %s)
            ORDER BY holiday_date
        """, (emp_id,))
        
        holidays = cur.fetchall()
        cur.close()
        conn.close()

        if holidays:
            holiday_list = "\n Upcoming Holidays:\n"
            for holiday in holidays:
                holiday_list += f"• {holiday[0]} on {holiday[1]}\n"
            return holiday_list
        else:
            return "No upcoming holidays."

    def add_holiday(self):
        """HR adds a new holiday."""
        print("\n Add New Holiday")
        holiday_name = input("Enter Holiday Name: ")
        holiday_date = input("Enter Holiday Date (YYYY-MM-DD): ")
        ethnicity = input("Enter Applicable Ethnicity ('All' for public holidays, or specific group like 'Māori'): ")

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO holiday_calendar (holiday_name, holiday_date, applicable_ethnicity) VALUES (%s, %s, %s)",
                    (holiday_name, holiday_date, ethnicity))
        conn.commit()
        cur.close()
        conn.close()

        return f"Holiday '{holiday_name}' added successfully!"

    def delete_holiday(self):
        """Show available holidays and confirm before deletion."""
        print("\n **Available Holidays:**")
        available_holidays = self.view_holiday_calendar(None)

        if "No holidays found." in available_holidays:
            print("No holidays available to delete.")
            return

        print(available_holidays)  #  Display all holidays
        
        #  Ask for the holiday name
        holiday_name = input("\n Enter the Holiday Name to Delete: ").strip()

        if not holiday_name:
            print("Invalid input. Please enter a valid holiday name.")
            return
        
        #  Confirm before deleting
        confirmation = input(f" Are you sure you want to delete '{holiday_name}'? (yes/no): ").strip().lower()
        
        if confirmation != "yes":
            print("Holiday deletion canceled.")
            return

        #  Proceed with deletion
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("DELETE FROM holiday_calendar WHERE holiday_name = %s RETURNING *", (holiday_name,))
        deleted_rows = cur.rowcount
        
        conn.commit()
        cur.close()
        conn.close()
        if deleted_rows > 0:
            message = f"Holiday '{holiday_name}' deleted successfully."
            return message  # Explicitly return success message
        else:
            message = f" Holiday '{holiday_name}' not found."
            return message  # Explicitly return failure message