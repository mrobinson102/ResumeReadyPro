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
openai.api_key = os.getenv("OPENAI_API_KEY")

# Prompt templates
prompt_templates = {
    "Internship Section": """
Generate a résumé section titled 'Internship & Co-op Experience'. Use the following input to format each role clearly with company name, role, dates, and bullet points for responsibilities and accomplishments. Highlight technologies used and any metrics if mentioned.

Input:
{user_input}

Format output in markdown or plain text suitable for a professional resume.
""",
    "Categorized Projects": """
You are helping a user build a résumé. Categorize the following projects into three sections:

1. Internship Projects
2. Academic Coursework Projects
3. Personal Side Projects

For each project, include:
- Project title
- Role or responsibility
- Technologies used (languages, frameworks)
- Key accomplishment or what was built

Input:
{user_input}

Return output in resume bullet style under each category.
""",
    "GitHub Repo Summary": """
For each of the following GitHub repositories, generate a résumé-ready bullet point that describes:
- What the project does
- Technologies used
- A notable feature or result
- Keep each bullet under 30 words

GitHub Repo List:
{user_input}

Output each bullet with a hyperlink to the repo.
""",
    "Resume Only": """
You are an AI résumé assistant. The user does not want a cover letter. Only generate a professional résumé using the following inputs:
- Experience
- Skills
- Education
- Projects

Format the résumé cleanly with appropriate headings and bullet points, omitting any cover letter language.
""",
    "Tech Summary for Big Tech": """
Write a compelling 2–3 sentence professional summary for a résumé targeting top tech companies (e.g., Microsoft, Amazon). The tone should be confident, clear, and metrics-driven.

Use the input below. Highlight relevant languages, platforms, and impact.

Input:
{user_input}
"""
}

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

# Load Users
user_data = load_users()

# Create credentials for streamlit_authenticator
user_credentials = {'usernames': {}}
for uname, uinfo in user_data.items():
    if "password" in uinfo:
        user_credentials['usernames'][uname] = {
            'name': uinfo.get('name', uname),
            'password': stauth.Hasher([uinfo['password']]).generate()[0]
        }

# Add admin user
admin_user = 'admin'
if admin_user not in user_credentials['usernames']:
    user_credentials['usernames'][admin_user] = {
        'name': 'Admin User',
        'password': stauth.Hasher(['adminpass']).generate()[0]
    }

# Authentication Setup
authenticator = stauth.Authenticate(
    user_credentials,
    'resume_app', 'abcdef', cookie_expiry_days=30
)

# App Configuration
st.set_page_config(page_title="ResumeReadyPro", page_icon="📄", layout="wide")

# Styling
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
    </style>
""", unsafe_allow_html=True)

# Login
name, auth_status, username = authenticator.login("Login", "main")

if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.image("https://i.imgur.com/m0E0FLO.png", width=150)
    st.sidebar.markdown(f"<h3 style='color:#2d3436;'>Welcome {username}</h3>", unsafe_allow_html=True)

    page = st.sidebar.radio("Go to", [
        "Generate Summary", "Upload Resume", "Admin Dashboard", "Register User", "About"
    ])

    st.title("📄 ResumeReadyPro: AI Resume Enhancer")
    st.markdown("---")

    if username not in user_data:
        user_data[username] = {"summaries": 0, "resumes": 0, "questions": 0}

    if page == "Generate Summary":
        st.subheader("✍️ Resume Summary or Advanced Generator")

        advanced = st.checkbox("Use Advanced Prompt Templates")
        if advanced:
            selected_prompt = st.selectbox("Choose Template", list(prompt_templates.keys()))
            user_input = st.text_area("Enter Input for Template", height=200)

            if st.button("Generate Using Template"):
                filled_prompt = prompt_templates[selected_prompt].format(user_input=user_input)
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": filled_prompt}],
                    temperature=0.7
                )
                st.text_area("Generated Output", response.choices[0].message.content, height=250)
                user_data[username]["summaries"] += 1
                save_users(user_data)
        else:
            full_name = st.text_input("Your Full Name")
            career_goal = st.text_input("Job Title / Career Goal")
            experience = st.text_area("Work Experience Summary")
            skills = st.text_area("Skills / Tools / Technologies")

            if st.button("Generate Summary"):
                prompt = f"Generate a professional resume summary for {full_name} targeting the role of {career_goal}. "                          f"Include experience: {experience}. Skills: {skills}."
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}]
                )
                result = response.choices[0].message.content
                st.success("Summary Generated!")
                st.text_area("Generated Summary", result, height=200)
                user_data[username]["summaries"] += 1
                save_users(user_data)

# The remaining routes (Upload Resume, Admin Dashboard, Register User, About) would follow...
          
