import streamlit as st
import openai
import pandas as pd
import datetime
import pytz
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- SETUP OPENAI ---
openai.api_key = st.secrets["openai_api_key"]

# --- GOOGLE SHEETS SETUP ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)
client = gspread.authorize(credentials)
SHEET_NAME = "YourGoogleSheetNameHere"
sheet = client.open(SHEET_NAME).sheet1

# --- FUNCTIONS ---

def get_user_data():
    return sheet.get_all_records()

def append_user(email, password, name, age, gender):
    sheet.append_row([email, password, name, age, gender, "", "0", "3"])  # 0 usage, 3 max_usage default

def get_user(email, password):
    users = get_user_data()
    for user in users:
        if user["email"] == email and user["password"] == password:
            return user
    return None

def update_usage(email, new_usage):
    cell = sheet.find(email)
    usage_cell = f"G{cell.row}"  # usage
    sheet.update_acell(usage_cell, str(new_usage))

def increment_usage(email):
    cell = sheet.find(email)
    usage = int(sheet.cell(cell.row, 7).value)  # column G
    max_usage = sheet.cell(cell.row, 8).value  # column H
    if max_usage.lower() != "unlimited" and usage >= int(max_usage):
        return False
    sheet.update_cell(cell.row, 7, str(usage + 1))
    return True

def get_max_usage(email):
    cell = sheet.find(email)
    return sheet.cell(cell.row, 8).value

def get_current_usage(email):
    cell = sheet.find(email)
    return sheet.cell(cell.row, 7).value

def show_dashboard(user):
    st.subheader("📊 Dashboard")
    st.markdown(f"""
        - 👤 **Name**: {user['name']}
        - 🎂 **Age**: {user['age']}
        - ⚧️ **Gender**: {user['gender']}
        - 📧 **Email**: {user['email']}
        - ✅ **Usage**: {get_current_usage(user['email'])} / {get_max_usage(user['email'])}
        - 💬 **Contact**: contact@example.com
    """)

    st.divider()
    st.subheader("📁 Main Feature")

    # Example: usage-based access
    if st.button("🔍 Run Analysis"):
        if not increment_usage(user['email']):
            st.error("❌ Usage limit reached. Please upgrade to continue.")
        else:
            st.success("✅ Feature executed. Usage updated.")
            # Your actual app feature logic goes here

# --- AUTH UI ---

def main():
    st.title("🔐 AI App with Usage Limits & Google Sheet Auth")
    menu = ["Login", "Sign Up"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Sign Up":
        st.subheader("Create New Account")
        with st.form("signup_form"):
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value=1, step=1)
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Sign Up")
            if submit:
                users = get_user_data()
                if any(u['email'] == email for u in users):
                    st.warning("🚫 Email already exists.")
                else:
                    append_user(email, password, name, age, gender)
                    st.success("✅ Account created! Please log in.")

    elif choice == "Login":
        st.subheader("Login to Your Account")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = get_user(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user = user
                st.session_state.email = user["email"]
                st.success(f"Welcome {user['name']}!")
                show_dashboard(user)
            else:
                st.error("❌ Invalid credentials")

    if st.session_state.get("logged_in", False):
        show_dashboard(st.session_state.user)

if __name__ == "__main__":
    main()
