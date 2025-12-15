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

# ---------------- Camera Input ----------------
user_photo = st.camera_input("Take a photo to include in your postcard")

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

# ---------------- Postcard Generator ----------------
def create_postcard_super_clear(to_name, from_name, message, user_img=None):
    width, height = 1000, 800
    bg_color = (240, 240, 220)
    ink_brown = (92, 64, 51)

    base = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(base)
    padding = 60

    # ---------------- Border ----------------
    draw.rectangle(
        [0, 0, width - 1, height - 1],
        outline=(139, 94, 60),
        width=12
    )

    # ---------------- Top Text: "Postcard for you!" ----------------
    font_top = load_font("PatrickHand-Regular.ttf", 72)
    top_text = "Postcard for you!"
    bbox = draw.textbbox((0, 0), top_text, font=font_top)
    text_width = bbox[2] - bbox[0]
    top_x = width // 2 - text_width // 2
    top_y = 20  # near top
    draw.text((top_x, top_y), top_text, fill=ink_brown, font=font_top)

    # ---------------- Teddy Image (LEFT, BIG, CLEAR) ----------------
    teddy_img = load_image("teddy-pic.png")
    max_teddy_size = 420
    teddy_ratio = min(
        max_teddy_size / teddy_img.width,
        max_teddy_size / teddy_img.height
    )
    teddy_img = teddy_img.resize(
        (int(teddy_img.width * teddy_ratio), int(teddy_img.height * teddy_ratio)),
        Image.LANCZOS
    )
    teddy_x = padding + 20
    teddy_y = height // 2 - teddy_img.height // 2
    base.paste(teddy_img, (teddy_x, teddy_y), teddy_img)

    # ---------------- Add user camera image if available ----------------
    if user_img is not None:
        # Resize to fit top-right corner
        max_size = 200
        ratio = min(max_size / user_img.width, max_size / user_img.height)
        user_img = user_img.resize(
            (int(user_img.width * ratio), int(user_img.height * ratio)),
            Image.LANCZOS
        )
        user_x = width - user_img.width - padding
        user_y = top_y + 80  # below top text
        base.paste(user_img, (user_x, user_y), user_img)

    # ---------------- Fonts for postcard text ----------------
    font_big = load_font("PatrickHand-Regular.ttf", 64)
    font_medium = load_font("PatrickHand-Regular.ttf", 56)
    font_message = load_font("PatrickHand-Regular.ttf", 52)

    # ---------------- Right column ----------------
    right_x = int(width * 0.55)
    start_y = int(height * 0.30)
    line_gap = 80

    draw.text(
        (right_x, start_y),
        f"To:  {to_name}",
        fill=ink_brown,
        font=font_big
    )

    draw.text(
        (right_x, start_y + line_gap * 1.4),
        "Message:",
        fill=ink_brown,
        font=font_big
    )

    wrapped_message = textwrap.fill(message, width=22)
    draw.text(
        (right_x + 10, start_y + line_gap * 2.4),
        wrapped_message,
        fill=ink_brown,
        font=font_message
    )

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
            # Convert camera input to PIL Image if available
            pil_user_img = None
            if user_photo is not None:
                pil_user_img = Image.open(user_photo).convert("RGBA")

            postcard_image = create_postcard_super_clear(
                to_name,
                from_name,
                message_input,
                user_img=pil_user_img
            )

            st.image(postcard_image)

            img_bytes = io.BytesIO()
            postcard_image.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            send_postcard_email(img_bytes, receiver_email)

            st.success("Postcard sent successfully 💖")

        except Exception as e:
            st.error(str(e))
