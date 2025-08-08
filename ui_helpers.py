import streamlit as st

def setup_ui():
    st.markdown("""
        <style>
            .sidebar .sidebar-content {
                background-color: #f4f4f4;
            }
            .stButton > button {
                color: white;
                background: linear-gradient(to right, #00b894, #0984e3);
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 0.5rem;
                font-weight: bold;
            }
        </style>
    """, unsafe_allow_html=True)