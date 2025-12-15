import streamlit as st
from PIL import Image
import requests
import re

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Send a Postcard 💌",
    layout="centered"
)

st.title("📮 Send a Postcard")

# ---------------- Image ----------------
try:
    postcard = Image.open("postcard_template.png")
    st.image(postcard, use_container_width=True)
except:
    pass

# ---------------- Inputs ----------------
to_name = st.text_input("To")
from_name = st.text_input("From")
message = st.text_area("Message", max_chars=500)
receiver_email = st.text_input("Recipient Email")

# ---------------- Helpers ----------------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def send_postcard_email():
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {st.secrets['RESEND_API_KEY']}",
        "Content-Type": "application/json",
    }

    html = f"""
    <h2>💌 You received a postcard</h2>
    <p>{message}</p>
    <p>— {from_name}</p>
    """

    data = {
        "from": "Postcard <onboarding@resend.dev>",
        "to": [receiver_email],
        "subject": "You received a postcard 💌",
        "html": html,
    }

    r = requests.post(url, headers=headers, json=data)
    r.raise_for_status()

# ---------------- Button ----------------
if st.button("📨 Send Postcard"):
    if not all([to_name, from_name, message, receiver_email]):
        st.error("Please fill all fields")
    elif not is_valid_email(receiver_email):
        st.error("Invalid email address")
    else:
        try:
            send_postcard_email()
            st.success("Postcard sent 💖")
        except Exception:
            st.error("Something went wrong. Please try again later.")
