import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Config
TAB_NAME = "Users"
spreadsheet_id = st.secrets["gcp_service_account"]["sheet_id"]  # ✅ FIXED

# Auth
creds = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)
service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()

def get_range(start_cell="A1:Z1000"):
    return f"{TAB_NAME}!{start_cell}"

def init_session_state():
    defaults = {
        "is_logged_in": False,
        "user_data": {},
        "usage_count": 0,
        "max_usage": 3,
        "email": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_user_row(email):
    try:
        result = sheet.values().get(spreadsheetId=spreadsheet_id, range=get_range("A2:A")).execute()
        emails = result.get("values", [])
        for i, row in enumerate(emails, start=2):
            if row and row[0].strip().lower() == email.strip().lower():
                return i
        return None
    except Exception as e:
        st.error(f"Error finding user row: {e}")
        return None

def get_user_data(email):
    try:
        headers = sheet.values().get(spreadsheetId=spreadsheet_id, range=get_range("1:1")).execute().get("values", [[]])[0]
        row_number = get_user_row(email)
        if not row_number:
            return None
        row_data = sheet.values().get(spreadsheetId=spreadsheet_id, range=get_range(f"{row_number}:{row_number}")).execute().get("values", [[]])[0]

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
    try:
        row_number = get_user_row(email)
        if not row_number:
            return

        headers = sheet.values().get(spreadsheetId=spreadsheet_id, range=get_range("1:1")).execute().get("values", [[]])[0]
        usage_index = headers.index("usage_count")

        row_data = sheet.values().get(spreadsheetId=spreadsheet_id, range=get_range(f"{row_number}:{row_number}")).execute().get("values", [[]])[0]
        current_usage = int(row_data[usage_index]) if len(row_data) > usage_index and row_data[usage_index].isdigit() else 0
        row_data[usage_index] = str(current_usage + 1)

        update_range = get_range(f"{row_number}:{row_number}")
        sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=update_range,
            valueInputOption="RAW",
            body={"values": [row_data]}
        ).execute()
    except Exception as e:
        st.error(f"Error updating usage count: {e}")

def store_user(email, name, password, age=None, gender=None):
    try:
        headers = sheet.values().get(spreadsheetId=spreadsheet_id, range=get_range("1:1")).execute().get("values", [[]])[0]
        new_user = {
            "email": email,
            "name": name,
            "password": password,
            "usage_count": "0",
            "max_usage": "5",
            "age": age or "",
            "gender": gender or ""
            "otp": "",
        }

        row = [new_user.get(header, "") for header in headers]
        sheet.values().append(
            spreadsheetId=spreadsheet_id,
            range=get_range(),
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": [row]}
        ).execute()
        return True
    except Exception as e:
        st.error(f"Error storing new user: {e}")
        return False

def authenticate_user(email, password):
    try:
        user = get_user_data(email)
        if user and user.get("password") == password:
            return True
        return False
    except Exception as e:
        st.error(f"Authentication failed: {e}")
        return False
