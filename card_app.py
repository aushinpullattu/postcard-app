import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import re
import requests
import os
import textwrap

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

def create_postcard(to_name, from_name, message):
    # Load template
    template_path = os.path.join(os.path.dirname(__file__), "postcard_template.png")
    base = Image.open(template_path).convert("RGBA")

    # Optionally resize to standard postcard size
    base = base.resize((1200, 800))
    draw = ImageDraw.Draw(base)

    # Fonts
    try:
        font_large = ImageFont.truetype("arial.ttf", 48)  # To/From
        font_medium = ImageFont.truetype("arial.ttf", 36)  # Message
    except:
        font_large = font_medium = ImageFont.load_default()

    # ---------------- Positions ----------------
    padding = 50
    # To in top-right
    to_pos = (base.width - padding - draw.textlength(f"To: {to_name}", font=font_large), padding)
    # From in bottom-left
    from_pos = (padding, base.height - padding - 50)
    # Message box
    message_top = padding + 100
    message_bottom = base.height - padding - 100
    message_left = padding + 20
    message_right = base.width - padding - 20
    message_width = message_right - message_left

    # Draw To
    draw.text(to_pos, f"To: {to_name}", fill="black", font=font_large)

    # Draw From
    draw.text(from_pos, f"From: {from_name}", fill="black", font=font_large)

    # Wrap message
    wrapper = textwrap.TextWrapper(width=40)
    lines = wrapper.wrap(text=message)

    # Draw message
    current_y = message_top
    line_spacing = 50
    for line in lines:
        draw.text((message_left, current_y), line, fill="black", font=font_medium)
        current_y += line_spacing
        if current_y + line_spacing > message_bottom:
            break  # stop if message overflows

    return base

def send_postcard_email(image_bytes):
    """Send postcard via Resend API with attachment"""
    import base64
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
            postcard_image = create_postcard(to_name, from_name, message)
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
