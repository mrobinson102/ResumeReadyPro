import streamlit as st

def about_page(username):
    st.image("assets/ceo_photo.jpg", width=150)
    st.markdown("""
    ### About ResumeReadyPro
    AI-powered resume and job fit platform helping professionals level up.

    **CEO Bio:** Michelle Robinson, 25+ years in federal data architecture and DevSecOps.
    """)