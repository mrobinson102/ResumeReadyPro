import streamlit as st
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import openai

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="ResumeReadyPro", layout="wide")
st.title("📄 ResumeReadyPro: AI Resume Enhancer")

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Generate Summary", "Upload Resume", "About"])

# Function to generate professional summary
def generate_summary(user_input):
    prompt = f"""
    You are a professional resume writer. Generate a concise, impactful professional summary based on the following information:

    {user_input}

    Summary:
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
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

# Pages
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

            st.download_button(
                label="📥 Download Summary as .txt",
                data=summary,
                file_name="resume_summary.txt",
                mime="text/plain"
            )
        else:
            st.error("Please fill out at least Name, Role, and Experience fields.")

elif page == "Upload Resume":
    st.subheader("📤 Upload Your Resume (PDF)")
    uploaded_file = st.file_uploader("Choose your resume PDF", type="pdf")

    if uploaded_file:
        resume_text = extract_text_from_pdf(uploaded_file)
        st.text_area("Extracted Resume Text", resume_text, height=300)

        if st.button("Generate Interview Questions"):
            prompt = f"""
            Review the following resume content and generate 5 targeted interview questions that assess readiness and fit for technical roles:

            {resume_text}

            Questions:
            """
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
                max_tokens=300
            )
            questions = response.choices[0].message.content.strip()
            st.success("Generated Interview Questions:")
            st.write(questions)

elif page == "About":
    st.subheader("About ResumeReadyPro")
    st.markdown("""
    **ResumeReadyPro** is an AI-powered resume enhancement tool designed to help you:

    - Write professional summaries based on your experience
    - Extract resume content from PDFs
    - Generate interview questions for practice

    Built with ❤️ using Streamlit and OpenAI.
    """)
