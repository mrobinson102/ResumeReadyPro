# streamlit_app.py
# ResumeReadyPro - Hybrid (Offline + GPT-ready)
# ------------------------------------------------
# Version: 1.0.0
# Last Updated: 2025-08-08
#
# Features:
# - Local auth (login/register/change password) with JSON storage
# - Onboarding wizard for first-time users
# - Generate Summary (Offline mock or GPT when enabled)
# - Upload Resume -> extract text + generate interview questions (Offline/GPT)
# - Prompt Lab (templates + tone controls)
# - Job Fit & Salary Alignment Analyzer (weighted: required vs nice-to-have, seniority, years)
# - Admin Dashboard with metrics + JSON/CSV export
# - Export to TXT/PDF/DOCX
#
# Toggle GPT on by setting USE_GPT=True and providing OPENAI_API_KEY in your env.

import streamlit as st
import openai
import os
from io import BytesIO
from fpdf import FPDF
from PyPDF2 import PdfReader
import pandas as pd
import json
import streamlit_authenticator as stauth
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from datetime import datetime
from modules.utils import load_users, save_users, hash_password
from modules.ui import apply_custom_styles, show_about, show_onboarding
from modules.features import generate_summary, upload_resume, prompt_lab, job_fit_analysis
from modules.admin import admin_dashboard, register_user, change_password

# Load environment variables
load_dotenv()
USE_GPT = os.getenv("USE_GPT", "false").lower() == "true"
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load and hash user credentials
USERS_DB = "user_data.json"
user_data = load_users(USERS_DB)
user_credentials = {'usernames': {}}
for uname, uinfo in user_data.items():
    if "password" in uinfo:
        user_credentials['usernames'][uname] = {
            'name': uinfo.get('name', uname),
            'password': hash_password(uinfo['password'])
        }

# Add admin if not present
if "admin" not in user_credentials["usernames"]:
    user_credentials["usernames"]["admin"] = {
        "name": "Admin User",
        "password": hash_password("adminpass")
    }

# Authenticator setup
authenticator = stauth.Authenticate(
    user_credentials, 'resume_app', 'abcdef', cookie_expiry_days=30
)

# App config and styling
st.set_page_config("ResumeReadyPro", "📄", layout="wide")
apply_custom_styles()

# Login
name, auth_status, username = authenticator.login("Login", "main")

if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.image("https://i.imgur.com/m0E0FLO.png", width=150)
    st.sidebar.write(f"👋 Welcome, {username}")

    page = st.sidebar.radio("Navigate", [
        "🧠 Generate Summary", "📄 Upload Resume", "🧪 Prompt Lab",
        "🧮 Job Fit & Salary", "🔐 Change Password",
        "📊 Admin Dashboard", "➕ Register User", "ℹ️ About"
    ])

    if username not in user_data:
        user_data[username] = {"summaries": 0, "resumes": 0, "questions": 0}
        save_users(user_data, USERS_DB)
        show_onboarding()

    if page == "🧠 Generate Summary":
        generate_summary(username, user_data, save_users, USERS_DB, USE_GPT)
    elif page == "📄 Upload Resume":
        upload_resume(username, user_data, save_users, USERS_DB, USE_GPT)
    elif page == "🧪 Prompt Lab":
        prompt_lab(username, user_data, save_users, USERS_DB, USE_GPT)
    elif page == "🧮 Job Fit & Salary":
        job_fit_analysis(username, user_data, save_users, USERS_DB, USE_GPT)
    elif page == "🔐 Change Password":
        change_password(username, user_data, save_users, USERS_DB)
    elif page == "📊 Admin Dashboard":
        admin_dashboard(user_data)
    elif page == "➕ Register User":
        register_user(user_data, save_users, USERS_DB)
    elif page == "ℹ️ About":
        show_about()
elif auth_status is False:
    st.error("Incorrect username or password")
elif auth_status is None:
    st.warning("Please enter your login credentials")
