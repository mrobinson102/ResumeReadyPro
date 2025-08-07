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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime

# Load .env keys
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

USERS_DB = "user_data.json"
if not os.path.exists(USERS_DB):
    with open(USERS_DB, "w") as f:
        json.dump({}, f)

def load_users():
    with open(USERS_DB, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_DB, "w") as f:
        json.dump(data, f, indent=4)

user_data = load_users()
user_credentials = {'usernames': {}}
for uname, uinfo in user_data.items():
    if "password" in uinfo:
        user_credentials['usernames'][uname] = {
            'name': uinfo.get('name', uname),
            'password': stauth.Hasher([uinfo['password']]).generate()[0]
        }

if "admin" not in user_credentials['usernames']:
    user_credentials['usernames']["admin"] = {
        "name": "Admin",
        "password": stauth.Hasher(["adminpass"]).generate()[0]
    }

authenticator = stauth.Authenticate(user_credentials, 'resume_app', 'abcdef', cookie_expiry_days=30)
st.set_page_config("ResumeReadyPro", "📄", layout="wide")

st.markdown("""
<style>
.sidebar .sidebar-content { background-color: #eef2f3; }
.stButton > button {
    color: white;
    background: linear-gradient(to right, #00b894, #0984e3);
    font-weight: bold; border-radius: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

name, auth_status, username = authenticator.login("Login", "main")

if auth_status:
    authenticator.logout("Logout", "sidebar")
    st.sidebar.image("https://i.imgur.com/m0E0FLO.png", width=150)
    st.sidebar.markdown("### 👤 Welcome: **{}**".format(username))
    st.sidebar.markdown("---")
    st.sidebar.markdown("ℹ️ This app helps you generate resume content and interview questions with AI.")

    user_data.setdefault(username, {"summaries": 0, "resumes": 0, "questions": 0})

    page = st.sidebar.radio("Navigation", [
        "Generate Summary", "Upload Resume", "Admin Dashboard", "Register User", "About"
    ])

    if page == "Generate Summary":
        st.subheader("✍️ Resume Summary Generator")
        full_name = st.text_input("Your Full Name")
        career_goal = st.text_input("Career Objective")
        experience = st.text_area("Work Experience")
        skills = st.text_area("Skills / Technologies")

        if st.button("Generate"):
            prompt = f"Generate a resume summary for {full_name} targeting {career_goal}. Experience: {experience}. Skills: {skills}."
            st.text("⚠️ GPT disabled for now. This would call OpenAI API.")

            user_data[username]["summaries"] += 1
            save_users(user_data)

    elif page == "Upload Resume":
        st.subheader("📤 Upload Resume to Generate Questions")
        uploaded = st.file_uploader("Upload Resume (PDF)", type="pdf")
        if uploaded:
            text = "n/".join([p.extract_text() for p in PdfReader(uploaded).pages])
            st.text_area("Resume Content", text, height=200)
            st.text("⚠️ GPT generation skipped (API calls disabled).")
            user_data[username]["resumes"] += 1
            user_data[username]["questions"] += 5
            save_users(user_data)

    elif page == "Admin Dashboard":
        st.subheader("📊 Admin Dashboard")
        df = pd.DataFrame.from_dict(user_data, orient="index")
        st.dataframe(df)

        fig, ax = plt.subplots()
        df[["summaries", "resumes", "questions"]].sum().plot(kind="bar", ax=ax)
        ax.set_title("Usage Stats")
        st.pyplot(fig)

        export_type = st.selectbox("Export Format", ["CSV", "JSON"])
        if st.button("Download Export"):
            if export_type == "CSV":
                st.download_button("Download CSV", df.to_csv().encode("utf-8"), "user_data.csv")
            else:
                st.download_button("Download JSON", json.dumps(user_data), "user_data.json")

    elif page == "Register User":
        st.subheader("Register New User")
        new_user = st.text_input("Username")
        new_name = st.text_input("Full Name")
        new_pass = st.text_input("Password", type="password")
        if st.button("Register"):
            user_data[new_user] = {"name": new_name, "password": new_pass, "summaries": 0, "resumes": 0, "questions": 0}
            save_users(user_data)
            st.success("User created!")

    elif page == "About":
        st.markdown("### ℹ️ About ResumeReadyPro")
        st.info("This tool helps generate AI-enhanced resume summaries and interview prep. Built in Streamlit.")

elif auth_status is False:
    st.error("Invalid username or password")
    st.caption("🔒 Forgot your password or username? Contact support@example.com")
elif auth_status is None:
    st.warning("Enter your credentials to continue")
