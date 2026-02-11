import streamlit as st
from auth.session_manager import init_session_state, store_user, authenticate_user
from auth.otp_utils import send_otp_to_email
from PyPDF2 import PdfReader
from openai import OpenAI
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import re

# ------------------- CONFIG -------------------
TAB_NAME = "Users"
DEBUG_MODE = False
client = OpenAI(
    api_key=st.secrets["aiintellisense"]["api_key"],
    base_url="https://api.aiintellisense.com/api/proxy/openai/v1"
)


# ------------------- GOOGLE SHEETS -------------------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds_dict = st.secrets["gcp_service_account"]
creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
sheets_service = build("sheets", "v4", credentials=creds)
spreadsheet_id = creds_dict["sheet_id"]

# ------------------- SHEET HELPERS -------------------
def get_sheet_values():
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{TAB_NAME}!A2:H"
    ).execute()
    return result.get("values", [])

def get_user_row_index(email):
    rows = get_sheet_values()
    for i, row in enumerate(rows):
        if row and row[0].strip().lower() == email.strip().lower():
            return i + 2
    return None

def get_usage(email):
    row = get_user_row_index(email)
    if not row:
        return 0, "unknown"
    values = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{TAB_NAME}!G{row}:H{row}"
    ).execute().get("values", [[]])[0]
    current = int(values[0]) if len(values) > 0 and values[0].isdigit() else 0
    max_val = values[1] if len(values) > 1 else "5"
    return current, max_val

def increment_usage(email):
    row = get_user_row_index(email)
    if not row:
        return False
    current, max_val = get_usage(email)
    if max_val != "unlimited" and current >= int(max_val):
        return False
    sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"{TAB_NAME}!G{row}",
        valueInputOption="RAW",
        body={"values": [[current + 1]]}
    ).execute()
    return True

# ------------------- MAIN APP -------------------
def main():
    st.set_page_config(page_title="Resume Analyzer Bot", layout="centered")
    init_session_state()

    if st.session_state.get("logged_in", False):
        dashboard()
    else:
        st.sidebar.title("Navigation")
        choice = st.sidebar.radio("Go to", ["Login", "Signup"])
        if choice == "Login":
            login_page()
        else:
            signup_page()

# ------------------- LOGIN PAGE -------------------
def login_page():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_user(email, password):
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("Invalid email or password.")

# ------------------- SIGNUP PAGE -------------------
def signup_page():
    st.title("📝 Signup")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")
    age = st.number_input("Age", min_value=1, max_value=120)
    gender = st.radio("Gender", ["Male", "Female", "Other"])

    if st.button("Generate OTP"):
        if not all([name, email, password, confirm_password]):
            st.warning("Please fill out all fields.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            otp = send_otp_to_email(email)
            if otp:
                st.session_state.signup_otp = otp
                st.session_state.signup_data = {
                    "name": name,
                    "email": email,
                    "password": password,
                    "age": str(age),
                    "gender": gender
                }
                st.success(f"OTP sent to {email}")
                if DEBUG_MODE:
                    st.info(f"DEBUG OTP: {otp}")
            else:
                st.error("❌ Failed to send OTP. Please try again.")

    if "signup_otp" in st.session_state:
        otp_input = st.text_input("Enter OTP to complete registration")
        if st.button("Register"):
            if otp_input == st.session_state.signup_otp:
                data = st.session_state.signup_data
                success = store_user(
                    data["email"],
                    data["name"],
                    data["password"],
                    data["age"],
                    data["gender"]
                )
                if success:
                    st.success("🎉 Registered successfully! Please login.")
                    del st.session_state.signup_otp
                    del st.session_state.signup_data
                else:
                    st.warning("User already exists.")
            else:
                st.error("❌ Invalid OTP. Please try again.")

# ------------------- DASHBOARD -------------------
def dashboard():
    st.title("📊 Resume Analyzer & Job Match Bot")
    st.write(f"Welcome, **{st.session_state.email}**!")

    used, maxed = get_usage(st.session_state.email)
    st.info(f"🧾 Usage: **{used} / {maxed}**")

    uploaded_file = st.file_uploader("Upload Resume PDF", type=["pdf"])
    job_description = st.text_area("Paste Job Description Here")

    if st.button("Analyze Match"):
        if uploaded_file and job_description:
            if not increment_usage(st.session_state.email):
                st.error("❌ Usage limit reached. Please contact admin at rachit.jb77@gmail.com with subject RAusage")
                return

            reader = PdfReader(uploaded_file)
            resume_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    # Remove invalid UTF-8 characters like emojis
                    clean_text = re.sub(r'[^\x00-\x7F]+', '', text)
                    resume_text += clean_text

            prompt = f"""
Compare the resume to the job description and return:
- Match percentage (0–100%)
- Matched skills
- Missing skills
- One-line suitability summary
- Final Recommendation: Strong / Medium / Weak Match

Resume:
{resume_text}

Job Description:
{job_description}
"""

            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful AI HR assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                result = response.choices[0].message.content
                st.success("✅ Analysis complete!")
                st.markdown("### 📋 Analysis Result")
                st.write(result)
            except Exception as e:
                st.error(f"❌ OpenAI API error: {e}")
        else:
            st.warning("Please upload resume and enter job description.")

    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.email = ""
        st.rerun()

# ------------------- RUN APP -------------------
if __name__ == "__main__":
    main()






