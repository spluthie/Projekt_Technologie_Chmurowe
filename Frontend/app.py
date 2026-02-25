import streamlit as st
import requests

# API URLs
AUTH_URL = "http://localhost:8000"
POST_URL = "http://localhost:8001"

# Initialize session state for JWT token
if "token" not in st.session_state:
    st.session_state.token = ""

# --- LOGIN ---
st.title("Mini Social App")

st.subheader("Login / Register")
username = st.text_input("Username")
password = st.text_input("Password", type="password")

col1, col2 = st.columns(2)

with col1:
    if st.button("Register"):
        try:
            res = requests.post(f"{AUTH_URL}/register",
                                json={"username": username, "password": password})
            if res.status_code == 200:
                st.success("Registered successfully!")
            else:
                st.error(res.json()["detail"])
        except Exception as e:
            st.error(f"Error: {e}")

with col2:
    if st.button("Login"):
        try:
            res = requests.post(f"{AUTH_URL}/login",
                                json={"username": username, "password": password})
            if res.status_code == 200:
                st.session_state.token = res.json()["access_token"]
                st.success("Logged in!")
            else:
                st.error(res.json()["detail"])
        except Exception as e:
            st.error(f"Error: {e}")

# --- LOGOUT ---
if st.session_state.token:
    if st.button("Logout"):
        st.session_state.token = ""
        st.success("Logged out!")

# --- CREATE POST ---
if st.session_state.token:
    st.subheader("Create Post")
    content = st.text_area("Post content")
    if st.button("Submit Post"):
        try:
            headers = {"Authorization": f"Bearer {st.session_state.token}"}
            res = requests.post(f"{POST_URL}/posts", json={"content": content}, headers=headers)
            if res.status_code == 200:
                st.success("Post created!")
            else:
                st.error(res.json()["detail"])
        except Exception as e:
            st.error(f"Error: {e}")

# --- DISPLAY POSTS ---
st.subheader("Latest Posts")
try:
    res = requests.get(f"{POST_URL}/posts")
    posts = res.json()
    for p in posts:
        st.write(f"**{p['username']}**: {p['content']}")
except Exception as e:
    st.error(f"Error fetching posts: {e}")