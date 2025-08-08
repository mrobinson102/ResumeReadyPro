import streamlit as st
from ui_helpers import setup_ui
from auth import login_flow
from summary import summary_page
from upload_resume import upload_resume_page
from admin import admin_dashboard_page
from job_fit import job_fit_page
from prompt_lab import prompt_lab_page
from about import about_page

st.set_page_config(page_title="ResumeReadyPro", layout="wide")
setup_ui()

auth_status, username = login_flow()
if not auth_status:
    st.stop()

PAGES = {
    "Generate Summary": summary_page,
    "Upload Resume": upload_resume_page,
    "Job Fit Analysis": job_fit_page,
    "Prompt Lab": prompt_lab_page,
    "Admin Dashboard": admin_dashboard_page,
    "About": about_page,
}

page = st.sidebar.radio("Navigate", list(PAGES.keys()))
PAGES[page](username)