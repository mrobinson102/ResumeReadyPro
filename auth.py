import streamlit as st
import streamlit_authenticator as stauth
import json, os

USERS_DB = "user_data.json"

def load_users():
    if not os.path.exists(USERS_DB):
        return {}
    with open(USERS_DB, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_DB, "w") as f:
        json.dump(data, f, indent=2)

def login_flow():
    user_data = load_users()
    credentials = {'usernames': {}}
    for uname, uinfo in user_data.items():
        if "password" in uinfo:
            credentials['usernames'][uname] = {
                'name': uinfo.get('name', uname),
                'password': stauth.Hasher([uinfo['password']]).generate()[0]
            }
    authenticator = stauth.Authenticate(credentials, "app", "cookie", 30)
    name, auth_status, username = authenticator.login("Login", "main")
    if auth_status:
        authenticator.logout("Logout", "sidebar")
        st.sidebar.success(f"Welcome {username}")
    elif auth_status is False:
        st.error("Invalid credentials")
    return auth_status, username if auth_status else None