# prompt_lab.py
import os
import streamlit as st
from dotenv import load_dotenv

# OpenAI 1.x client + exceptions
try:
    from openai import OpenAI, APIError, RateLimitError, APIConnectionError
except Exception:  # fallback if package not available at build time
    OpenAI = None
    APIError = RateLimitError = APIConnectionError = Exception

# Load .env
load_dotenv()
API_KEY = (
    os.getenv("OPENAI_API_KEY")
    or os.getenv("OPENAI_KEY")
    or os.getenv("api_key")
)

# Build client if possible
client = None
if OpenAI and API_KEY:
    try:
        client = OpenAI(api_key=API_KEY)
    except Exception:
        client = None  # don’t crash page if something’s off


def _offline_mock(prompt: str) -> str:
    return (
        "(Offline mock)\n\n"
        "You asked:\n"
        f"{prompt}\n\n"
        "Sample résumé-ready output:\n"
        "- Led design of cloud-native solutions using AWS and Terraform.\n"
        "- Improved reliability by implementing CI/CD and IaC.\n"
        "- Collaborated with cross-functional teams to deliver measurable outcomes."
    )


def prompt_lab_ui():
    st.title("🧪 Prompt Lab")

    st.markdown(
        """
Use this tool to test any custom prompt in real-time.

- Enter your prompt below (e.g., “Generate a résumé summary for a cloud architect…”)
- Click **Run** to see the response.
- Uses OpenAI Chat Completions (falls back to an offline mock if no key).
"""
    )

    user_prompt = st.text_area("Custom Prompt", height=150, placeholder="Type a prompt…")

    if st.button("Run") and user_prompt.strip():
        # If client isn’t available (no key / bad import), use offline mock
        if client is None:
            st.info("No API key detected or client unavailable. Showing offline mock output.")
            st.markdown("### ✨ Response")
            st.write(_offline_mock(user_prompt))
            return

        try:
            with st.spinner("Generating response…"):
                resp = client.chat.completions.create(
                    model="gpt-3.5-turbo",     # change to gpt-4o-mini later if desired
                    messages=[
                        {"role": "system", "content": "You are a professional resume writer and career assistant."},
                        {"role": "user", "content": user_prompt},
                    ],
                    max_tokens=800,
                    temperature=0.7,
                )
            out = (resp.choices[0].message.content or "").strip()
            st.markdown("### ✨ Response")
            st.write(out if out else "(Empty response)")

        except (RateLimitError,) as e:
            st.error("Rate limit or quota issue. Once billing is enabled, try again.")
        except (APIConnectionError,) as e:
            st.error("Network/API connection issue. Please retry.")
        except (APIError,) as e:
            st.error(f"OpenAI API Error: {e}")
        except Exception as e:
            st.error(f"Unexpected Error: {e}")
