import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import re
import requests
import base64
import textwrap

# ---------------- Page config ----------------
st.set_page_config(
    page_title="Send a New Postcard 💌",
    layout="centered"
)

st.title("📮 Send a New Postcard")

# ---------------- Inputs ----------------
to_name = st.text_input("To")
from_name = st.text_input("From")
message = st.text_area("Message", max_chars=500)
receiver_email = st.text_input("Recipient Email")

# ---------------- Helpers ----------------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def create_new_postcard(to_name, from_name, message):
    """
    Generate a completely new postcard with a fresh design and dynamic user inputs.
    """
    # Create blank canvas
    width, height = 1200, 800
    base = Image.new("RGBA", (width, height), (255, 248, 230))  # light cream background
    draw = ImageDraw.Draw(base)

    # Optional: add some border or decoration
    border_color = (200, 160, 120)
    border_thickness = 20
    draw.rectangle(
        [border_thickness//2, border_thickness//2, width - border_thickness//2, height - border_thickness//2],
        outline=border_color, width=border_thickness
    )

    # Fonts
    try:
        font_large = ImageFont.truetype("arial.ttf", 48)  # To/From
        font_medium = ImageFont.truetype("arial.ttf", 36)  # Message
        font_small = ImageFont.truetype("arial.ttf", 28)   # Optional decorations
    except:
        font_large = font_medium = font_small = ImageFont.load_default()

    padding = 50

    # Draw To: top-right
    to_text = f"To: {to_name}"
    to_pos = (width - padding - draw.textlength(to_text, font=font_large), padding)
    draw.text(to_pos, to_text, fill=(0, 0, 0), font=font_large)

    # Draw From: bottom-left
    from_text = f"From: {from_name}"
    from_pos = (padding, height - padding - 50)
    draw.text(from_pos, from_text, fill=(0, 0, 0), font=font_large)

    # Message area
    message_top = padding + 120
    message_bottom = height - padding - 120
    message_left = padding + 40
    message_right = width - padding - 40
    message_width = message_right - message_left

    # Wrap message
    wrapper = textwrap.TextWrapper(width=40)
    lines = wrapper.wrap(text=message)

    # Center vertically
    total_text_height = len(lines) * 50
    start_y = message_top + ((message_bottom - message_top - total_text_height) // 2)

    for line in lines:
        draw.text((message_left, start_y), line, fill=(0, 0, 0), font=font_medium)
        start_y += 50

    # Optional: add a small stamp box
    stamp_size = 100
    draw.rectangle(
        [width - padding - stamp_size, height - padding - stamp_size, width - padding, height - padding],
        outline=(150, 0, 0), width=5
    )
    draw.text((width - padding - stamp_size + 10, height - padding - stamp_size + 30), "STAMP", fill=(150,0,0), font=font_small)

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
            # Generate completely new postcard
            postcard_image = create_new_postcard(to_name, from_name, message)

            # Show postcard preview in Streamlit
            st.image(postcard_image, use_container_width=True)

            # Convert to bytes for email
            img_bytes = io.BytesIO()
            postcard_image.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Send email
            send_postcard_email(img_bytes)
            st.success("Postcard generated and sent 💖")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
