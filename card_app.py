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

# Streamlit background beige
st.markdown(
    """
    <style>
    .stApp {
        background-color: #F5F0E1;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("📮 Send a Postcard")

# ---------------- Inputs ----------------
to_name = st.text_input("To")
from_name = st.text_input("From")
message_input = st.text_area("Message", max_chars=500)
receiver_email = st.text_input("Recipient Email")

# ---------------- Helpers ----------------
def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def create_postcard_high_res_small_canvas(to_name, from_name, message):
    """
    Create postcard with smaller canvas (500x400) but crisp, big text using Patrick font.
    """
    # ---------------- High-res rendering ----------------
    scale = 4  # render 4x bigger internally
    width, height = 50*scale, 40*scale
    base = Image.new("RGBA", (width, height), (245, 240, 225))  # beige background
    draw = ImageDraw.Draw(base)
    padding = 20 * scale

    # Brown border
    draw.rectangle([0,0,width-1,height-1], outline=(139,94,60), width=10*scale)

    # ---------------- Load Patrick font ----------------
    try:
        font_to = ImageFont.truetype("Patrick.ttf", 10*scale)
        font_from = ImageFont.truetype("Patrick.ttf", 10*scale)
        font_message = ImageFont.truetype("Patrick.ttf", 8*scale)
        font_stamp = ImageFont.truetype("Patrick.ttf", 5*scale)
    except:
        font_to = font_from = font_message = font_stamp = ImageFont.load_default()

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
    message_text = f"Message: {message}"
    msg_bbox = draw.textbbox((0,0), message_text, font=font_message)
    msg_width = msg_bbox[2] - msg_bbox[0]
    msg_height = msg_bbox[3] - msg_bbox[1]
    msg_x = width - padding - msg_width
    msg_y = height - padding - msg_height - 30*scale  # slightly above bottom
    draw.text((msg_x, msg_y), message_text, fill=(0,0,0), font=font_message)

    # ---------------- Stamp (top-right) ----------------
    stamp_text = "STAMP"
    stamp_bbox = draw.textbbox((0,0), stamp_text, font=font_stamp)
    stamp_width = stamp_bbox[2] - stamp_bbox[0]
    draw.text((width - padding - stamp_width, padding), stamp_text, fill=(139,94,60), font=font_stamp)

    # ---------------- Downscale to final canvas ----------------
    final_width, final_height = 500, 400
    postcard_resized = base.resize((final_width, final_height), resample=Image.LANCZOS)

    return postcard_resized

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
    if not all([to_name, from_name, message_input, receiver_email]):
        st.error("Please fill all fields")
    elif not is_valid_email(receiver_email):
        st.error("Invalid email address")
    else:
        try:
            # Generate postcard
            postcard_image = create_postcard_high_res_small_canvas(to_name, from_name, message_input)

            # Show preview
            st.image(postcard_image,width = 500)

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
