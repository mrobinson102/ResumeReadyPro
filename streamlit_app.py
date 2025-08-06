import streamlit as st
import openai
import os
from io import BytesIO
from PyPDF2 import PdfReader
from fpdf import FPDF
from dotenv import load_dotenv
import streamlit_authenticator as stauth
from datetime import datetime
import sqlite3

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Authentication Setup ---
hashed_passwords = stauth.Hasher(['adminpass']).generate()
authenticator = stauth.Authenticate(
    {'admin': {'name': 'Admin User', 'password': hashed_passwords[0]}},
    'resume_app', 'abcdef', cookie_expiry_days=30
)
name, authentication_status, username = authenticator.login('Login', 'main')

# --- App Content ---
if authentication_status:
    authenticator.logout('Logout', 'sidebar')

    st.set_page_config(page_title="ResumeReadyPro", page_icon="📄", layout="centered")
    st.title("📄 ResumeReadyPro")
    st.subheader("AI-Powered Resume & Interview Builder")
    st.markdown("---")

    st.image("logo.png", width=150)

    # Form Inputs
    name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    uploaded_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])

    if "summary" not in st.session_state:
        st.session_state.summary = ""
    if "interview_questions" not in st.session_state:
        st.session_state.interview_questions = ""

    if uploaded_file:
        reader = PdfReader(uploaded_file)
        full_text = ""
        for page in reader.pages:
            full_text += page.extract_text()

        st.text_area("Extracted Resume Text", value=full_text, height=200)

        if st.button("Generate Summary & Questions"):
            with st.spinner("Processing with AI..."):
                try:
                    # Generate summary
                    summary_response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "user", "content": f"Write a 3-4 sentence professional summary for this resume:\n{full_text}"}
                        ]
                    )
                    summary = summary_response.choices[0].message.content.strip()
                    st.session_state.summary = summary

                    # Generate interview questions
                    questions_response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "user", "content": f"Based on this resume, generate 5 potential interview questions:\n{full_text}"}
                        ]
                    )
                    questions = questions_response.choices[0].message.content.strip()
                    st.session_state.interview_questions = questions

                    # Save to SQLite database
                    conn = sqlite3.connect("resume_logs.db")
                    c = conn.cursor()
                    c.execute('''CREATE TABLE IF NOT EXISTS logs
                                 (timestamp TEXT, name TEXT, email TEXT, summary TEXT, questions TEXT)''')
                    c.execute("INSERT INTO logs VALUES (?, ?, ?, ?, ?)", 
                              (datetime.now().isoformat(), name, email, summary, questions))
                    conn.commit()
                    conn.close()

                    st.success("Resume summary and questions generated successfully!")
                except Exception as e:
                    st.error(f"AI Error: {e}")

    if st.session_state.summary:
        st.markdown("### ✨ AI-Generated Summary")
        st.info(st.session_state.summary)

    if st.session_state.interview_questions:
        st.markdown("### ❓ Interview Questions")
        st.info(st.session_state.interview_questions)

        # TXT Download
        txt_data = f"""{name}
{email}

--- Resume Summary ---
{st.session_state.summary}

--- Interview Questions ---
{st.session_state.interview_questions}
"""
        st.download_button("⬇️ Download as TXT", data=txt_data, file_name="resume_output.txt", mime="text/plain")

        # PDF Download
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in txt_data.split('\n'):
            pdf.multi_cell(0, 10, line)
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        st.download_button("⬇️ Download as PDF", data=pdf_output, file_name="resume_output.pdf", mime="application/pdf")

else:
    st.warning("Please log in to access the application.")
