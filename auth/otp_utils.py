# auth/utils_otp.py

import random
import smtplib
from email.mime.text import MIMEText

OTP_STORE = {}

def send_otp_to_email(email):
    otp = str(random.randint(100000, 999999))
    OTP_STORE[email] = otp

    sender_email = "rachit87911094@gmail.com"
    sender_password = "wams pdga tiek xmda"  # App-specific password

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

        print("OTP email sent successfully!")
        return otp
    except Exception as e:
        print(f"Failed to send OTP: {e}")
        return None

def verify_otp(email, otp_input):
    return OTP_STORE.get(email) == otp_input
