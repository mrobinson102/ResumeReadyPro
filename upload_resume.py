import streamlit as st

def upload_resume_page(username):
    st.header("Upload Resume & Get Interview Questions")
    st.info("Upload and question generation logic goes here.")

elif page == "Upload Resume":
    st.subheader("📤 Upload Resume and Generate Interview Questions")
    uploaded = st.file_uploader("Upload PDF Resume", type=["pdf"])
    if uploaded:
        reader = PdfReader(uploaded)
        extracted_pages = [page.extract_text() for page in reader.pages if page.extract_text() is not None]
        text = "\n".join(extracted_pages)

        st.text_area("Extracted Resume Text", text, height=200)

        qtype = st.selectbox("Question Type", ["Behavioral", "Technical", "Mixed"])
        qcount = st.slider("Number of Questions", 1, 10, 5)

        if st.button("Generate Interview Questions"):
            prompt = f"Generate {qcount} {qtype} interview questions from this resume:\n{text}"
            try:
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.write(response.choices[0].message.content)
                user_data[username]["resumes"] += 1
                user_data[username]["questions"] += qcount
                save_users(user_data)
            except Exception as e:
                st.error(f"An error occurred: {e}")
