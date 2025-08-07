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

    # rest of the app continues as previously defined...

elif authentication_status is False:
    st.error("Username or password is incorrect")
elif authentication_status is None:
    st.warning("Please enter your username and password")
