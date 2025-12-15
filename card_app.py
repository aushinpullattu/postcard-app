import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import textwrap
import io

# ----------------------------
# Constants
# ----------------------------
TEMPLATE_PATH = "postcard_template.png"
FONT_PATH = "fonts/PatrickHand-Regular.ttf"

# ----------------------------
# Postcard generator function
# ----------------------------
def generate_postcard(to_name, from_name, message):
    img = Image.open(TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Load custom fonts
    font_to = ImageFont.truetype(FONT_PATH, 46)
    font_msg = ImageFont.truetype(FONT_PATH, 34)
    font_from = ImageFont.truetype(FONT_PATH, 42)

    text_color = "#4a4a4a"

    # -------- Positions (tuned for your template) --------
    to_position = (900, 420)         # Right side, top
    message_position = (900, 500)    # Right side, middle
    from_position = (250, 850)       # Left side, bottom

    # Draw "To"
    draw.text(to_position, f"to: {to_name}", fill=text_color, font=font_to)

    # Wrap message for multiline text
    wrapped_message = textwrap.fill(message, width=28)
    draw.multiline_text(
        message_position,
        wrapped_message,
        fill=text_color,
        font=font_msg,
        spacing=10
    )

    # Draw "From"
    draw.text(from_position, f"from: {from_name}", fill=text_color, font=font_from)

    return img

# ----------------------------
# Streamlit app
# ----------------------------
st.title("💌 Custom Postcard Generator")

# User inputs
to_name = st.text_input("To")
from_name = st.text_input("From")
message = st.text_area("Message", height=150)

if st.button("Generate Postcard"):
    if not to_name or not from_name or not message:
        st.warning("Please fill in all fields!")
    else:
        postcard_img = generate_postcard(to_name, from_name, message)
        st.image(postcard_img, caption="Your cute postcard!", use_column_width=True)

        # Provide download
        buf = io.BytesIO()
        postcard_img.save(buf, format="PNG")
        byte_im = buf.getvalue()
        st.download_button(
            label="📥 Download Postcard",
            data=byte_im,
            file_name="postcard.png",
            mime="image/png"
        )
