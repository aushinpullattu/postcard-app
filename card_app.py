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
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------------- Hide Streamlit UI ----------------
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stApp {
    background-color: #F5F0E1;
}
</style>
""", unsafe_allow_html=True)

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

def load_image(image_name):
    if not os.path.exists(image_name):
        raise FileNotFoundError(f"Image file not found: {image_name}")
    return Image.open(image_name).convert("RGBA")

def format_text(text):
    text = text.strip()
    if text.islower():
        return text.capitalize()
    return text

# ---------------- Postcard Generator ----------------
def create_postcard_super_clear(to_name, from_name, message):
    width, height = 1000, 800
    bg_color = (240, 240, 220)
    ink_brown = (92, 64, 51)

    base = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(base)
    padding = 60

    # Border
    draw.rectangle(
        [0, 0, width - 1, height - 1],
        outline=(139, 94, 60),
        width=12
    )

    # ---------------- Teddy Image (proportional resize) ----------------
    teddy_img = load_image("teddy-pic.png")
    max_size = 420
    ratio = min(max_size / teddy_img.width, max_size / teddy_img.height)
    teddy_img = teddy_img.resize(
        (int(teddy_img.width * ratio), int(teddy_img.height * ratio)),
        Image.LANCZOS
    )

    teddy_x = padding + 20
    teddy_y = height // 2 - teddy_img.height // 2
    base.paste(teddy_img, (teddy_x, teddy_y), teddy_img)

    # Fonts
    font_big = load_font("PatrickHand-Regular.ttf", 64)
    font_medium = load_font("PatrickHand-Regular.ttf", 56)
    font_message = load_font("PatrickHand-Regular.ttf", 52)

    # Format text
    to_name = format_text(to_name)
    from_name = format_text(from_name)
    message = format_text(message)

    # ---------------- Right column ----------------
    right_x = int(width * 0.55)
    start_y = int(height * 0.28)
    line_gap = 80

    # To
    draw.text(
        (right_x, start_y),
        f"To:  {to_name}",
        fill=ink_brown,
        font=font_big
    )

    # Message label (extra spacing)
    draw.text(
        (right_x, start_y + line_gap * 1.4),
        "Message:",
        fill=ink_brown,
        font=font_big
    )

    # Message text
    wrapped_message = textwrap.fill(message, width=22)
    draw.text(
        (right_x + 10, start_y + line_gap * 2.4),
        wrapped_message,
        fill=ink_brown,
        font=font_message
    )

    # From (bottom-left)
    draw.text(
        (padding + 40, height - 120),
        f"From: {from_name}",
        fill=ink_brown,
        font=font_medium
    )

    return base

# ---------------- Email Sender ----------------
def send_postcard_email(image_bytes, receiver_email):
    api_key = st.secrets.get("RESEND_API_KEY")

    if not api_key:
        raise ValueError("RESEND_API_KEY not found in Streamlit secrets")

    encoded_image = base64.b64encode(image_bytes.getvalue()).decode()

    data = {
        "from": "Postcard <hello@postcard.work>",
        "to": [receiver_email],
        "subject": "You received a postcard 💌",
        "html": "<p>You’ve received a cute postcard 💌</p>",
        "attachments": [
            {
                "content": encoded_image,
                "filename": "postcard.png"
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://api.resend.com/emails",
        headers=headers,
        json=data
    )

    if response.status_code != 200:
        raise Exception(f"Resend error {response.status_code}: {response.text}")

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

            st.image(postcard_image)

            img_bytes = io.BytesIO()
            postcard_image.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            send_postcard_email(img_bytes, receiver_email)

            st.success("Postcard sent successfully 💖")

        except Exception as e:
            st.error(str(e))
