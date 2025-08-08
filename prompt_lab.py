import streamlit as st
import openai
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Page title
st.title("🧪 Prompt Lab")

# 👉 Instructions
st.info("""
**How to Use the Prompt Lab**

Use the Prompt Lab to test and experiment with custom GPT prompts related to résumé building, job search, or career strategy.

**Steps:**

1. ✍️ Enter your **custom prompt** in the text box. Examples:
   - "Generate a résumé summary for a software engineer with 10 years of experience in cloud computing."
   - "Rewrite this bullet point to sound more impactful: Led daily standups for a cross-functional team."
   - "Identify keywords missing in this résumé for a cybersecurity analyst role."

2. 📄 Include any necessary resume details or context in the prompt.

3. ▶️ Click **Run** to get GPT-generated output.

> Tip: Great for résumé bullets, summaries, job title targeting, and gap analysis experimentation.
""")

# Prompt input
prompt = st.text_area("Custom Prompt", height=250)

if st.button("Run") and prompt.strip():
    try:
        with st.spinner("Thinking..."):
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional résumé coach and career strategist."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=700
            )
        output = response.choices[0].message.content
        st.markdown("### 💡 Response")
        st.markdown(output)
    except Exception as e:
        st.error(f"Something went wrong: {e}")
