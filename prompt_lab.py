# prompt_lab.py

import streamlit as st
import os
import openai
from dotenv import load_dotenv
from openai.error import OpenAIError  # ✅ fixed import

# Load API key
load_dotenv()
openai.api_key = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENAI_KEY")
    or os.getenv("api_key")
)

def prompt_lab_ui():
    st.title("🧪 Prompt Lab")

    st.markdown("""
    Use this tool to test any custom prompt in real-time.
    - Enter your prompt below (e.g., “Generate a résumé summary for a cloud architect…”)
    - Click **Run** to see the response.
    - GPT-3.5 Turbo is used.
    """)

    user_prompt = st.text_area("Custom Prompt", height=150)

    if st.button("Run") and user_prompt.strip():
        try:
            with st.spinner("Generating response..."):
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a professional resume writer and career assistant."},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=800,
                    temperature=0.7,
                )
                st.markdown("### ✨ Response")
                st.write(response.choices[0].message.content.strip())

        except OpenAIError as e:
            st.error(f"OpenAI API Error: {e}")
        except Exception as e:
            st.error(f"Unexpected Error: {e}")
