import streamlit as st
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import openai
import time
from fpdf import FPDF
from datetime import datetime
import sqlite3
from PIL import Image, UnidentifiedImageError
import io
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Load authentication config
auth_config = {
    'credentials': {
        'usernames': {
            'admin': {
                'email': 'admin@resumereadypro.com',
                'name': 'Admin User',
                'password': stauth.Hasher(['adminpass']).generate()[0]
            },
            'demo': {
                'email': 'demo@resumereadypro.com',
                'name': 'Demo User',
                'password': stauth.Hasher(['demopass']).generate()[0]
            }
        }
    },
    'cookie': {
        'name': 'resumereadypro_cookie',
        'key': 'some_signature_key',
        'expiry_days': 1
    },
    'preauthorized': {
        'emails': ["admin@resumereadypro.com"]
    }
}

# Authenticate users
authenticator = stauth.Authenticate(
    auth_config['credentials'],
    auth_config['cookie']['name'],
    auth_config['cookie']['key'],
    auth_config['cookie']['expiry_days']
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status is False:
    st.error("Incorrect username or password.")
elif authentication_status is None:
    st.warning("Please enter your username and password.")
elif authentication_status:

    # Initialize DB connection
    conn = sqlite3.connect("usage_logs.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS usage (
        timestamp TEXT,
        name TEXT,
        action TEXT
    )''')
    conn.commit()

    # Function to log usage
    def log_usage(name, action):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO usage (timestamp, name, action) VALUES (?, ?, ?)", (timestamp, name, action))
        conn.commit()

    # Set up Streamlit
    st.set_page_config(page_title="ResumeReadyPro", layout="wide")

    # Apply custom CSS styles with branding, font, and enhancements
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

            .stApp {
                background-color: #f2f6fc;
                font-family: 'Inter', sans-serif;
            }
            .css-1d391kg, .css-1v0mbdj, .css-18e3th9 {
                background-color: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.05);
            }
            h1, h2, h3, h4, h5 {
                color: #002B5B;
                font-weight: 700;
            }
            .stButton>button {
                background-color: #002B5B;
                color: white;
                border-radius: 6px;
                padding: 0.5em 1.5em;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #004080;
            }
            .stTextArea>div>textarea {
                font-family: 'Courier New', Courier, monospace;
                font-size: 0.9em;
                line-height: 1.5;
                border-radius: 8px;
                padding: 10px;
            }
            .stSelectbox>div>div>div {
                font-size: 0.9em;
            }
            .css-1aumxhk {
                font-weight: 600;
            }
            .stSlider .css-1aumxhk {
                color: #002B5B;
            }
            .stSpinner>div>div {
                color: #002B5B !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("📄 ResumeReadyPro: AI Resume Enhancer")

    # Sidebar Navigation
    try:
        logo_path = "assets/logo.png"
        image = Image.open(logo_path)
        st.sidebar.image(image, width=150)
    except (FileNotFoundError, UnidentifiedImageError):
        st.sidebar.markdown("**ResumeReadyPro**")

    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Generate Summary", "Upload Resume", "Admin Dashboard", "About"])

    # Function to generate professional summary
    def generate_summary(user_input):
        prompt = f"""
        You are a professional resume writer. Generate a concise, impactful professional summary based on the following information:

        {user_input}

        Summary:
        """
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content.strip()

    # Function to extract text from PDF
    def extract_text_from_pdf(uploaded_file):
        pdf = PdfReader(uploaded_file)
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text

    # Function to generate interview questions
    def generate_interview_questions(resume_text, category, num_questions):
        prompt = f"""
        Review the following resume and generate {num_questions} {category.lower()} interview questions:

        Resume:
        {resume_text}

        Questions:
        """
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=300
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"⚠️ Error: {str(e)}"

    # Export to PDF
    def export_to_pdf(text, filename="resume_summary.pdf"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "ResumeReadyPro - Professional Summary", ln=True, align="C")
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
        pdf.ln(10)
        for line in text.splitlines():
            pdf.multi_cell(0, 10, line)
        return pdf.output(dest="S").encode("latin-1")

    if page == "Generate Summary":
        st.subheader("✍️ Generate a Resume Summary")
        name = st.text_input("Your Full Name")
        role = st.text_input("Job Title / Career Goal")
        experience = st.text_area("Work Experience Summary")
        skills = st.text_area("Skills / Tools / Technologies")

        if st.button("Generate Summary"):
            if name and role and experience:
                user_input = f"Name: {name}\nRole: {role}\nExperience: {experience}\nSkills: {skills}"
                summary = generate_summary(user_input)
                st.success("Here’s your professional summary:")
                st.write(summary)
                log_usage(name, "Generated Summary")

                st.download_button(
                    label="📥 Download Summary as .txt",
                    data=summary,
                    file_name="resume_summary.txt",
                    mime="text/plain"
                )

                pdf_data = export_to_pdf(summary)
                st.download_button(
                    label="📄 Download Summary as PDF",
                    data=pdf_data,
                    file_name="resume_summary.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("Please fill out at least Name, Role, and Experience fields.")

    elif page == "Upload Resume":
        st.subheader("📤 Upload Your Resume (PDF)")
        uploaded_file = st.file_uploader("Choose your resume PDF", type="pdf")

        if uploaded_file:
            resume_text = extract_text_from_pdf(uploaded_file)
            st.text_area("Extracted Resume Text", resume_text, height=300)

            st.markdown("### Customize Your Questions")
            category = st.selectbox("Question Type", ["Behavioral", "Technical", "General"])
            num_questions = st.slider("Number of Questions", min_value=3, max_value=10, value=5)

            if st.button("Generate Interview Questions"):
                with st.spinner("Generating interview questions..."):
                    questions = generate_interview_questions(resume_text, category, num_questions)
                if questions.startswith("⚠️"):
                    st.warning(questions)
                else:
                    st.success("Generated Interview Questions:")
                    st.write(questions)
                log_usage("Resume Upload", "Generated Questions")

    elif page == "Admin Dashboard":
        st.subheader("📊 Admin Usage Dashboard")
        rows = c.execute("SELECT * FROM usage ORDER BY timestamp DESC LIMIT 100").fetchall()
        if rows:
            for row in rows:
                st.write(f"[{row[0]}] {row[1]} - {row[2]}")
        else:
            st.info("No usage data yet.")

    elif page == "About":
        st.subheader("About ResumeReadyPro")
        st.markdown("""
        **ResumeReadyPro** is an AI-powered resume enhancement tool designed to help you:

        - Write professional summaries based on your experience
        - Extract resume content from PDFs
        - Generate interview questions for practice
        - Export summaries as TXT or PDF
        - Track usage and view logs in Admin Dashboard
        - Enjoy polished layout, branding, and streamlined experience
        - Secure user authentication and admin-only access

        Built with ❤️ using Streamlit and OpenAI.
        """)
