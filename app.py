import json

import streamlit as st
from google import genai
from google.genai import types
from twilio.rest import Client as TwilioClient

from prompts import SUMMARY_REQUEST_PROMPT, SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE

MODEL_NAME = "gemini-3.5-flash"
st.set_page_config(page_title="Plani Helper", page_icon="🍀", layout="centered")

# Retrieve secrets safely
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TWILIO_ACCOUNT_SID = st.secrets.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = st.secrets.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = st.secrets.get("TWILIO_WHATSAPP_FROM", "")
TWILIO_CONTENT_SID = st.secrets.get("TWILIO_CONTENT_SID", "")

if not GEMINI_API_KEY:
    st.error(
        "Missing `GEMINI_API_KEY`!\n\n"
        "- **If deploying on Streamlit Cloud:** Open **App Settings → Secrets** in your Streamlit Cloud dashboard and paste your secrets.\n"
        "- **If running locally:** Add your key to `.streamlit/secrets.toml`."
    )
    st.stop()


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


@st.cache_resource
def get_twilio_client():
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
        try:
            return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        except Exception:
            return None
    return None


gemini_client = get_gemini_client()
twilio_client = get_twilio_client()


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])


def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text
    except Exception as error:
        return f"Sorry, something went wrong: {error}"


def clean_whatsapp_text(text):
    if not text:
        return "No summary available."
    text = " ".join(text.split())  # collapse whitespace/newlines
    return text[:1500] + "..." if len(text) > 1500 else text


def send_whatsapp(to_number, user_name, summary):
    if not twilio_client or not TWILIO_WHATSAPP_FROM or not TWILIO_CONTENT_SID:
        return False, "Twilio WhatsApp credentials not configured."
    # Content template expects {{1}} = name, {{2}} = summary.
    try:
        content_variables = json.dumps(
            {"1": user_name, "2": clean_whatsapp_text(summary)}, ensure_ascii=False
        )
        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            content_sid=TWILIO_CONTENT_SID,
            content_variables=content_variables,
        )
        return True, message.sid
    except Exception as error:
        return False, str(error)


# Step 1: Onboarding
if "onboarded" not in st.session_state:
    st.title("🍀 Plani Helper")
    st.caption("Find, care for, and understand your plants and animals.")
    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        whatsapp_number = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
            help="We'll text you updates, tips, and reminders.",
        )
        submitted = st.form_submit_button("Take Flight 🍀")
    if submitted:
        if not name.strip() or not whatsapp_number.strip():
            st.warning("Please fill in both your name and WhatsApp number.")
        else:
            st.session_state.name = name.strip()
            st.session_state.whatsapp_number = whatsapp_number.strip()
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()
    st.stop()

# Step 2: Chat Interface
header_col, button_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("🍀 Plani Helper")

with button_col:
    has_twilio = bool(twilio_client and TWILIO_WHATSAPP_FROM and TWILIO_CONTENT_SID)
    send_disabled = len(st.session_state.messages) <= 2
    if st.button("📤 Send to WhatsApp", disabled=send_disabled, use_container_width=True):
        if not has_twilio:
            st.warning(
                "Twilio WhatsApp is not configured. "
                "Please add `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM`, "
                "and `TWILIO_CONTENT_SID` to your secrets to enable WhatsApp sending."
            )
        else:
            with st.spinner("Summarizing your consultation..."):
                summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
            success, info = send_whatsapp(st.session_state.whatsapp_number, st.session_state.name, summary)
            if success:
                st.success("Sent! Check your WhatsApp 📲")
            else:
                st.error(f"Couldn't send that: {info}")

st.caption(f"Logged in as **{st.session_state.name}** — updates go to `{st.session_state.whatsapp_number}`")

if not st.session_state.messages:
    welcome_text = WELCOME_MESSAGE_TEMPLATE
    try:
        welcome_text = WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name)
    except Exception:
        pass
    add_message("assistant", "text", welcome_text)
else:
    for message in st.session_state.messages:
        render_message(message)

user_input = st.chat_input(
    "Ask a question, or attach a photo of your plant or animal",
    accept_file=True,
    file_type=["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append("What is this plant/animal? Give me the care and diagnosis tips.")

    with st.spinner("Analyzing with Gemini..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)
