import datetime
import os
from decimal import Decimal
from db import get_db_connection
from email_service import send_email
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, SimpleDocTemplate, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

class PayrollSystem:
    def process_weekly_payroll(self, hr_id):
        """HR manually processes payroll at the end of the week ONLY for employees with valid work hours."""
        today = datetime.date.today()
        week_start = today - datetime.timedelta(days=today.weekday())  # Monday
        week_end = today  # End of week (Sunday)

        conn = get_db_connection()
        cur = conn.cursor()

        #Fetch all employees (HR, PM, and Employees)
        cur.execute("SELECT user_id, annual_salary, ethnicity, nationality, region, email, name, designation, ird_number, bank_account FROM users")
        employees = cur.fetchall()

        if not employees:
            return "No payroll records to process."

        payroll_generated = False  # Track if payroll is generated for at least one employee

        for employee in employees:
            user_id, annual_salary, ethnicity, nationality, region, email, name, designation, ird_number, bank_account = employee

            # Convert Annual Salary to Hourly Rate
            weekly_hours = 40
            weeks_per_year = 52
            hourly_rate = round(Decimal(annual_salary) / (weeks_per_year * weekly_hours), 2)

            #  Fetch hours worked for each day of the week
            cur.execute("""
                SELECT DATE(login_time) AS work_date, 
                       SUM(EXTRACT(EPOCH FROM (logout_time - login_time)) / 3600) AS hours_worked
                FROM time_tracking
                WHERE user_id = %s 
                AND DATE(login_time) BETWEEN %s AND %s
                AND logout_time IS NOT NULL
                GROUP BY DATE(login_time)
                ORDER BY work_date
            """, (user_id, week_start, week_end))
            hours_worked = cur.fetchall()  # List of tuples: [(date, hours_worked), ...]

            if not hours_worked:
                print(f" Skipping payroll for {name} (ID: {user_id}) - No valid work hours this week.")
                continue  #  Skip payroll processing for this employee

            #  Calculate total hours worked for the week
            total_hours = sum(hours for _, hours in hours_worked)

            #  Calculate salary components
            base_hours = 40  # Standard weekly hours
            overtime_hours = max(total_hours - base_hours, 0)
            regular_hours = min(total_hours, base_hours)

            #  Convert values to Decimal
            total_hours = Decimal(total_hours)
            regular_hours = Decimal(regular_hours)
            overtime_hours = Decimal(overtime_hours)

            #  Calculate salary components
            regular_pay = regular_hours * hourly_rate
            overtime_rate = Decimal('1.5')
            overtime_pay = overtime_hours * (hourly_rate * overtime_rate)
            holiday_pay = Decimal(0)

            #  Calculate holiday pay based on region, nationality, and ethnicity
            cur.execute("""
                SELECT COUNT(*) FROM holiday_calendar 
                WHERE holiday_date BETWEEN %s AND %s
                AND (region = %s OR region = 'All')
                AND (nationality = %s OR nationality = 'All')
                AND (applicable_ethnicity = %s OR applicable_ethnicity = 'All')
            """, (week_start, week_end, region, nationality, ethnicity))
            holiday_count = cur.fetchone()[0]
            holiday_pay = Decimal(holiday_count * (hourly_rate * 8))  # 8 hours per holiday

            #  Māori 5% additional pay
            is_maori = ethnicity.strip().lower() in ["māori", "maori"]
            maori_bonus = (regular_pay + overtime_pay + holiday_pay) * Decimal('0.05') if is_maori else Decimal(0)

            #  Night shift allowance (For Employees only)
            night_shift_allowance = Decimal(0)
            if designation == "Employee":
                cur.execute("SELECT COUNT(*) FROM employee_shifts WHERE user_id = %s AND shift_code = 'N'", (user_id,))
                night_shift_days = cur.fetchone()[0]
                night_shift_allowance = Decimal(night_shift_days * 0.25)

            total_earnings = regular_pay + overtime_pay + holiday_pay + maori_bonus + night_shift_allowance
            tax_deductions = round(total_earnings * Decimal('0.15'), 2)  # 15% tax
            final_salary = round(total_earnings - tax_deductions, 2)

            #  Generate Payslip for Employees with Valid Work Hours
            payslip_filename = f"payslip_{user_id}.pdf"
            self.generate_payslip(
    filename=payslip_filename,
    name=name,
    designation=designation,
    ird_number=ird_number,
    bank_account=bank_account,
    annual_salary=annual_salary,
    week_start=week_start,
    week_end=week_end,
    total_hours=total_hours,  
    regular_pay=regular_pay,
    overtime_pay=overtime_pay,
    holiday_pay=holiday_pay,
    maori_bonus=maori_bonus,
    night_shift_allowance=night_shift_allowance,
    total_earnings=total_earnings,
    tax_deductions=tax_deductions,
    final_salary=final_salary,
    is_maori=is_maori
)


            # Send payslip email with PDF attachment
            subject = "📑 Your Weekly Payslip"
            body = f"""
            Hello {name},

            Your payroll for the week {week_start} to {week_end} has been processed.
            Please find your payslip attached.

            Best Regards,
            Payroll System
            """
            send_email(email, subject, body, attachment_path=payslip_filename)

            payroll_generated = True  # At least one employee had payroll generated

        conn.commit()
        cur.close()
        conn.close()

        if not payroll_generated:
            return "No payroll processed. No employees logged in and out this week."

        return "Payroll processed successfully. Payslips have been emailed to employees who worked."

    def generate_payslip(self, filename, name, designation, ird_number, bank_account, annual_salary, 
                         week_start, week_end, total_hours, regular_pay, overtime_pay, holiday_pay, 
                         maori_bonus, night_shift_allowance, total_earnings, tax_deductions, final_salary, 
                         is_maori=False):
        """Generate a professional **tabular payslip** with Māori language support."""

        #  Company Name
        company_name = "Car Rental Corporation"

        #  Register Fonts
        font_path_regular = "NotoSans-Regular.ttf"
        font_path_bold = "NotoSans-Bold.ttf"
        if not os.path.exists(font_path_regular) or not os.path.exists(font_path_bold):        raise FileNotFoundError("❌ Missing font files 'NotoSans-Regular.ttf' or 'NotoSans-Bold.ttf'. Download them.")

        pdfmetrics.registerFont(TTFont("NotoSans", font_path_regular))
        pdfmetrics.registerFont(TTFont("NotoSans-Bold", font_path_bold))
        
        #  Create PDF Document
        doc = SimpleDocTemplate(filename, pagesize=letter)
        elements = []

        #  Styles
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        title_style.fontName = "NotoSans-Bold"
        title_style.fontSize = 20
        title_style.alignment = 1  # Centered

        normal_style = styles["Normal"]
        normal_style.fontName = "NotoSans"
        normal_style.fontSize = 12

        #  Convert Annual Salary to Hourly Rate
        weeks_per_year = 52
        weekly_hours = 40
        hourly_rate = round(Decimal(annual_salary) / (weeks_per_year * weekly_hours), 2)

        #  Māori Language Support
        lang = {
            "Employee Payslip": "Pūkete Utu Kaimahi" if is_maori else "Employee Payslip",
            "Employee": "Kaimahi" if is_maori else "Employee",
            "Designation": "Tūranga Mahi" if is_maori else "Designation",
            "IRD Number": "IRN Nama" if is_maori else "IRD Number",
            "Bank Account": "Pūkete Peeke" if is_maori else "Bank Account",
            "Week Start": "Tīmatanga Wiki" if is_maori else "Week Start",
            "Week End": "Mutunga Wiki" if is_maori else "Week End",
            "Earnings": "Ngā Moni whiwhi" if is_maori else "Earnings",
            "Hourly Rate": "Rahi Utu ā-haora" if is_maori else "Hourly Rate",
            "Total Hours Worked": "Ngā haora mahi katoa" if is_maori else "Total Hours Worked",
            "Regular Pay": "Utu auau" if is_maori else "Regular Pay",
            "Overtime Pay": "Utu haora taapiri" if is_maori else "Overtime Pay",
            "Holiday Pay": "Utu Hararei" if is_maori else "Holiday Pay",
            "Māori Bonus": "Tāpirihanga Māori" if is_maori else "Māori Bonus",
            "Night Shift Allowance": "Utu pō" if is_maori else "Night Shift Allowance",
            "Total Earnings": "Tapeke whiwhinga" if is_maori else "Total Earnings",
            "Deductions": "Nga tangohanga" if is_maori else "Deductions",
            "Tax Deductions": "Taake Tangohanga" if is_maori else "Tax Deductions",
            "Net Salary": "Utu tīmata" if is_maori else "Net Salary"
        }

        #  Add Company Name in Bold & Large Font
        elements.append(Paragraph(f"<b>{company_name}</b>", title_style))
        elements.append(Spacer(1, 12))  # Space

        #  Add Employee & Payroll Details
        elements.append(Paragraph(f"<b>{lang['Employee Payslip']}</b>", title_style))
        elements.append(Spacer(1, 10))

        employee_details = [
            [lang["Employee"], name],
            [lang["Designation"], designation],
            [lang["IRD Number"], ird_number],
            [lang["Bank Account"], bank_account],
            [lang["Week Start"], week_start],
            [lang["Week End"], week_end]
        ]

        table = Table(employee_details, colWidths=[150, 250])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'NotoSans'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 15))

        #  Salary Breakdown Table
        salary_data = [
            [lang["Earnings"], "Amount ($)"],
            [lang["Hourly Rate"], f"{hourly_rate:.2f}"],
            [lang["Total Hours Worked"], f"{total_hours:.2f} hrs"],
            [lang["Regular Pay"], f"{regular_pay:.2f}"],
            [lang["Overtime Pay"], f"{overtime_pay:.2f}"],
            [lang["Holiday Pay"], f"{holiday_pay:.2f}"],
            [lang["Māori Bonus"], f"{maori_bonus:.2f}"],
            [lang["Night Shift Allowance"], f"{night_shift_allowance:.2f}"],
            [lang["Total Earnings"], f"{total_earnings:.2f}"]
        ]

        salary_table = Table(salary_data, colWidths=[200, 120])
        salary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'NotoSans-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, 1), (-1, -1), 'NotoSans'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(salary_table)
        elements.append(Spacer(1, 15))

        #  Net Salary
        final_salary_table = Table([[lang["Net Salary"], f"${final_salary:.2f}"]], colWidths=[200, 120])
        final_salary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.green),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'NotoSans-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 16),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(final_salary_table)

        #  Build PDF
        doc.build(elements)