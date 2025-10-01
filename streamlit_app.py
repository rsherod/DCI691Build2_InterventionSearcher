# DCI 691 Build 2 - Intervention Grid Searcher (R. Sherod, fall 2024)
import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
from io import BytesIO
import json
import os
import uuid
import datetime

# Streamlit configuration
st.set_page_config(page_title="Streamlit Chatbot", layout="wide")

# Initialize all session state variables
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "form_responses" not in st.session_state:
    st.session_state.form_responses = {}
if "should_generate_response" not in st.session_state:
    st.session_state.should_generate_response = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "model_name" not in st.session_state:
    st.session_state.model_name = "gemini-2.0-flash"
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.5
if "debug" not in st.session_state:
    st.session_state.debug = []
if "pdf_content" not in st.session_state:
    st.session_state.pdf_content = ""
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "sample_tier2_loaded" not in st.session_state:
    st.session_state.sample_tier2_loaded = False
if "sample_tier2_name" not in st.session_state:
    st.session_state.sample_tier2_name = ""

if "session_id" not in st.session_state:
    # One ID per chat session—this will be the Firestore doc id
    st.session_state.session_id = str(uuid.uuid4())
if "firestore_inited" not in st.session_state:
    st.session_state.firestore_inited = False
if "firestore_doc_ref" not in st.session_state:
    st.session_state.firestore_doc_ref = None

