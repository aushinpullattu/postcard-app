import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import re
import requests
import base64
import textwrap

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Send a Postcard 💌",
    layout="centered"
)

# Background color
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

def create_postcard_clear(to_name, from_name, message):
    # Final canvas size (NO resizing)
    width, height = 500, 400
    base = Image.new("RGBA", (width, height), (240, 240, 220))
    draw = ImageDraw.Draw(base)
    padding = 30

    # Border
    draw.rectangle(
        [0, 0, width - 1, height - 1],
        outline=(139, 94, 60),
        width=6
    )

    # Load font
    try:
        font_to = ImageFont.truetype("Patrick.ttf", 28)
        font_from = ImageFont.truetype("Patrick.ttf", 26)
        font_message = ImageFont.truetype("Patrick.ttf", 22)
        font_stamp = ImageFont.truetype("Patrick.ttf", 18)
    except:
        font_to = font_from = font_message = font_stamp = ImageFont.load_default()

    # Stamp (top-right)
    draw.text(
        (width - padding - 70, padding),
        "STAMP",
        fill=(139, 94, 60),
        font=font_stamp
    )

    # To (middle-right)
    draw.text(
        (width - padding - 220, height // 2 - 20),
        f"To: {to_name}",
        fill=(0, 0, 0),
        font=font_to
    )

    # From (bottom-left)
    draw.text(
        (padding, height - padding - 40),
        f"From: {from_name}",
        fill=(0, 0, 0),
        font=font_from
    )

    # Message (wrapped, bottom-right)
    wrapped_message = textwrap.fill(f"Message: {message}", width=26)
    draw.text(
        (width - padding - 260, height - padding - 120),
        wrapped_message,
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

    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {st.secrets['RESEND_API_KEY']}",
        "Content-Type": "application/json"
    }

    r = requests.post(url, headers=headers, json=data)
    r.raise_for_status()

# ---------------- Button ----------------
if st.button("📨 Send Postcard"):
    if not all([to_name, from_name, message_input, receiver_email]):
        st.error("Please fill all fields")
    elif not is_valid_email(receiver_email):
        st.error("Invalid email address")
    else:
        try:
            postcard_image = create_postcard_clear(
                to_name,
                from_name,
                message_input
            )

            # Preview
            st.image(postcard_image, width=500)

            # Convert to bytes
            img_bytes = io.BytesIO()
            postcard_image.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Send email
            send_postcard_email(img_bytes)

            st.success("Postcard generated and sent 💖")

        except requests.exceptions.HTTPError as http_err:
            st.error(f"HTTP Error: {http_err} — check your Resend API key")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
