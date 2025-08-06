import streamlit as st

st.set_page_config(page_title="ResumeReadyPro", layout="centered")

st.title("📄 ResumeReadyPro")
st.subheader("Generate resume summaries and interview questions")

with st.form("user_form"):
    full_name = st.text_input("Full Name")
    email = st.text_input("Email Address")
    position = st.text_input("Target Job Title")
    skills = st.text_area("Skills or Keywords (comma-separated)")
    resume_text = st.text_area("Paste your resume text here")

    submitted = st.form_submit_button("Generate")

if submitted:
    if not resume_text:
        st.warning("Please paste your resume to continue.")
    else:
        # Simulated outputs
        st.success("✅ AI Summary:")
        st.write(f"{full_name} is a results-driven professional targeting a {position} role...")

        st.success("🎯 Sample Interview Questions:")
        st.markdown("""
        1. Can you describe your experience with [insert key skill]?
        2. How have you contributed to success in previous roles?
        3. Tell us about a challenging project and how you handled it.
        """)

        st.download_button("📥 Download Summary", data="Resume Summary Text Here", file_name="summary.txt")
        st.download_button("📥 Download Questions", data="Interview Questions Here", file_name="questions.txt")