##############################
# Firestore (Firebase) setup #
##############################
# This will NOT change bot behavior; it just enables saving.
try:
    # Lazy import so it’s easy to remove if needed
    import firebase_admin
    from firebase_admin import credentials, firestore as fb_firestore

    if not st.session_state.firestore_inited:
        # Prefer a service account passed via Streamlit secrets.
        # Add your JSON under: st.secrets["FIREBASE_SERVICE_ACCOUNT"]
        # Minimal keys used: project_id, client_email, private_key
        if "FIREBASE_SERVICE_ACCOUNT" in st.secrets:
            sa_info = dict(st.secrets["FIREBASE_SERVICE_ACCOUNT"])
            # Fix escaped newlines in private_key if necessary
            if "private_key" in sa_info and "\\n" in sa_info["private_key"]:
                sa_info["private_key"] = sa_info["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(sa_info)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
        else:
            # Fall back to Application Default Credentials (e.g., if deployed on GCP)
            if not firebase_admin._apps:
                firebase_admin.initialize_app()

        db = fb_firestore.client()
        # Collection name: "chat_sessions" (change if you like)
        st.session_state.firestore_doc_ref = db.collection("chat_sessions").document(st.session_state.session_id)
        st.session_state.firestore_inited = True
except Exception as _firebase_e:
    # If Firebase isn’t configured, we silently skip—bot still runs.
    st.session_state.firestore_inited = False
    st.session_state.firestore_doc_ref = None

def _messages_to_transcript(messages: list) -> str:
    """
    Convert entire conversation into a single-line-friendly string.
    Keeps everything in one Firestore document field.
    """
    # Timestamp header (ISO 8601, local time not required)
    ts = datetime.datetime.utcnow().isoformat() + "Z"
    lines = [f"[transcript_saved_at_utc={ts}]"]
    for m in messages:
        role = m.get("role", "unknown")
        # Ensure we only store text content
        content = str(m.get("content", "")).replace("\r", " ").replace("\n", " ").strip()
        lines.append(f"{role}: {content}")
    # Join with a single space to keep it “one line”; Firestore stores it as a single string field
    return " ".join(lines)

def _messages_to_turns(messages: list) -> list:
    """
    Flat list of turns so Firestore shows one element per message.
    Example: [{i, role, content}, ...]
    """
    turns = []
    for i, m in enumerate(messages, start=1):
        turns.append({
            "i": i,
            "role": m.get("role", "unknown"),
            "content": str(m.get("content", "")),
        })
    return turns

def _messages_to_exchanges(messages: list) -> list:
    """
    Group messages into user→assistant pairs for easier reading.
    Example: [{"user": "...", "assistant": "..."}, ...]
    """
    exchanges = []
    current = None
    for m in messages:
        role = m.get("role", "")
        text = str(m.get("content", ""))
        if role == "user":
            current = {"user": text, "assistant": None}
            exchanges.append(current)
        elif role == "assistant":
            if current and current.get("assistant") is None:
                current["assistant"] = text
            else:
                exchanges.append({"user": None, "assistant": text})
        else:
            exchanges.append({"user": None, "assistant": None})
    return exchanges

def save_chat_to_firestore():
    """
    Writes the entire chat to a single Firestore document (one row).
    Safe no-op if Firestore isn’t configured.
    """
    try:
        if not st.session_state.firestore_doc_ref:
            return
        payload = {
            "session_id": st.session_state.session_id,
            "model_name": st.session_state.get("model_name", None),
            "transcript": _messages_to_transcript(st.session_state.get("messages", [])),
            # NEW: structured fields for readable, line-by-line viewing
            "turns": _messages_to_turns(st.session_state.get("messages", [])),
            "exchanges": _messages_to_exchanges(st.session_state.get("messages", [])),            
            "message_count": len(st.session_state.get("messages", [])),
            "saved_at_utc": datetime.datetime.utcnow()
        }
        # set() creates or overwrites the single document for this session id
        st.session_state.firestore_doc_ref.set(payload)
    except Exception as _save_e:
        # Don’t surface any Firestore issues to users
        pass

# Center the entire main content area on large screens and give it a comfy max width
st.markdown("""
    <style>
      /* Centers the main block container within the viewport when layout='wide' */
      .block-container {
        max-width: 1200px;   /* tweak 1100–1300 if you like */
        margin-left: auto !important;
        margin-right: auto !important;
      }
    </style>
""", unsafe_allow_html=True)

# Display image
image_path = 'Tier 2 and Tier 3 Intervention Grid Search.jpg'
try:
    image = Image.open(image_path)
    # Use a 3-column layout and place the image in the center column
    _left, center, _right = st.columns([1, 2, 1])
    with center:
        st.image(image, width=900)
    st.markdown("<div style='text-align: center;'><small style='color: rgb(128, 128, 128);'>Created by Rebecca Sherod (2024)</small></div>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center;'><small style='color: rgb(128, 128, 128);'>This work was supported, in part, by ASU's Mary Lou Fulton Teachers College (MLFTC). The opinions and findings expressed in this document are those of the author and do not necessarily reflect those of the funding agency. This bot was funded in part by Project EPIC (USDE, OSEP Award Number: H325D220011).</small></div>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error loading image: {e}")

# Title and BotDescription 
st.subheader("Welcome to the Intervention Grid Searcher!")
st.write("The goal of this bot is to help you find Tier 2 and Tier 3 Interventions from the intervention grids at your school. \n\nDirections: Use the panel on the left to upload the Tier 2 and/or Tier 3 Intervention Grid from your school. Then, select options from the drop-down menu that best describe the student or group of students you are interested in selecting an intervention for. When you are ready, hit 'Submit Responses' and the bot will provide a table with the name and description of the interventions from your intervention grid that might be a good fit.")
st.caption("Note: This bot is not designed to receive any identifiable information. This Bot can make mistakes. Make sure you refer back to the intervention grid to determine if it is a good fit for the student or students.")

# Initialize Gemini client
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# -------- Always-use-JSON preload (no file upload to Gemini) --------
SAMPLE_TIER2_JSON = "sample_tier2.json"
try:
    if not st.session_state.sample_tier2_loaded:
        if os.path.exists(SAMPLE_TIER2_JSON):
            with open(SAMPLE_TIER2_JSON, "r", encoding="utf-8") as jf:
                data = json.load(jf)
            # Join page texts (fallback to whole file if structure differs)
            pages = data.get("pages")
            if isinstance(pages, list):
                st.session_state.pdf_content = "\n\n".join(p.get("text", "") for p in pages)
            else:
                st.session_state.pdf_content = json.dumps(data, ensure_ascii=False, indent=2)
            st.session_state.uploaded_file = None
            st.session_state.pdf_uploaded = True
            st.session_state.sample_tier2_loaded = True
            st.session_state.sample_tier2_name = SAMPLE_TIER2_JSON
            st.session_state.debug.append("Sample Tier 2 loaded from JSON")
        else:
            st.warning("Sample Tier 2 JSON not found. Add 'sample_tier2.json' to the repo root.")
except Exception as e:
    st.error(f"Error loading sample Tier 2 JSON: {e}")
    st.session_state.debug.append(f"Sample JSON load error: {e}")

# Sidebar for model and temperature selection
with st.sidebar:

    # File upload section - show Tier 2 and Tier 3 slots, but DISABLED
    st.markdown("<h1 style='text-align: center;'>Upload Intervention Grid</h1>", unsafe_allow_html=True)

    # Match the screenshot: caption above, no bold label on the uploader
    st.caption("Upload Tier 2 or Tier 3 Intervention Grid:")
    st.file_uploader("Tier 2 or Tier 3 Intervention Grid (disabled)",
                     type=["pdf"], disabled=True, key="tier2_disabled_slot",
                     label_visibility="collapsed")
    if st.session_state.sample_tier2_loaded:
        st.success("✅ A Tier 2 Intervention Grid has already been uploaded.")
    else:
        st.info("No sample detected.")

    
    # Student Information Form
    st.markdown("<h1 style='text-align: center;'>Student Information</h1>", unsafe_allow_html=True)

    if 'form_responses' not in st.session_state:
        st.session_state.form_responses = {}

    with st.form("user_form"):
        st.session_state.form_responses['Academic_read'] = st.selectbox(
            "Reading Performance:", 
            options=["Click to select", "below average", "average", "above average"], 
            key="Academic_read"
        )

        st.session_state.form_responses['Academic_math'] = st.selectbox(
            "Math Performance:", 
            options=["Click to select", "below average", "average", "above average"], 
            key="Academic_math"
        )

        st.session_state.form_responses['SRSS_I'] = st.selectbox(
            "SRSS-Internalizing Score:", 
            options=["Click to select", "Low", "Moderate", "High"], 
            key="SRSS_I"
        )

        st.session_state.form_responses['SRSS_E'] = st.selectbox(
            "SRSS-Externalizing Score:", 
            options=["Click to select", "Low", "Moderate", "High"], 
            key="SRSS_E"
        )

        st.session_state.form_responses['Days_missed'] = st.selectbox(
            "Number of Days Student has Missed:", 
            options=["Click to select", "0-5 days", "6-10 days", "11-15 days", "16+ days"], 
            key="Days_missed"
        )

        st.session_state.form_responses['ODRs'] = st.selectbox(
            "Number of Office Discipline Referrals Earned:", 
            options=["Click to select", "0-1 referrals", "2-3 referrals", "4-5 referrals", "6+ referrals"], 
            key="ODRs"
        )

        submit_button = st.form_submit_button("Submit Responses")
        if submit_button:
            if not st.session_state.pdf_uploaded:
                st.error("Please upload the Intervention Grid first before submitting the form.")
            else:
                st.session_state.form_submitted = True
                st.session_state.should_generate_response = True
                st.success("Thank you! Your responses have been recorded.")
    
    # Clear chat functionality
    clear_button = st.button("Clear Chat")
    if clear_button:
        st.session_state.messages = []
        st.session_state.debug = []
        st.session_state.chat_session = None
        st.session_state.pdf_uploaded = False
        st.session_state.uploaded_file = None
        # OPTIONAL: start a brand-new Firestore document for the next chat
        st.session_state.session_id = str(uuid.uuid4())
        try:
            # Re-point the doc ref to the new session id
            st.session_state.firestore_doc_ref = fb_firestore.client()\
                .collection("chat_sessions")\
                .document(st.session_state.session_id)
        except Exception:
            # If Firestore isn't configured, silently continue
            pass        
        st.success("Chat cleared!")
        st.rerun()

# Load system prompt
def load_text_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        st.error(f"Error loading text file: {e}")
        return ""

system_prompt = load_text_file('instructions.txt')

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle form submission and generate response
if st.session_state.should_generate_response:
    if not st.session_state.pdf_uploaded:
        st.error("Please upload the intervention grid first.")
        st.session_state.should_generate_response = False
        st.rerun()
    else:    
        combined_prompt = f"""Using the uploaded intervention grid, please analyze the following student information:

Form Responses:
"""
        for q, a in st.session_state.form_responses.items():
            combined_prompt += f"{q}: {a}\n"
        
        combined_prompt += "\nPlease analyze this information against the intervention grid and suggest appropriate interventions."
    
        current_message = {"role": "user", "content": combined_prompt}
        st.session_state.messages.append(current_message)

        with st.chat_message("user"):
            st.markdown(current_message["content"])

        with st.chat_message("assistant"):
            message_placeholder = st.empty()

            if st.session_state.chat_session is None:
                try:
                    generation_config = {
                        "temperature": st.session_state.temperature,
                        "top_p": 0.95,
                        "top_k": 40,
                        "max_output_tokens": 4096,
                    }
                    model = genai.GenerativeModel(
                        model_name=st.session_state.model_name,
                        generation_config=generation_config,
                    )
                    
                    initial_messages = [
                        {"role": "user", "parts": [f"System: {system_prompt}"]},
                        {"role": "model", "parts": ["Understood. I will follow these instructions."]},
                    ]
                    
                    st.session_state.chat_session = model.start_chat(history=initial_messages)
                    st.session_state.debug.append("Chat session initialized successfully")
                except Exception as e:
                    st.error(f"Error initializing chat session: {str(e)}")
                    st.session_state.debug.append(f"Chat initialization error: {str(e)}")
                    st.stop()

            try:
                # Combine PDF and prompt into a single message to reduce API calls
                parts = []
                # Always include JSON text of the grid (no PDF)
                if st.session_state.get("pdf_content"):
                    parts.append("Intervention Grid (text extract):\n" + st.session_state.pdf_content)
                parts.append(current_message["content"])
                
                # Send everything in one API call
                response = st.session_state.chat_session.send_message(parts)
                full_response = response.text
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.debug.append("Assistant response generated")
                # Save the entire conversation snapshot to Firestore (keep this INSIDE the try)
                save_chat_to_firestore()                
            except Exception as e:
                st.error(f"An error occurred while generating the response: {str(e)}")
                st.session_state.debug.append(f"Error: {str(e)}")

        st.session_state.should_generate_response = False
        st.rerun()

# User input handling
user_input = st.chat_input("Type here:")

if user_input:
    current_message = {"role": "user", "content": user_input}
    st.session_state.messages.append(current_message)

    with st.chat_message("user"):
        st.markdown(current_message["content"])

    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        if st.session_state.chat_session is None:
            try:
                generation_config = {
                    "temperature": st.session_state.temperature,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 4096,
                }
                model = genai.GenerativeModel(
                    model_name=st.session_state.model_name,
                    generation_config=generation_config,
                )
                
                initial_messages = [
                    {"role": "user", "parts": [f"System: {system_prompt}"]},
                    {"role": "model", "parts": ["Understood. I will follow these instructions."]},
                ]
                
                st.session_state.chat_session = model.start_chat(history=initial_messages)
                st.session_state.debug.append("Chat session initialized successfully")
            except Exception as e:
                st.error(f"Error initializing chat session: {str(e)}")
                st.session_state.debug.append(f"Chat initialization error: {str(e)}")
                st.stop()

        try:
            # Include JSON grid text with ad-hoc user messages as well
            parts = []
            if st.session_state.get("pdf_content"):
                parts.append("Intervention Grid (text extract):\n" + st.session_state.pdf_content)
            parts.append(user_input)
            response = st.session_state.chat_session.send_message(parts)
            full_response = response.text
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.debug.append("Assistant response generated")
            # Save the entire conversation snapshot to Firestore (keep this INSIDE the try)
            save_chat_to_firestore()            
        except Exception as e:
            st.error(f"An error occurred while generating the response: {str(e)}")
            st.session_state.debug.append(f"Error: {str(e)}")

    st.rerun()

# Debug information
#st.sidebar.title("Debug Info")
#for debug_msg in st.session_state.debug:
#    st.sidebar.text(debug_msg)
