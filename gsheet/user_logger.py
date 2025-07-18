# utils/user_logger.py

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

def log_user_interaction(user_email, action):
    try:
        # Define the required scopes
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # Path to your service account credentials JSON
        creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "secrets/gsheets_credentials.json")
        creds = Credentials.from_service_account_file(creds_path, scopes=scope)

        # Authorize the client
        client = gspread.authorize(creds)

        # Open spreadsheet and worksheet
        sheet = client.open("ResumeAnalyzerUsers")
        worksheet = sheet.worksheet("UserLogs")

        # Append new row
        worksheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user_email,
            action
        ])
    except Exception as e:
        print(f"❌ Error logging user interaction: {e}")
