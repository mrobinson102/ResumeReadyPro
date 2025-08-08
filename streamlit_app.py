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
# ---- helpers: safe text extraction ----
def _read_txt(file):
    try:
        return file.read().decode("utf-8", errors="ignore")
    except Exception:
        try:
            file.seek(0)
            return file.read().decode("latin-1", errors="ignore")
        except Exception:
            return ""

def extract_text_from_upload(uploaded_file):
    """Return plain text from pdf/docx/txt; empty string if unsupported/failed."""
    if not uploaded_file:
        return ""
    name = (uploaded_file.name or "").lower()
    try:
        if name.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            return "\n".join([(p.extract_text() or "") for p in reader.pages])
        elif name.endswith(".docx"):
            doc = Document(uploaded_file)
            return "\n".join([p.text for p in doc.paragraphs])
        elif name.endswith(".txt"):
            return _read_txt(uploaded_file)
        else:
            # best effort: try text
            return _read_txt(uploaded_file)
    except Exception:
        return ""

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
    
        jd_col, resume_col = st.columns(2)
        with jd_col:
            jd_file = st.file_uploader("Upload Job Description (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="jd_up")
            jd_text = st.text_area("…or paste JD text", value="", height=220, key="jd_text")
            if jd_file and not jd_text.strip():
                jd_text = extract_text_from_upload(jd_file)
                st.session_state["jd_text"] = jd_text
                st.experimental_rerun()
    
        with resume_col:
            rs_file = st.file_uploader("Upload Your Resume (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="rs_up")
            resume_text = st.text_area("…or paste your resume text", value="", height=220, key="rs_text")
            if rs_file and not resume_text.strip():
                resume_text = extract_text_from_upload(rs_file)
                st.session_state["rs_text"] = resume_text
                st.experimental_rerun()
    
        st.caption("Tip: uploading a file auto-fills the text box; you can still edit it before analysis.")
    
        if st.button("Analyze Fit"):
            if not (jd_text or st.session_state.get("jd_text")) or not (resume_text or st.session_state.get("rs_text")):
                st.warning("Please provide both a JD and a resume (upload or paste).")
            else:
                job_desc = jd_text or st.session_state.get("jd_text", "")
                resume_input = resume_text or st.session_state.get("rs_text", "")
                prompt = (
                    "Analyze how well this resume fits the job description. Identify strengths, clear gaps, "
                    "and 3–5 concrete action steps the candidate should take next. Return a short, scannable output.\n\n"
                    f"Job Description:\n{job_desc}\n\nResume:\n{resume_input}"
                )
                try:
                    response = openai.chat.completions.create(
                        model="gpt-4",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    analysis = response.choices[0].message.content
                    st.text_area("Fit Analysis", analysis, height=380)
                except Exception as e:
                    # Friendly errors until billing is on
                    st.error("Couldn’t call OpenAI (likely quota/billing). Once billing is enabled, try again.")
                    st.caption(f"(Debug: {e})")
    
    
        # --- PAGE: Prompt Lab ---
        elif page == "Prompt Lab":
            from prompt_lab import prompt_lab_ui
            prompt_lab_ui()
        

    # --- PAGE: Admin Dashboard ---
elif page == "Admin Dashboard":
    st.subheader("📊 Admin Dashboard")

    # Keep only real user rows (skip any meta/system dicts)
    real_users = {
        u: d for u, d in user_data.items()
        if isinstance(d, dict) and ("summaries" in d or "resumes" in d or "questions" in d or "gap_analyses" in d)
    }

    # Build DataFrame
    df = pd.DataFrame.from_dict(real_users, orient="index")

    # Ensure the columns exist and are numeric; show 0 instead of NaN/None
    for col in ["summaries", "resumes", "questions", "gap_analyses"]:
        if col not in df.columns:
            df[col] = 0
    df[["summaries", "resumes", "questions", "gap_analyses"]] = (
        df[["summaries", "resumes", "questions", "gap_analyses"]]
        .apply(pd.to_numeric, errors="coerce")
        .fillna(0)
        .astype(int)
    )

    c1, c2 = st.columns([1.4, 1])  # wider table, smaller chart

    with c1:
        st.dataframe(
            df[["summaries", "resumes", "questions", "gap_analyses"]],
            use_container_width=True
        )

    with c2:
        try:
            totals = df[["summaries", "resumes", "questions", "gap_analyses"]].sum(numeric_only=True)
            fig, ax = plt.subplots(figsize=(4.8, 3.2))
            totals.plot(kind="bar", ax=ax, color="#2E86C1")
            ax.set_title("Usage Summary", fontsize=12)
            ax.tick_params(axis="x", labelrotation=0)
            ax.bar_label(ax.containers[0], label_type="edge", fontsize=9)
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
            if not new_user or not new_pass:
                st.error("Username and password are required.")
            elif user_exists(new_user):
                st.error("User already exists.")
            else:
                user_data[new_user] = {
                    "name": new_name or new_user,
                    "password": new_pass,
                    "summaries": 0, "resumes": 0, "questions": 0,
                    "meta": {"reset_token": "", "reset_issued_at": ""}
                }
                save_users(user_data)
                st.success("User registered.")

     # ---- Password & reset helpers ----
    import secrets
    from datetime import datetime
    
    def user_exists(username: str) -> bool:
        return isinstance(user_data, dict) and username in user_data
    
    def create_reset_token(username: str):
        """Create and store a one-time reset token for a user."""
        if not user_exists(username):
            return False, "No such user."
        token = secrets.token_urlsafe(12)
        user_data[username].setdefault("meta", {})
        user_data[username]["meta"]["reset_token"] = token
        user_data[username]["meta"]["reset_issued_at"] = datetime.utcnow().isoformat() + "Z"
        save_users(user_data)
        return True, token
    
    def reset_password_with_token(username: str, token: str, new_password: str):
        """Verify token and set a new password. Clears token after use."""
        if not user_exists(username):
            return False, "No such user."
        meta = user_data[username].get("meta", {})
        stored = meta.get("reset_token", "")
        if not stored:
            return False, "No reset token exists for this user."
        if token.strip() != stored:
            return False, "Invalid token."
    
        # Set new password (we store plaintext in JSON; stauth re-hashes on load)
        user_data[username]["password"] = new_password
        # Clear token
        user_data[username]["meta"]["reset_token"] = ""
        save_users(user_data)
        return True, "Password reset successful."
    
    def change_password_direct(username: str, old_password: str, new_password: str):
        """Validate old password and update to new password."""
        if not user_exists(username):
            return False, "No such user."
        current = user_data[username].get("password", "")
        if old_password != current:
            return False, "Old password is incorrect."
        user_data[username]["password"] = new_password
        save_users(user_data)
        return True, "Password changed."

    # --- PAGE: Change Password ---
elif page == "Change Password":
        st.subheader("🔑 Change Password")
        if not auth_status:
            st.info("Please log in to change your password.")
        else:
            old_pw = st.text_input("Old Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm = st.text_input("Confirm New Password", type="password")
    
            if st.button("Update Password"):
                if not new_pw or new_pw != confirm:
                    st.error("New passwords do not match.")
                else:
                    ok, msg = change_password_direct(username, old_pw, new_pw)
                    st.success(msg) if ok else st.error(msg)    


   # --- PAGE: Reset Password ---
elif page == "Reset Password":
    st.subheader("🔒 Password Reset (Token-based)")
    tabs = st.tabs(["Request Token", "Reset With Token"])

    # Tab 1: Request token
    with tabs[0]:
        st.write("Enter the username to generate a one-time reset token. In this offline build, the token will be shown on-screen.")
        uname = st.text_input("Username for reset", key="rt_user")
        if st.button("Create Reset Token"):
            if not uname:
                st.error("Please enter a username.")
            else:
                ok, token_or_msg = create_reset_token(uname)
                if ok:
                    st.success("Reset token created. Copy it now (no email yet in offline mode):")
                    st.code(token_or_msg, language=None)
                else:
                    st.error(token_or_msg)

    # Tab 2: Reset with token
    with tabs[1]:
        uname2 = st.text_input("Username", key="rt_user2")
        token = st.text_input("Reset Token", key="rt_token")
        new_pw2 = st.text_input("New Password", type="password", key="rt_pw")
        confirm2 = st.text_input("Confirm New Password", type="password", key="rt_pw2")

        if st.button("Reset Password"):
            if not (uname2 and token and new_pw2):
                st.error("Please fill in all fields.")
            elif new_pw2 != confirm2:
                st.error("New passwords do not match.")
            else:
                ok, msg = reset_password_with_token(uname2, token, new_pw2)
                st.success(msg) if ok else st.error(msg)

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
