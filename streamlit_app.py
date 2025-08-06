import streamlit as st
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
import openai

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="ResumeReadyPro", layout="wide")

# Apply custom CSS styles
st.markdown("""
    <style>
        .stApp {
            background-color: #f4f4f4;
            font-family: 'Segoe UI', sans-serif;
        }
        .css-1d391kg, .css-1v0mbdj, .css-18e3th9 {
            background-color: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
        }
        .st-bb, .st-c9, .st-c8, .st-b3 {
            color: #333;
        }
        h1, h2, h3, h4 {
            color: #002B5B;
        }
        .stButton>button {
            background-color: #002B5B;
            color: white;
            border-radius: 5px;
            padding: 0.5em 1.5em;
            font-weight: bold;
        }
        .stButton>button:hover {
            background-color: #004080;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

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

# Function to generate interview questions with options
def generate_interview_questions(resume_text, category, num_questions):
    prompt = f"""
    Review the following resume and generate {num_questions} {category.lower()} interview questions:

    Resume:
    {resume_text}

    Questions:
    """
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

        st.markdown("### Customize Your Questions")
        category = st.selectbox("Question Type", ["Behavioral", "Technical", "General"])
        num_questions = st.slider("Number of Questions", min_value=3, max_value=10, value=5)

        if st.button("Generate Interview Questions"):
            questions = generate_interview_questions(resume_text, category, num_questions)
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
