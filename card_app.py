import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import re
import requests
import base64
import textwrap

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Send a Stylish Postcard 💌",
    layout="centered"
)

st.title("📮 Send a Stylish Postcard")

# ---------------- Inputs ----------------
to_name = st.text_input("To")
from_name = st.text_input("From")
message = st.text_area("Message", max_chars=500)
receiver_email = st.text_input("Recipient Email")

# ---------------- Helpers ----------------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def create_stylish_postcard(to_name, from_name, message):
    """
    Generate a stylish postcard with beige background, brown border, large user input text, 
    and a stamp on top-right.
    """
    # Canvas
    width, height = 800, 600  # smaller postcard
    base = Image.new("RGBA", (width, height), (245, 240, 225))  # beige background
    draw = ImageDraw.Draw(base)

    # Brown border
    border_thickness = 20
    draw.rectangle([0,0,width-1,height-1], outline=(139,94,60), width=border_thickness)

    # Fonts
    try:
        font_to = ImageFont.truetype("arial.ttf", 60)
        font_from = ImageFont.truetype("arial.ttf", 60)
        font_message = ImageFont.truetype("arial.ttf", 70)
        font_stamp = ImageFont.truetype("arial.ttf", 40)
    except:
        font_to = font_from = font_message = font_stamp = ImageFont.load_default()

    padding = 30

    # ---------------- To ----------------
    to_text = f"To: {to_name}"
    draw.text((padding, padding), to_text, fill=(0,0,0), font=font_to)

    # ---------------- From ----------------
    from_text = f"From: {from_name}"
    from_bbox = draw.textbbox((0,0), from_text, font=font_from)
    from_height = from_bbox[3] - from_bbox[1]
    draw.text((padding, height - padding - from_height), from_text, fill=(0,0,0), font=font_from)

    # ---------------- Message ----------------
    # Wrap message
    wrapper = textwrap.TextWrapper(width=25)
    lines = wrapper.wrap(text=message)

    # Calculate total height
    line_height = font_message.getbbox("A")[3] - font_message.getbbox("A")[1] + 20
    total_text_height = len(lines) * line_height
    start_y = (height - total_text_height) // 2  # center vertically

    # Draw message
    for line in lines:
        text_width = draw.textlength(line, font=font_message)
        start_x = (width - text_width) // 2  # center horizontally
        draw.text((start_x, start_y), line, fill=(0,0,0), font=font_message)
        start_y += line_height

    # ---------------- Stamp ----------------
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
        "subject": "You received a stylish postcard 💌",
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
            # Generate stylish postcard
            postcard_image = create_stylish_postcard(to_name, from_name, message)

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
