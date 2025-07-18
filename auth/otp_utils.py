import random
import smtplib
from email.mime.text import MIMEText
import os

OTP_STORE = {}

def send_otp_to_email(email):
    otp = str(random.randint(100000, 999999))
    OTP_STORE[email] = otp

    sender_email = os.getenv("SENDER_EMAIL", "rachit87911094@gmail.com")
    sender_password = os.getenv("SENDER_PASSWORD", "wams pdga tiek xmda")  # Ideally set in secrets.toml or env var

    try:
        msg = MIMEText(f"Your OTP is: {otp}")
        msg["Subject"] = "Your OTP for Resume Analyzer Signup"
        msg["From"] = sender_email
        msg["To"] = email

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        print(f"OTP sent to {email}")
        return otp
    except Exception as e:
        print(f"Failed to send OTP to {email}: {e}")
        return None

def verify_otp(email, otp_input):
    return OTP_STORE.get(email) == otp_input
