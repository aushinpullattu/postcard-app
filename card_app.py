import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import re
import requests
import base64
import textwrap
import os

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Send a Postcard 💌",
    layout="centered"
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #F5F0E1;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📮 Send a Postcard")

# ---------------- Inputs ----------------
to_name = st.text_input("To")
from_name = st.text_input("From")
message_input = st.text_area("Message", max_chars=500)
receiver_email = st.text_input("Recipient Email")

# ---------------- Helpers ----------------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def load_font(font_name, size):
    if not os.path.exists(font_name):
        raise FileNotFoundError(f"Font file not found: {font_name}")
    return ImageFont.truetype(font_name, size)

def create_postcard_super_clear(to_name, from_name, message):
    # HIGH RES canvas (2x)
    width, height = 1000, 800
    base = Image.new("RGB", (width, height), (240, 240, 220))
    draw = ImageDraw.Draw(base)
    padding = 60

    # Border
    draw.rectangle(
        [0, 0, width - 1, height - 1],
        outline=(139, 94, 60),
        width=12
    )

    # Fonts (BIG + cute)
    font_to = load_font("PatrickHand-Regular.ttf", 64)
    font_from = load_font("PatrickHand-Regular.ttf", 58)
    font_message = load_font("PatrickHand-Regular.ttf", 52)
    font_stamp = load_font("PatrickHand-Regular.ttf", 42)

    # Stamp
    draw.text(
        (width - padding - 140, padding),
        "STAMP",
        fill=(139, 94, 60),
        font=font_stamp
    )

    # To
    draw.text(
        (width - padding - 480, height // 2 - 40),
        f"To: {to_name}",
        fill=(0, 0, 0),
        font=font_to
    )

    # From
    draw.text(
        (padding, height - padding - 80),
        f"From: {from_name}",
        fill=(0, 0, 0),
        font=font_from
    )

    # Message (wrapped)
    wrapped = textwrap.fill(message, width=24)
    draw.text(
        (width - padding - 520, height - padding - 280),
        f"Message:\n{wrapped}",
        fill=(0, 0, 0),
        font=font_message
    )

    return base

def send_postcard_email(image_bytes):
    encoded_image = base64.b64encode(image_bytes.getvalue()).decode()

    data = {
        "from": "Postcard <onboarding@yourdomain.com>",
        "to": [receiver_email],
        "subject": "You received a postcard 💌",
        "html": "<p>Here’s your postcard!</p>",
        "attachments": [
            {
                "content": encoded_image,
                "filename": "postcard.png"
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {st.secrets['RESEND_API_KEY']}",
        "Content-Type": "application/json"
    }

    r = requests.post("https://api.resend.com/emails", headers=headers, json=data)
    r.raise_for_status()

# ---------------- Button ----------------
if st.button("📨 Send Postcard"):
    if not all([to_name, from_name, message_input, receiver_email]):
        st.error("Please fill all fields")
    elif not is_valid_email(receiver_email):
        st.error("Invalid email address")
    else:
        try:
            postcard_image = create_postcard_super_clear(
                to_name,
                from_name,
                message_input
            )

            # IMPORTANT: DO NOT set width here
            st.image(postcard_image)

            img_bytes = io.BytesIO()
            postcard_image.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            send_postcard_email(img_bytes)

            st.success("Postcard generated and sent 💖")

        except FileNotFoundError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Something went wrong: {e}")
