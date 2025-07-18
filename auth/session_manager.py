import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import json



# Google Sheets config from streamlit secrets
SHEET_NAME = "ResumeAnalyzerUsers"  # Your spreadsheet name
TAB_NAME = "Users"  # Your sheet/tab name

# Load credentials and initialize gspread
sheet_creds = st.secrets["gspread_service_account"]
gc = gspread.authorize(Credentials.from_service_account_info(sheet_creds))
worksheet = gc.open(SHEET_NAME).worksheet(TAB_NAME)

def init_session_state():
    """Initialize Streamlit session state variables."""
    defaults = {
        "is_logged_in": False,
        "user_data": {},
        "usage_count": 0,
        "max_usage": 5,
        "email": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_user_row(email):
    """Find user row number by email."""
    try:
        emails = worksheet.col_values(1)
        if email in emails:
            return emails.index(email) + 1  # +1 for 1-based indexing
        return None
    except Exception as e:
        st.error(f"Error fetching user row: {e}")
        return None

def get_user_data(email):
    """Return user data as dict from the sheet."""
    row_number = get_user_row(email)
    if row_number is None:
        return None

    row_data = worksheet.row_values(row_number)
    headers = worksheet.row_values(1)

    # Fill missing cells with empty string
    if len(row_data) < len(headers):
        row_data += [""] * (len(headers) - len(row_data))

    user_data = dict(zip(headers, row_data))

    # Set default usage if empty
    if not user_data.get("usage_count"):
        user_data["usage_count"] = "0"
    if not user_data.get("max_usage"):
        user_data["max_usage"] = "5"

    return user_data

def update_usage(email):
    """Increment usage_count for a user in Google Sheet."""
    row_number = get_user_row(email)
    if row_number is None:
        return

    usage_cell = f"{get_column_letter('usage_count')}{row_number}"
    current_usage = int(worksheet.acell(usage_cell).value or "0")
    worksheet.update_acell(usage_cell, str(current_usage + 1))

def get_column_letter(column_name):
    """Get the column letter for a column name."""
    headers = worksheet.row_values(1)
    if column_name not in headers:
        raise ValueError(f"Column '{column_name}' not found.")
    col_index = headers.index(column_name) + 1
    return gspread.utils.rowcol_to_a1(1, col_index)[0]

