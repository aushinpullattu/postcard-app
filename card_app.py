import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import re
import requests

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

def create_dynamic_postcard(to_name, from_name, message):
    # Load your uploaded postcard template
    template_path = "postcard-template.png"
    postcard = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(postcard)

    # Fonts
    try:
        font_large = ImageFont.truetype("arial.ttf", 36)
        font_medium = ImageFont.truetype("arial.ttf", 28)
    except:
        font_large = font_medium = ImageFont.load_default()

    # Positions (adjust these based on your template)
    to_pos = (120, 50)
    from_pos = (120, postcard.height - 100)
    message_pos = (50, 150)
    message_max_width = 400

    # Draw To
    draw.text(to_pos, f"To: {to_name}", fill="black", font=font_large)

    # Draw From
    draw.text(from_pos, f"From: {from_name}", fill="black", font=font_large)

    # Draw Message with wrapping
    lines = []
    words = message.split()
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        bbox = draw.textbbox((0,0), test_line, font=font_medium)
        if bbox[2] <= message_max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    lines.append(line)

    for i, line in enumerate(lines):
        draw.text((message_pos[0], message_pos[1] + i*35), line, fill="black", font=font_medium)

    return postcard

def send_postcard_email(image_bytes):
    """Example placeholder for sending email"""
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
        # Attachments need proper API support
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
            # Generate postcard dynamically
            postcard_image = create_dynamic_postcard(to_name, from_name, message)

            # Show postcard preview in Streamlit
            st.image(postcard_image, use_container_width=True)

            # Convert to bytes for sending email
            img_bytes = io.BytesIO()
            postcard_image.save(img_bytes, format="PNG")
            img_bytes.seek(0)

            # Send postcard (attach image if API supports)
            send_postcard_email(img_bytes)

            st.success("Postcard generated and sent 💖")
        except Exception as e:
            st.error(f"Something went wrong: {e}")
