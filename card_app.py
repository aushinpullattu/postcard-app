import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import requests
import re
import io

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

def create_postcard_image(to_name, from_name, message):
    # Open postcard template
    postcard = Image.open("postcard_template.png").convert("RGB")
    draw = ImageDraw.Draw(postcard)

    # Optional: Use a custom font
    try:
        font = ImageFont.truetype("arial.ttf", size=30)
        font_small = ImageFont.truetype("arial.ttf", size=24)
    except:
        font = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Define positions
    to_position = (50, 50)
    from_position = (50, postcard.height - 100)
    message_position = (50, 150)

    # Draw text
    draw.text(to_position, f"To: {to_name}", fill="black", font=font)
    
    # Split message into multiple lines if too long
    max_width = postcard.width - 100
    lines = []
    words = message.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        w, _ = draw.textsize(test_line, font=font_small)
        if w <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    for i, line in enumerate(lines):
        draw.text((message_position[0], message_position[1] + i * 30), line, fill="black", font=font_small)

    draw.text(from_position, f"From: {from_name}", fill="black", font=font)

    return postcard

def send_postcard_email(image_bytes):
    url = "https://api.resend.com/emails"
    headers = {
        "Authorization": f"Bearer {st.secrets['RESEND_API_KEY']}",
        "Content-Type": "application/json",
    }

    html = f"""
    <h2>💌 You received a postcard</h2>
    <p>See your postcard attached!</p>
    <img src="cid:postcard_image" alt="Postcard" />
    """

    data = {
        "from": "Postcard <onboarding@resend.dev>",
        "to": [receiver_email],
        "subject": "You received a postcard 💌",
        "html": html,
        # Normally you'd send attachments via proper API method; this is just a placeholder
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
            # Create postcard image with text
            postcard_image = create_postcard_image(to_name, from_name, message)

            # Show postcard in Streamlit
            st.image(postcard_image, use_container_width=True)

            # Optionally: convert to bytes to send via email
            img_bytes = io.BytesIO()
            postcard_image.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Send email (with image if your API supports attachments)
            send_postcard_email(img_bytes)

            st.success("Postcard sent 💖")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
