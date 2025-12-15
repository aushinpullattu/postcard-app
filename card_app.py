import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import re
import requests
import base64

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Send a Postcard 💌",
    layout="centered"
)

st.title("📮 Send a Postcard")

# ---------------- Inputs ----------------
to_name = st.text_input("To")
from_name = st.text_input("From")
message = st.text_area("Message", max_chars=500)
receiver_email = st.text_input("Recipient Email")

# ---------------- Helpers ----------------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def create_fixed_super_big_postcard(to_name, from_name, message):
    """
    Create a postcard with fixed super big fonts:
    - To: middle-right
    - From: bottom-left
    - Message: bottom-right
    - Stamp: top-right
    """
    # Canvas
    width, height = 500, 300
    base = Image.new("RGBA", (width, height), (245, 240, 225))  # beige background
    draw = ImageDraw.Draw(base)

    # Brown border
    border_thickness = 20
    draw.rectangle([0,0,width-1,height-1], outline=(139,94,60), width=border_thickness)

    # ---------------- Fixed super big fonts ----------------
    try:
        font_to = ImageFont.truetype("arial.ttf", 400)
        font_from = ImageFont.truetype("arial.ttf", 400)
        font_message = ImageFont.truetype("arial.ttf", 350)
        font_stamp = ImageFont.truetype("arial.ttf", 200)
    except:
        font_to = font_from = font_message = font_stamp = ImageFont.load_default()

    padding = 40

    # ---------------- To (middle-right) ----------------
    to_text = f"To: {to_name}"
    to_bbox = draw.textbbox((0,0), to_text, font=font_to)
    to_width = to_bbox[2] - to_bbox[0]
    to_height = to_bbox[3] - to_bbox[1]
    to_x = width - padding - to_width
    to_y = height // 2 - to_height // 2
    draw.text((to_x, to_y), to_text, fill=(0,0,0), font=font_to)

    # ---------------- From (bottom-left) ----------------
    from_text = f"From: {from_name}"
    from_bbox = draw.textbbox((0,0), from_text, font=font_from)
    from_height = from_bbox[3] - from_bbox[1]
    draw.text((padding, height - padding - from_height), from_text, fill=(0,0,0), font=font_from)

    # ---------------- Message (bottom-right) ----------------
    # Draw as one big block
    msg_bbox = draw.textbbox((0,0), message, font=font_message)
    msg_width = msg_bbox[2] - msg_bbox[0]
    msg_height = msg_bbox[3] - msg_bbox[1]

    msg_x = width - padding - msg_width
    msg_y = height - padding - msg_height
    draw.text((msg_x, msg_y), message, fill=(0,0,0), font=font_message)

    # ---------------- Stamp (top-right) ----------------
    stamp_text = "STAMP"
    stamp_bbox = draw.textbbox((0,0), stamp_text, font=font_stamp)
    stamp_width = stamp_bbox[2] - stamp_bbox[0]
    draw.text((width - padding - stamp_width, padding), stamp_text, fill=(139,94,60), font=font_stamp)

    return base

def send_postcard_email(image_bytes):
    """Send postcard via Resend API with attachment"""
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
    if not all([to_name, from_name, message, receiver_email]):
        st.error("Please fill all fields")
    elif not is_valid_email(receiver_email):
        st.error("Invalid email address")
    else:
        try:
            # Generate postcard
            postcard_image = create_fixed_super_big_postcard(to_name, from_name, message)

            # Show preview
            st.image(postcard_image, use_column_width=True)

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
