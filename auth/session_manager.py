import os
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# Google Sheet Configuration
SERVICE_ACCOUNT_PATH = os.path.join(os.path.dirname(__file__), "../secrets/gsheets_credentials.json")
SHEET_NAME = "ResumeAnalyzerUsers"  # 📌 Spreadsheet file name
TAB_NAME = "Users"  # ✅ Sheet tab name within the spreadsheet

def init_session_state():
    default_values = {
        "logged_in": False,
        "email": "",
        "otp_sent": False,
        "awaiting_otp": False,
        "name": "",
        "usage_count": 0,
        "max_usage": "5",
        "age": "",
        "gender": ""
    }
    for key, value in default_values.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_worksheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_PATH, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME)
    return sheet.worksheet(TAB_NAME)

def load_users():
    ws = get_worksheet()
    return ws.get_all_records()

def store_user(name, email, password, age, gender):
    ws = get_worksheet()
    users = load_users()

    if any(str(user.get("email", "")).strip().lower() == email.strip().lower() for user in users):
        return False

    ws.append_row([
        email.strip(),
        password.strip(),
        name.strip(),
        age.strip(),
        gender.strip(),
        "",   # OTP
        0,    # usage_count
        "5"   # max_usage
    ])
    return True

def authenticate_user(email, password):
    users = load_users()
    for user in users:
        if (
            str(user.get("email", "")).strip().lower() == email.strip().lower() and
            str(user.get("password", "")).strip() == password.strip()
        ):
            st.session_state.logged_in = True
            st.session_state.email = email.strip()
            st.session_state.name = str(user.get("name", ""))
            st.session_state.age = str(user.get("age", ""))
            st.session_state.gender = str(user.get("gender", ""))
            st.session_state.usage_count = int(user.get("usage_count", 0))
            st.session_state.max_usage = str(user.get("max_usage", "5"))
            return True
    return False

def get_user_data(email):
    users = load_users()
    for i, user in enumerate(users):
        if str(user.get("email", "")).strip().lower() == email.strip().lower():
            return i, user
    return None, None

def update_otp(email, otp):
    ws = get_worksheet()
    cell = ws.find(email)
    if cell:
        otp_col = 6  # Column F
        ws.update_cell(cell.row, otp_col, otp)

def verify_otp_in_sheet(email, input_otp):
    _, user = get_user_data(email)
    return user and str(user.get("otp", "")).strip() == str(input_otp).strip()

def increment_usage(email):
    ws = get_worksheet()
    cell = ws.find(email)
    if cell:
        usage_col = 7  # Column G
        current_count = int(ws.cell(cell.row, usage_col).value or 0)
        ws.update_cell(cell.row, usage_col, current_count + 1)
        st.session_state.usage_count = current_count + 1
