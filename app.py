import os
import json
import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI
import gspread
from google.oauth2.service_account import Credentials
import re

# ---------- 🔐 Load credentials ----------
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
sheet_creds = json.loads(st.secrets["gspread_service_account"].to_json())
creds = Credentials.from_service_account_info(sheet_creds, scopes=SCOPES)

gc = gspread.authorize(creds)
SHEET_NAME = "ResumeAnalyzerUsers"
TAB_NAME = "Users"
sheet = gc.open(SHEET_NAME).worksheet(TAB_NAME)

client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# ---------- 🧠 Functions ----------
def get_user_data(email):
    users = sheet.get_all_records()
    for i, user in enumerate(users, start=2):
        if user["email"].lower() == email.lower():
            return i, user
    return None, None

def update_usage(email):
    row_num, user = get_user_data(email)
    if not user:
        return False

    if user["max_usage"].lower() != "unlimited":
        if int(user["usage_count"]) >= int(user["max_usage"]):
            return False
        new_count = int(user["usage_count"]) + 1
        sheet.update_cell(row_num, 6, new_count)  # usage_count = col 6
        user["usage_count"] = new_count  # update local cache too
    return True

def generate_analysis(resume_text, jd_text):
    prompt = f"""
You are a professional HR recruiter. Compare the following resume and job description, and:
1. List 3 strengths and 3 weaknesses.
2. Give a matching score between 0-100%.
3. Finally, write a short recommendation about whether the candidate is a good fit and why.

Resume:
{resume_text}

Job Description:
{jd_text}
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# ---------- 🌟 Streamlit UI ----------
st.set_page_config(page_title="Resume Analyzer & Job Match Bot", page_icon="🧠")
st.title("🧠 Resume Analyzer & Job Match Bot")
st.markdown("Compare your resume to a job description and get match score, strengths, weaknesses & feedback.")

# ---------- 🔐 Login ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.subheader("🔐 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        _, user = get_user_data(email)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.email = email
            st.success("Logged in successfully.")
            st.experimental_rerun()
        else:
            st.error("Invalid email or password.")
    st.stop()

# ---------- 👤 Show User Info ----------
row_num, user = get_user_data(st.session_state.email)
usage_count = int(user["usage_count"])
max_usage = user["max_usage"]

st.info(
    f"👤 **Name:** {user['name']} | 📧 **Email:** {user['email']}  \n"
    f"📊 **Usage:** {usage_count} / {max_usage}"
)

# ---------- 📤 Upload & Analyze ----------
st.subheader("📄 Upload Resume (PDF) and Paste Job Description")
resume_file = st.file_uploader("Upload Resume PDF", type=["pdf"])
job_desc = st.text_area("Paste Job Description", height=200)

if st.button("Analyze Match"):
    if not resume_file or not job_desc.strip():
        st.warning("Please upload resume and paste job description.")
    elif max_usage.lower() != "unlimited" and usage_count >= int(max_usage):
        st.error("⚠️ You’ve reached your usage limit.")
    else:
        resume_text = extract_text_from_pdf(resume_file)
        with st.spinner("Analyzing..."):
            result = generate_analysis(resume_text, job_desc)
        st.success("✅ Analysis Complete!")
        st.markdown("### 📊 Analysis Result")
        st.markdown(result)

        # Extract score % if present
        score_match = re.search(r"(\d{1,3})\s*[%]", result)
        if score_match:
            percent_score = int(score_match.group(1))
            st.progress(min(percent_score, 100) / 100)

        # Final Recommendation
        st.markdown("### 🎯 Final Recommendation")
        if "good fit" in result.lower():
            st.success("The candidate is likely a **strong fit** for this role based on the resume.")
        elif "not a good fit" in result.lower() or "weak fit" in result.lower():
            st.error("The candidate is **not an ideal match**. Consider tailoring the resume.")
        else:
            st.info("Review the analysis to understand alignment.")

        # ✅ Increment usage
        update_usage(st.session_state.email)
        st.experimental_rerun()
