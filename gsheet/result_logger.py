import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import os

def log_match_result(user_email, resume_text, job_description, match_score, tips):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "google_creds.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)

    sheet = client.open("ResumeAnalyzerUsers")
    worksheet = sheet.worksheet("ResumeMatchResults")

    worksheet.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user_email,
        resume_text[:500],        # Truncate for storage
        job_description[:500],    # Truncate for storage
        match_score,
        tips
    ])
