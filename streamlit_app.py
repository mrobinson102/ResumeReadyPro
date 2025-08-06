import streamlit as st
import openai
import os
from io import BytesIO
from fpdf import FPDF
from PyPDF2 import PdfReader
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from dotenv import load_dotenv

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

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.set_page_config(page_title="ResumeReadyPro", page_icon="📄", layout="centered")
    authenticator.logout("Logout", "sidebar")
    st.sidebar.title(f"Welcome {name}")

    st.title("📄 ResumeReadyPro")
    st.subheader("Build standout resumes and generate interview questions with AI")
    st.markdown("---")

    uploaded_file = st.file_uploader("📤 Upload Your Resume (PDF only)", type=["pdf"])

    extracted_text = ""
    if uploaded_file is not None:
        reader = PdfReader(uploaded_file)
        for page in reader.pages:
            extracted_text += page.extract_text() or ""

    if extracted_text:
        st.markdown("### Extracted Resume Text")
        st.text_area("Resume Content", extracted_text, height=200)

        if st.button("🧠 Generate Interview Questions"):
            with st.spinner("Generating questions..."):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "user", "content": f"Generate 5 interview questions based on this resume:\n{extracted_text}"}
                        ]
                    )
                    questions = response.choices[0].message.content.strip()
                    st.success("Questions generated!")
                    st.markdown("### 🤖 AI-Generated Interview Questions")
                    st.write(questions)
                except Exception as e:
                    st.error(f"Error: {e}")

    st.markdown("---")
    st.markdown("### ✨ Create Resume from Summary")
    full_name = st.text_input("Full Name")
    email = st.text_input("Email")
    summary_input = st.text_area("Enter your achievements or experience")

    if st.button("✨ Generate Resume Summary"):
        if full_name and email and summary_input:
            with st.spinner("Generating summary..."):
                try:
                    summary_response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "user", "content": f"Write a 3-4 sentence resume summary for this content:\n{summary_input}"}
                        ]
                    )
                    generated_summary = summary_response.choices[0].message.content.strip()
                    st.session_state.generated_summary = generated_summary
                    st.success("Summary created!")
                    st.markdown("### 📝 Summary Preview")
                    st.info(generated_summary)
                except Exception as e:
                    st.error(f"Failed to generate summary: {e}")
        else:
            st.warning("Please complete all fields.")

    if "generated_summary" in st.session_state:
        summary_text = f"""{full_name}\n{email}\n\nProfessional Summary:\n{st.session_state.generated_summary}"""

        txt_bytes = BytesIO(summary_text.encode("utf-8"))
        st.download_button("⬇️ Download as TXT", data=txt_bytes, file_name="resume.txt", mime="text/plain")

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        for line in summary_text.split("\n"):
            pdf.multi_cell(0, 10, line)
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        st.download_button("⬇️ Download as PDF", data=pdf_output, file_name="resume.pdf", mime="application/pdf")

elif authentication_status is False:
    st.error("Username or password is incorrect")
elif authentication_status is None:
    st.warning("Please enter your username and password")
