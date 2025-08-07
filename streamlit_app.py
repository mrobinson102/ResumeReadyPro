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
import matplotlibimport streamlit as st
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
        .block-container { padding-top: 2rem; }
        .sidebar .sidebar-content { background-color: #eef2f3; }
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
        st.subheader("✍️ Generate a Resume Summary")
        full_name = st.text_input("Your Full Name")
        career_goal = st.text_input("Job Title / Career Goal")
        work_experience = st.text_area("Work Experience Summary")
        skills = st.text_area("Skills / Tools / Technologies")

        if st.button("Generate Summary"):
            prompt = f"""Generate a professional resume summary for {full_name}, who is seeking a {career_goal} role. Experience: {work_experience}. Skills: {skills}"""
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}]
            )
            summary = response.choices[0].message.content
            st.success("Generated Summary:")
            st.write(summary)
            user_data[username]["summaries"] += 1
            save_users(user_data)

    elif page == "Upload Resume":
        st.subheader("📤 Upload Resume")
        uploaded_file = st.file_uploader("Choose a PDF resume", type="pdf")
        if uploaded_file:
            reader = PdfReader(uploaded_file)
            raw_text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
            st.text_area("Extracted Resume Text", raw_text, height=250)

            st.subheader("Customize Your Questions")
            q_type = st.selectbox("Question Type", ["Behavioral", "Technical", "Situational"])
            num_questions = st.slider("Number of Questions", 1, 10, 5)

            if st.button("Generate Interview Questions"):
                prompt = f"Generate {num_questions} {q_type} interview questions based on this resume: {raw_text}"
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}]
                )
                questions = response.choices[0].message.content
                st.success("Generated Questions:")
                st.write(questions)
                user_data[username]["questions"] += 1
                user_data[username]["resumes"] += 1
                save_users(user_data)

                # Resume Insights
                st.subheader("📌 Resume Insights")
                try:
                    prompt = f"Analyze this resume text and give detailed insights on how it could be improved:\n{raw_text}"
                    response = client.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    insights = response.choices[0].message.content
                    st.text_area("Resume Insights", insights, height=300)
                except Exception as e:
                    st.error(f"Insights Error: {e}")

    elif page == "Admin Dashboard":
        st.subheader("📊 Admin Dashboard")
        df = pd.DataFrame.from_dict(user_data, orient='index')
        st.dataframe(df)

        export_format = st.selectbox("Export format", ["CSV", "JSON"])
        if st.button("Download Export"):
            if export_format == "CSV":
                csv = df.to_csv().encode('utf-8')
                st.download_button("Download CSV", csv, "user_data.csv")
            else:
                json_str = json.dumps(user_data, indent=4)
                st.download_button("Download JSON", json_str, "user_data.json")

        st.subheader("📈 ResumeReadyPro Usage Metrics")
        metrics = ["summaries", "resumes", "questions"]
        counts = [sum(user[m] for user in user_data.values()) for m in metrics]
        plt.figure(figsize=(6,4))
        plt.bar(metrics, counts, color="#74b9ff")
        plt.title("ResumeReadyPro Usage Metrics")
        st.pyplot(plt)

    elif page == "Register User":
        st.subheader("👤 Register New User")
        new_user = st.text_input("Username")
        new_name = st.text_input("Full Name")
        new_pass = st.text_input("Password", type="password")
        if st.button("Register"):
            if new_user and new_pass:
                user_data[new_user] = {"name": new_name, "password": new_pass, "summaries": 0, "resumes": 0, "questions": 0}
                save_users(user_data)
                st.success("User registered!")

    elif page == "About":
        st.subheader("ℹ️ About ResumeReadyPro")
        st.markdown("""
        ResumeReadyPro is an AI-powered app designed to help users:
        - Generate personalized resume summaries
        - Analyze and improve resume content
        - Practice with AI-generated interview questions
        - View usage analytics and download reports
        """)

elif authentication_status is False:
    st.error("Username or password is incorrect")
elif authentication_status is None:
    st.warning("Please enter your username and password")

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
