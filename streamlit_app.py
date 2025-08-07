import streamlit as st
import openai
import os
from io import BytesIO
from fpdf import FPDF
from PyPDF2 import PdfReader
import pandas as pd
import json
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv
import matplotlib.pyplot as plt

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Authentication Setup
hashed_passwords = stauth.Hasher(['adminpass']).generate()
credentials = {
    'usernames': {
        'admin': {
            'name': 'Admin User',
            'password': hashed_passwords[0]
        }
    }
}

authenticator = stauth.Authenticate(
    credentials,
    'resume_app', 'abcdef', cookie_expiry_days=30
)

# Set global app config
st.set_page_config(page_title="ResumeReadyPro", page_icon="📄", layout="wide")

# Custom login UI
st.markdown("""
    <style>
        .login-container {
            text-align: center;
            padding: 2rem;
        }
        .login-header {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 1rem;
        }
        .login-sub {
            color: #555;
            margin-bottom: 2rem;
        }
    </style>
    <div class="login-container">
        <div class="login-header">🔐 ResumeReadyPro Admin Login</div>
        <div class="login-sub">Please log in to access resume tools and analytics dashboard.</div>
    </div>
""", unsafe_allow_html=True)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f"Welcome {name}")

    # Navigation
    page = st.sidebar.radio("Go to", ["Generate Summary", "Upload Resume", "Admin Dashboard", "About"])

    st.title("📄 ResumeReadyPro: AI Resume Enhancer")
    st.markdown("---")

    if page == "Generate Summary":
        st.header("✍️ Generate a Resume Summary")
        full_name = st.text_input("Your Full Name")
        job_title = st.text_input("Job Title / Career Goal")
        experience = st.text_area("Work Experience Summary")
        skills = st.text_area("Skills / Tools / Technologies")

        if st.button("Generate Summary"):
            if full_name and job_title and experience and skills:
                with st.spinner("Generating your summary..."):
                    try:
                        summary_response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "user", "content": f"Write a professional resume summary for:\nName: {full_name}\nJob Title: {job_title}\nExperience: {experience}\nSkills: {skills}"}
                            ]
                        )
                        summary_text = summary_response.choices[0].message.content.strip()
                        st.success("✅ Summary Generated!")
                        st.markdown("### Preview")
                        st.info(summary_text)

                        txt_bytes = BytesIO(summary_text.encode("utf-8"))
                        st.download_button("⬇️ Download as TXT", data=txt_bytes, file_name="resume_summary.txt", mime="text/plain")

                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        for line in summary_text.split("\n"):
                            pdf.multi_cell(0, 10, line)
                        pdf_output = BytesIO()
                        pdf.output(pdf_output)
                        pdf_output.seek(0)
                        st.download_button("⬇️ Download as PDF", data=pdf_output, file_name="resume_summary.pdf", mime="application/pdf")

                    except Exception as e:
                        st.error(f"Failed to generate summary: {e}")
            else:
                st.warning("Please fill in all fields to generate your summary.")

    elif page == "Upload Resume":
        st.header("📤 Upload Resume")
        uploaded_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])

        if uploaded_file is not None:
            reader = PdfReader(uploaded_file)
            resume_text = ""
            for page in reader.pages:
                resume_text += page.extract_text() or ""

            st.markdown("### Extracted Resume Text")
            st.text_area("Resume Content", resume_text, height=200)

            st.markdown("### Customize Your Questions")
            question_type = st.selectbox("Question Type", ["Behavioral", "Technical", "Situational"])
            question_count = st.slider("Number of Questions", 1, 10, 5)

            if st.button("Generate Interview Questions"):
                with st.spinner("Generating questions..."):
                    try:
                        question_prompt = f"Generate {question_count} {question_type.lower()} interview questions based on the following resume:\n{resume_text}"
                        question_response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user", "content": question_prompt}]
                        )
                        questions = question_response.choices[0].message.content.strip()
                        st.success("✅ Questions Generated!")
                        st.markdown("### 🤖 AI-Generated Interview Questions")
                        st.write(questions)
                    except Exception as e:
                        st.error(f"Error: {e}")

            st.markdown("---")
            st.markdown("### 📊 Resume Insights")
            try:
                insights_prompt = f"Extract top 10 skills, certifications, job titles, and industries from this resume:\n{resume_text}"
                insights_response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": insights_prompt}]
                )
                insights_text = insights_response.choices[0].message.content.strip()
                st.info(insights_text)

                st.download_button("⬇️ Export Insights as JSON", data=json.dumps(insights_text), file_name="resume_insights.json")
                st.download_button("⬇️ Export Insights as CSV", data=insights_text, file_name="resume_insights.csv")

            except Exception as e:
                st.error(f"Insights Error: {e}")

    elif page == "Admin Dashboard":
        st.header("📊 Admin Dashboard")
        st.markdown("### Usage Analytics")
        usage_data = {
            "Metric": ["Summaries Generated", "Resumes Uploaded", "Questions Generated"],
            "Count": [42, 28, 35]
        }
        df_usage = pd.DataFrame(usage_data)
        st.dataframe(df_usage)

        st.bar_chart(df_usage.set_index("Metric"))

    elif page == "About":
        st.header("ℹ️ About ResumeReadyPro")
        st.markdown("""
        ResumeReadyPro is an AI-powered tool designed to help professionals generate strong resume summaries and prepare for interviews with tailored questions — all from their existing resume content.

        Built using Streamlit, OpenAI, and PDF parsing tools.
        """)

elif authentication_status is False:
    st.error("Username or password is incorrect")
elif authentication_status is None:
    st.warning("Please enter your username and password")
