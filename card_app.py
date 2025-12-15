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

# Camera input
user_photo_camera = st.camera_input("Take a photo to include in your postcard")

# Fallback file uploader
st.markdown("**Or upload a photo if camera fails:**")
user_photo_upload = st.file_uploader("Upload a photo", type=["png","jpg","jpeg"])

# Decide which photo to use
user_photo = user_photo_camera if user_photo_camera is not None else user_photo_upload

# Preview uploaded/taken photo
if user_photo is not None:
    try:
        # Make sure the file is not empty
        if user_photo.getbuffer().nbytes > 0:
            pil_user_img = Image.open(user_photo).convert("RGBA")
            st.image(pil_user_img, caption="Your uploaded/taken photo", use_column_width=True)
        else:
            pil_user_img = None
    except Exception:
        pil_user_img = None
else:
    pil_user_img = None

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
def create_postcard(to_name, from_name, message, user_img=None):
    width, height = 1000, 800
    bg_color = (240, 240, 220)
    ink_brown = (92, 64, 51)

    base = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(base)
    padding = 60

    # Border
    draw.rectangle([0, 0, width-1, height-1], outline=(139,94,60), width=12)

    # Top text
    font_top = load_font("PatrickHand-Regular.ttf", 72)
    top_text = "Postcard for you!"
    bbox = draw.textbbox((0,0), top_text, font=font_top)
    text_width = bbox[2]-bbox[0]
    top_x = width//2 - text_width//2
    top_y = 20
    draw.text((top_x, top_y), top_text, fill=ink_brown, font=font_top)

    # Teddy bear (top-left, bigger)
    teddy_img = load_image("teddy-pic.png")
    max_teddy_size = 400
    teddy_ratio = min(max_teddy_size / teddy_img.width, max_teddy_size / teddy_img.height)
    teddy_img = teddy_img.resize((int(teddy_img.width*teddy_ratio), int(teddy_img.height*teddy_ratio)), Image.LANCZOS)
    teddy_x = padding
    teddy_y = top_y + 60
    base.paste(teddy_img, (teddy_x, teddy_y), teddy_img)

    # Fonts for text
    font_big = load_font("PatrickHand-Regular.ttf", 64)
    font_medium = load_font("PatrickHand-Regular.ttf", 56)
    font_message = load_font("PatrickHand-Regular.ttf", 52)

    # ---------------- Right side text ----------------
    right_x = int(width * 0.55)
    start_y = int(height * 0.25)
    line_gap = 80

    # From
    draw.text((right_x, start_y), f"From: {from_name}", fill=ink_brown, font=font_medium)
    # To
    draw.text((right_x, start_y + line_gap), f"To: {to_name}", fill=ink_brown, font=font_big)
    # Message label
    draw.text((right_x, start_y + line_gap*2), "Message:", fill=ink_brown, font=font_big)
    # Actual message content
    wrapped_message = textwrap.fill(message, width=22)
    draw.text((right_x + 10, start_y + line_gap*2.8), wrapped_message, fill=ink_brown, font=font_message)

    # ---------------- User photo (bottom-left) ----------------
    if user_img is not None:
        max_size = 300
        ratio = min(max_size/user_img.width, max_size/user_img.height)
        user_img = user_img.resize((int(user_img.width*ratio), int(user_img.height*ratio)), Image.LANCZOS)
        img_width, img_height = user_img.size
        user_x = padding
        user_y = height - img_height - 60
        frame_padding = 6
        frame_color = (92,64,51)
        draw.rectangle([user_x-frame_padding, user_y-frame_padding,
                        user_x+img_width+frame_padding, user_y+img_height+frame_padding],
                       outline=frame_color, width=4)
        base.paste(user_img, (user_x, user_y), user_img)

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
        "attachments": [{"content": encoded_image, "filename": "postcard.png"}]
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    response = requests.post("https://api.resend.com/emails", headers=headers, json=data)
    if response.status_code != 200:
        raise Exception(f"Resend error {response.status_code}: {response.text}")

# ---------------- Step 1: Preview postcard ----------------
if all([to_name, from_name, message_input]):
    postcard_image = create_postcard(to_name, from_name, message_input, user_img=pil_user_img)
    st.subheader("📬 Preview your postcard")
    st.image(postcard_image)

    # Save postcard to BytesIO for sending/downloading
    img_bytes = io.BytesIO()
    postcard_image.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    # ---------------- Step 2: Send & Download ----------------
    if st.button("📨 Send Postcard"):
        if not receiver_email:
            st.error("Please enter recipient email")
        elif not is_valid_email(receiver_email):
            st.error("Invalid email address")
        else:
            try:
                send_postcard_email(img_bytes, receiver_email)
                st.success("Postcard sent successfully 💖")
                st.download_button(
                    label="💾 Download Postcard",
                    data=img_bytes,
                    file_name="postcard.png",
                    mime="image/png"
                )
            except Exception as e:
                st.error(str(e))
