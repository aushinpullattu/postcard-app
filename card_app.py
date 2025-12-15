import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import requests
import io
import re

st.set_page_config(page_title="Send a Postcard 💌", layout="centered")
st.title("📮 Send a Postcard")

TEMPLATE_PATH = "postcard_template.png"

# ---------------- Inputs ----------------
to_name = st.text_input("To")
from_name = st.text_input("From")
message = st.text_area("Message", max_chars=300)
receiver_email = st.text_input("Recipient Email")

# ---------------- Helpers ----------------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def generate_postcard(to_name, from_name, message):
    img = Image.open(TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Use default font (safe on Streamlit Cloud)
    font_small = ImageFont.load_default()
    font_medium = ImageFont.load_default()

    # ---- Positions (tuned for your template) ----
    # Right side text
    to_position = (1050, 450)
    message_start = (1050, 520)
    from_position = (300, 900)

    # Draw "To"
    draw.text(to_position, f"To: {to_name}", fill="#4a4a4a", font=font_medium)

    # Wrap message nicely
    wrapped_text = textwrap.fill(message, width=35)
    draw.multiline_text(
        message_start,
        wrapped_text,
        fill="#4a4a4a",
        font=font_small,
        spacing=8
    )

    # Draw "From"
    draw.text(from_position, f"From: {from_name}", fill="#4a4a4a", font=font_medium)

    return img

def send_email_with_image(image):
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    files = {
        "file": ("postcard.png", buffer, "image/png")
    }

    data = {
        "from": "Postcard <onboarding@resend.dev>",
        "to": receiver_email,
        "subject": "You received a postcard 💌",
        "html": "<p>You received a cute postcard 💌</p>"
    }

    headers = {
        "Authorization": f"Bearer {st.secrets['RESEND_API_KEY']}"
    }

    response = requests.post(
        "https://api.resend.com/emails",
        headers=headers,
        data=data,
        files=files
    )

    response.raise_for_status()

# ---------------- Preview ----------------
if to_name and from_name and message:
    preview = generate_postcard(to_name, from_name, message)
    st.image(preview, caption="Postcard Preview 💖", use_container_width=True)

# ---------------- Send ----------------
if st.button("📨 Send Postcard"):
    if not all([to_name, from_name, message, receiver_email]):
        st.error("Please fill all fields")
    elif not is_valid_email(receiver_email):
        st.error("Invalid email address")
    else:
        try:
            postcard = generate_postcard(to_name, from_name, message)
            send_email_with_image(postcard)
            st.success("Postcard sent 💌")
        except Exception as e:
            st.error("Failed to send postcard")
            st.caption(str(e))
