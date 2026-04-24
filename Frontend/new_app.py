import streamlit as st

st.set_page_config(layout="wide")

# ---------- CSS ----------
st.markdown("""
<style>
.block-container {
    padding-top: 2rem;
}

.post-box {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 20px;
}

.feed-post {
    background-color: white;
    padding: 15px;
    border-radius: 10px;
    margin-bottom: 15px;
    box-shadow: 0px 1px 3px rgba(0,0,0,0.1);
}

.stButton>button {
    border-radius: 20px;
}
</style>
""", unsafe_allow_html=True)

# ---------- Top Bar ----------
col1, col2, col3 = st.columns([6,1,1])

with col2:
    if st.button("Login"):
        st.switch_page("pages/login.py")

with col3:
    if st.button("Register"):
        st.switch_page("pages/register.py")

st.title("Mini Twitter 🐦")

# ---------- Post Box ----------
st.markdown('<div class="post-box">', unsafe_allow_html=True)
post = st.text_area("What's happening?", height=100)
if st.button("Post"):
    st.success("Post submitted (connect to backend later)")
st.markdown('</div>', unsafe_allow_html=True)

# ---------- Feed ----------
st.subheader("Feed")

# Fake posts for now
posts = [
    {"user": "Mateusz", "content": "Hello world!"},
    {"user": "Anna", "content": "Streamlit is actually nice."},
]

for p in posts:
    st.markdown(f"""
    <div class="feed-post">
        <strong>@{p['user']}</strong>
        <p>{p['content']}</p>
    </div>
    """, unsafe_allow_html=True)