import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Sheets config
SHEET_NAME = "ResumeAnalyzerUsers"  # Spreadsheet name
TAB_NAME = "Users"  # Tab name

# Load credentials and build Sheets API client
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

# Helper to get full range like Users!A1:Z1000
def get_range(start_cell="A1:Z1000"):
    return f"{TAB_NAME}!{start_cell}"

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
    """Find user row number by email (1-based index)."""
    try:
        result = sheet.values().get(spreadsheetId=SHEET_NAME, range=get_range("A2:A")).execute()
        emails = result.get("values", [])
        for i, row in enumerate(emails, start=2):  # Starting from row 2
            if row and row[0].strip().lower() == email.strip().lower():
                return i
        return None
    except Exception as e:
        st.error(f"Error finding user row: {e}")
        return None

def get_user_data(email):
    """Return user data as dict from the sheet."""
    try:
        headers = sheet.values().get(spreadsheetId=SHEET_NAME, range=get_range("1:1")).execute().get("values", [[]])[0]
        row_number = get_user_row(email)
        if not row_number:
            return None
        row_data = sheet.values().get(spreadsheetId=SHEET_NAME, range=get_range(f"{row_number}:{row_number}")).execute().get("values", [[]])[0]

        # Fill missing fields
        if len(row_data) < len(headers):
            row_data += [""] * (len(headers) - len(row_data))

        user_data = dict(zip(headers, row_data))
        if not user_data.get("usage_count"):
            user_data["usage_count"] = "0"
        if not user_data.get("max_usage"):
            user_data["max_usage"] = "5"

        return user_data
    except Exception as e:
        st.error(f"Error fetching user data: {e}")
        return None

def update_usage(email):
    """Increment usage_count for a user in Google Sheet."""
    try:
        row_number = get_user_row(email)
        if not row_number:
            return

        headers = sheet.values().get(spreadsheetId=SHEET_NAME, range=get_range("1:1")).execute().get("values", [[]])[0]
        usage_index = headers.index("usage_count")

        row_data = sheet.values().get(spreadsheetId=SHEET_NAME, range=get_range(f"{row_number}:{row_number}")).execute().get("values", [[]])[0]
        current_usage = int(row_data[usage_index]) if len(row_data) > usage_index and row_data[usage_index].isdigit() else 0
        row_data[usage_index] = str(current_usage + 1)

        # Update only usage_count cell
        update_range = get_range(f"{row_number}:{row_number}")
        values = [row_data]
        sheet.values().update(
            spreadsheetId=SHEET_NAME,
            range=update_range,
            valueInputOption="RAW",
            body={"values": values}
        ).execute()
    except Exception as e:
        st.error(f"Error updating usage count: {e}")
