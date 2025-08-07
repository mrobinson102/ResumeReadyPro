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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

# Load environment variables
load_dotenv()
client = openai.OpenAI()

# Paths
USERS_DB = "user_data.json"

# Initialize or load user data
if not os.path.exists(USERS_DB):
    with open(USERS_DB, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USERS_DB, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_DB, "w") as f:
        json.dump(data, f, indent=4)

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

# App Styling
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
        }
        .sidebar .sidebar-content {
            background-color: #eef2f3;
        }
        .stButton > button {
            color: white;
            background: linear-gradient(to right, #00b894, #0984e3);
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-weight: bold;
        }
        .stButton > button:hover {
            background: linear-gradient(to right, #6c5ce7, #00cec9);
        }
        .stTextInput > div > input,
        .stTextArea > div > textarea {
            border-radius: 0.5rem;
            border: 1px solid #dfe6e9;
        }
        .css-1aumxhk, .css-1kyxreq {
            font-family: 'Segoe UI', sans-serif;
        }
    </style>
""", unsafe_allow_html=True)

# Custom login UI
st.markdown("""
    <div class="login-container">
        <div class="login-header">🔐 <strong style='color:#2d3436;'>ResumeReadyPro Admin Login</strong></div>
        <div class="login-sub">Please log in to access resume tools and analytics dashboard.</div>
    </div>
""", unsafe_allow_html=True)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.image("https://i.imgur.com/m0E0FLO.png", width=150)
    st.sidebar.markdown(f"<h3 style='color:#2d3436;'>Welcome {username}</h3>", unsafe_allow_html=True)

    page = st.sidebar.radio("Go to", [
        "Generate Summary", "Upload Resume", "Admin Dashboard", "Register User", "About"
    ])
    st.title("📄 ResumeReadyPro: AI Resume Enhancer")
    st.markdown("---")

    user_data = load_users()
    user_data.setdefault(username, {"summaries": 0, "resumes": 0, "questions": 0})

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
                        summary_response = client.chat.completions.create(
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

                        user_data[username]["summaries"] += 1
                        save_users(user_data)
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
                        question_response = client.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[{"role": "user", "content": question_prompt}]
                        )
                        questions = question_response.choices[0].message.content.strip()
                        st.success("✅ Questions Generated!")
                        st.markdown("### 🤖 AI-Generated Interview Questions")
                        st.write(questions)

                        txt_bytes = BytesIO(questions.encode("utf-8"))
                        st.download_button("⬇️ Download Questions as TXT", data=txt_bytes, file_name="interview_questions.txt", mime="text/plain")

                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", size=12)
                        for line in questions.split("\n"):
                            pdf.multi_cell(0, 10, line)
                        pdf_output = BytesIO()
                        pdf.output(pdf_output)
                        pdf_output.seek(0)
                        st.download_button("⬇️ Download Questions as PDF", data=pdf_output, file_name="interview_questions.pdf", mime="application/pdf")

                        user_data[username]["questions"] += question_count
                        save_users(user_data)
                    except Exception as e:
                        st.error(f"Error: {e}")

            st.markdown("---")
            st.markdown("### 📊 Resume Insights")
            try:
                insights_prompt = f"Extract top 10 skills, certifications, job titles, and industries from this resume:\n{resume_text}"
                insights_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": insights_prompt}]
                )
                insights_text = insights_response.choices[0].message.content.strip()
                st.info(insights_text)

                st.download_button("⬇️ Export Insights as JSON", data=json.dumps(insights_text), file_name="resume_insights.json")
                st.download_button("⬇️ Export Insights as TXT", data=insights_text, file_name="resume_insights.txt")

                user_data[username]["resumes"] += 1
                save_users(user_data)
            except Exception as e:
                st.error(f"Insights Error: {e}")

    elif page == "Admin Dashboard":
        st.header("📊 Admin Dashboard")
        st.markdown("### Usage Analytics")

        usage_df = pd.DataFrame.from_dict(user_data, orient="index")
        usage_df = usage_df.fillna(0)
        usage_df["user"] = usage_df.index
        usage_df.reset_index(drop=True, inplace=True)

        st.dataframe(usage_df)

        summary_total = usage_df["summaries"].sum()
        resume_total = usage_df["resumes"].sum()
        question_total = usage_df["questions"].sum()

        metrics_df = pd.DataFrame({
            "Metric": ["Summaries Generated", "Resumes Uploaded", "Questions Generated"],
            "Count": [summary_total, resume_total, question_total]
        })

        fig, ax = plt.subplots()
        ax.bar(metrics_df['Metric'], metrics_df['Count'], color=['#00cec9', '#74b9ff', '#a29bfe'])
        ax.set_ylabel("Count")
        ax.set_title("ResumeReadyPro Usage Metrics")
        st.pyplot(fig)

        if st.button("Download User Stats CSV"):
            st.download_button("⬇️ Export CSV", data=usage_df.to_csv(index=False), file_name="user_stats.csv")

        st.markdown("### Admin Tools")
        selected_user = st.selectbox("Select user to delete or reset", list(user_data.keys()))
        if st.button("Delete User"):
            user_data.pop(selected_user, None)
            save_users(user_data)
            st.success(f"Deleted user {selected_user}")
        if st.button("Reset Stats"):
            user_data[selected_user] = {"summaries": 0, "resumes": 0, "questions": 0}
            save_users(user_data)
            st.success(f"Stats reset for {selected_user}")

    elif page == "Register User":
        st.header("👤 Register New User")
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Create User"):
            if new_username and new_password:
                users = load_users()
                if new_username in users:
                    st.error("Username already exists")
                else:
                    hashed_pw = stauth.Hasher([new_password]).generate()[0]
                    credentials['usernames'][new_username] = {
                        'name': new_username,
                        'password': hashed_pw
                    }
                    users[new_username] = {"summaries": 0, "resumes": 0, "questions": 0}
                    save_users(users)
                    st.success(f"User {new_username} registered successfully")
            else:
                st.warning("Please enter both username and password")

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
