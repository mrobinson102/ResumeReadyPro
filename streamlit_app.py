# streamlit_app.py

import streamlit as st
import openai
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import streamlit_authenticator as stauth
import json
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from fpdf import FPDF
from PIL import Image
from docx import Document
from prompt_lab import prompt_lab_ui

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Path for user data
USERS_DB = "user_data.json"
if not os.path.exists(USERS_DB):
    with open(USERS_DB, "w") as f:
        json.dump({}, f)

# Load/save user data
def load_users():
    with open(USERS_DB, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_DB, "w") as f:
        json.dump(data, f, indent=4)

user_data = load_users()

# Create credentials for authenticator
user_credentials = {'usernames': {}}
for uname, uinfo in user_data.items():
    if "password" in uinfo:
        user_credentials['usernames'][uname] = {
            'name': uinfo.get('name', uname),
            'password': stauth.Hasher([uinfo['password']]).generate()[0]
        }

if 'admin' not in user_credentials['usernames']:
    user_credentials['usernames']['admin'] = {
        'name': 'Admin',
        'password': stauth.Hasher(['adminpass']).generate()[0]
    }

# Setup authentication
authenticator = stauth.Authenticate(
    user_credentials, 'resume_ready', 'abcdef', cookie_expiry_days=30
)

# Streamlit config
st.set_page_config(page_title="ResumeReadyPro", page_icon="🧠", layout="wide")

# Sidebar login
name, auth_status, username = authenticator.login("Login", "main")

# If logged in:
if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.image("assets/ceo.jpg", width=150)
    st.sidebar.markdown(f"### Welcome, {username}")

    page = st.sidebar.radio("Navigate", [
        "Generate Summary", "Upload Resume", "Job Fit & Salary", "Prompt Lab",
        "Admin Dashboard", "Register User", "Change Password", "Reset Password", "About"
    ])

    if username not in user_data:
        user_data[username] = {"summaries": 0, "resumes": 0, "questions": 0}
        save_users(user_data)

    st.title("📄 ResumeReadyPro")

    # --- PAGE: Generate Summary ---
    if page == "Generate Summary":
        st.subheader("✍️ Resume Summary Generator")
        full_name = st.text_input("Your Full Name")
        career_goal = st.text_input("Career Goal / Job Title")
        experience = st.text_area("Brief Work Experience")
        skills = st.text_area("Skills / Technologies")

        if st.button("Generate"):
            prompt = f"Write a 3-sentence resume summary for {full_name}, targeting a role in {career_goal}. Use this experience: {experience}. Highlight these skills: {skills}."
            try:
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}]
                )
                summary = response.choices[0].message.content
                st.success("Generated Summary")
                st.text_area("Summary", summary, height=150)
                user_data[username]["summaries"] += 1
                save_users(user_data)
            except Exception as e:
                st.error(f"Error: {e}")

    # --- PAGE: Upload Resume ---
    elif page == "Upload Resume":
        st.subheader("📤 Upload Resume")
        uploaded = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
        if uploaded:
            text = "\n".join([p.extract_text() for p in PdfReader(uploaded).pages])
            st.text_area("Resume Text", text, height=250)
            qtype = st.selectbox("Question Type", ["Behavioral", "Technical", "Mixed"])
            qcount = st.slider("Number of Questions", 1, 10, 5)

            if st.button("Generate Interview Questions"):
                prompt = f"Create {qcount} {qtype} interview questions based on this resume:\n{text}"
                try:
                    response = openai.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    questions = response.choices[0].message.content
                    st.text_area("Generated Questions", questions, height=250)
                    user_data[username]["resumes"] += 1
                    user_data[username]["questions"] += qcount
                    save_users(user_data)
                except Exception as e:
                    st.error(f"Error: {e}")

    # --- PAGE: Job Fit & Salary Alignment ---
    elif page == "Job Fit & Salary":
        st.subheader("🎯 Job Description Analysis")
        job_desc = st.text_area("Paste Job Description")
        resume_input = st.text_area("Paste Your Resume Text")

        if st.button("Analyze Fit"):
            prompt = f"Analyze how well this resume fits the job description. Identify strengths, gaps, and suggest action steps.\n\nJob:\n{job_desc}\n\nResume:\n{resume_input}"
            try:
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}]
                )
                analysis = response.choices[0].message.content
                st.text_area("Fit Analysis", analysis, height=300)
            except Exception as e:
                st.error(f"Error: {e}")

    # --- PAGE: Prompt Lab ---
    elif page == "Prompt Lab":
        from prompt_lab import prompt_lab_ui
        prompt_lab_ui()
        

    # --- PAGE: Admin Dashboard ---
    elif page == "Admin Dashboard":
        st.subheader("📊 Admin Dashboard")
    
        c1, c2 = st.columns([1.4, 1])  # wider table, narrower chart
        with c1:
            df = pd.DataFrame.from_dict(user_data, orient="index")
            st.dataframe(df, use_container_width=True)
    
        with c2:
            try:
                bar_counts = df[["summaries", "resumes", "questions"]].sum()
                fig, ax = plt.subplots(figsize=(4.5, 3))
                bar_counts.plot(kind="bar", ax=ax, color="#2E86C1")
                ax.set_title("Usage Summary", fontsize=12)
                ax.tick_params(axis="x", labelrotation=0)
                ax.bar_label(ax.containers[0], label_type='edge', fontsize=9)
                fig.tight_layout()
                st.pyplot(fig)
            except Exception as e:
                st.info(f"Chart unavailable: {e}")


    # --- PAGE: Register User ---
    elif page == "Register User":
        st.subheader("Register New User")
        new_user = st.text_input("Username")
        new_name = st.text_input("Full Name")
        new_pass = st.text_input("Password", type="password")
        if st.button("Register"):
            user_data[new_user] = {
                "name": new_name, "password": new_pass, "summaries": 0, "resumes": 0, "questions": 0
            }
            save_users(user_data)
            st.success("User registered.")

    # --- PAGE: Change Password ---
    elif page == "Change Password":
        st.subheader("Change Password")
        st.warning("Not yet implemented.")

    # --- PAGE: Reset Password ---
    elif page == "Reset Password":
        st.subheader("Reset Password")
        st.warning("Not yet implemented.")

    # --- PAGE: About ---
    elif page == "About":
        st.subheader("About ResumeReadyPro")
        st.image("assets/ceo.jpg", width=200)
        st.markdown("""
        **ResumeReadyPro** is a professional résumé optimization and job readiness platform built for modern job seekers.

        - 🧠 Powered by GPT-4
        - 📄 Resume summarization and analysis
        - 🔍 Job fit scoring and interview prep
        - 🔐 User analytics and dashboard

        **Founder & CEO:** Michelle Robinson  
        **Contact:** support@resumereadypro.com
        """)

# Handle failed login
elif auth_status is False:
    st.error("Invalid credentials. Try again.")
elif auth_status is None:
    st.info("Enter username and password.")
