import openai
import streamlit as st
import PyPDF2

# Load API key securely from Streamlit secrets
client = openai.OpenAI(api_key=st.secrets["openai"]["api_key"])

def extract_text_from_pdf(pdf_file):
    """Extracts text from uploaded PDF file."""
    pdf_file.seek(0)
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text if text else "No readable text found in the uploaded PDF."

def analyze_resume_match(resume_text, job_description):
    """
    Analyzes match between resume and job description using GPT.
    Returns a match score and 3 improvement suggestions.
    """
    # Limit to prevent token overflow
    resume_text = resume_text[:3000]
    job_description = job_description[:2000]

    prompt = f"""
You are a professional HR analyst.

Compare the following resume and job description, then:
- Give a match score out of 100
- Suggest 3 improvements for better match

RESUME:
{resume_text}

JOB DESCRIPTION:
{job_description}

Respond in this format:
Match Score: XX%
Suggestions:
1.
2.
3.
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content.strip()
