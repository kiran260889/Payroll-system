import smtplib
import os
import configparser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Load email config
config = configparser.ConfigParser()
config.read("config.ini")

# Ensure email configuration exists
if 'email' not in config.sections():
    raise KeyError("Error: Missing [email] section in config.ini. Please add it.")

try:
    SMTP_SERVER = config["email"]["smtp_server"]
    SMTP_PORT = int(config["email"]["smtp_port"])
    SENDER_EMAIL = config["email"]["sender_email"]
    SENDER_PASSWORD = config["email"]["sender_password"]
except KeyError as e:
    raise KeyError(f"Missing key in [email] section of config.ini: {e}")

def send_email(to_email, subject, body, attachment_path=None):
    """Send an email with an optional attachment (PDF payslip)."""
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    # Attach the email body
    msg.attach(MIMEText(body, 'plain'))

    # Attach PDF if provided and exists
    if attachment_path and os.path.exists(attachment_path):
        try:
            with open(attachment_path, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(attachment_path)}")
                msg.attach(part)
        except Exception:
            pass  # Silently fail if attachment cannot be processed

    try:
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return "Email sent successfully."
    except Exception as e:
        return f"Email sending failed: {e}"
