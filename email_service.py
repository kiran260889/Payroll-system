import smtplib
import configparser
from email.mime.text import MIMEText

# Load email config
config = configparser.ConfigParser()
config.read("config.ini")

# Ensure email configuration exists
if 'email' not in config.sections():
    raise KeyError("❌ Error: Missing [email] section in config.ini. Please add it.")

try:
    SMTP_SERVER = config["email"]["smtp_server"]
    SMTP_PORT = int(config["email"]["smtp_port"])
    SENDER_EMAIL = config["email"]["sender_email"]
    SENDER_PASSWORD = config["email"]["sender_password"]
except KeyError as e:
    raise KeyError(f"❌ Missing key in [email] section of config.ini: {e}")

def send_email(to_email, subject, body):
    """Send email notifications"""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    try:
        print(f"📧 Debug: Sending email to {to_email}")  # Debugging step
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, [to_email], msg.as_string())
        server.quit()
        print("✅ Debug: Email sent successfully.")  # Debugging step
        return "✅ Email sent successfully."
    except Exception as e:
        print(f"❌ Debug: Email sending failed: {e}")
        return f"❌ Email sending failed: {e}"
