import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

def log_user_interaction(user_email, action):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "google_creds.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)

    sheet = client.open("ResumeAnalyzerUsers")
    worksheet = sheet.worksheet("UserLogs")

    worksheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user_email,
        action
    ])
