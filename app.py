import streamlit as st
from auth.session_manager import init_session_state, store_user, authenticate_user
from auth.otp_utils import send_otp_to_email, verify_otp
from PyPDF2 import PdfReader
from openai import OpenAI
import gspread
import json
from google.oauth2.service_account import Credentials

# ------------------- CONFIG -------------------
DEBUG_MODE = False
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# Google Sheets Setup
SHEET_NAME = "ResumeAnalyzerUsers"
TAB_NAME = "Users"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
sheet_creds = json.loads(st.secrets["gspread_service_account"]["content"])
creds = Credentials.from_service_account_info(sheet_creds, scopes=SCOPES)
gc = gspread.authorize(creds)
worksheet = gc.open(SHEET_NAME).worksheet(TAB_NAME)

# ------------------- USAGE FUNCTIONS -------------------
def get_user_row(email):
    try:
        cell = worksheet.find(email)
        return cell.row
    except:
        return None

def get_usage(email):
    row = get_user_row(email)
    if not row:
        return 0, "unknown"
    current = int(worksheet.cell(row, 6).value or 0)
    max_val = worksheet.cell(row, 7).value or "5"
    return current, max_val

def increment_usage(email):
    row = get_user_row(email)
    if not row:
        return False
    current = int(worksheet.cell(row, 6).value or 0)
    max_val = worksheet.cell(row, 7).value
    if max_val != "unlimited" and current >= int(max_val):
        return False
    worksheet.update_cell(row, 6, current + 1)
    return True

# ------------------- MAIN APP -------------------
def main():
    st.set_page_config(page_title="Resana Auth", layout="centered")
    init_session_state()

    if st.session_state.logged_in:
        dashboard()
    else:
        st.sidebar.title("Navigation")
        choice = st.sidebar.radio("Go to", ["Login", "Signup"])
        if choice == "Login":
            login_page()
        elif choice == "Signup":
            signup_page()

# ------------------- LOGIN PAGE -------------------
def login_page():
    st.title("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_user(email, password):
            st.session_state.email = email
            st.session_state.logged_in = True
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
                    "age": age,
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
                    data["name"],
                    data["email"],
                    data["password"],
                    str(data["age"]),
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
                st.error("❌ Usage limit reached. Please contact admin.")
                return

            reader = PdfReader(uploaded_file)
            resume_text = ""
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    resume_text += text

            prompt = f"""
Compare the resume to the job description and return:
- Match percentage (0–100%).
- Matched skills.
- Missing skills.
- One-line suitability summary.
- Final Recommendation: Strong / Medium / Weak Match.

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
