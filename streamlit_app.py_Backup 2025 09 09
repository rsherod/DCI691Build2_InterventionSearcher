# DCI 691 Build 2 - Intervention Grid Searcher (R. Sherod, fall 2024)
import streamlit as st
import google.generativeai as genai
from PIL import Image
import io 
import time
from datetime import datetime, timedelta

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
    st.session_state.model_name = "gemini-2.0-flash"  # Changed default to flash
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
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {"tier2": None, "tier3": None}
if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = None
if "request_count" not in st.session_state:
    st.session_state.request_count = 0

# Rate limiting configuration
MIN_REQUEST_INTERVAL = 65  # 65 seconds between requests to be safe
MAX_RETRIES = 3
RETRY_DELAY = 70  # 70 seconds between retries

def can_make_request():
    """Check if enough time has passed since the last request"""
    if st.session_state.last_request_time is None:
        return True
    
    time_since_last = time.time() - st.session_state.last_request_time
    return time_since_last >= MIN_REQUEST_INTERVAL

def get_wait_time():
    """Get remaining wait time in seconds"""
    if st.session_state.last_request_time is None:
        return 0
    
    time_since_last = time.time() - st.session_state.last_request_time
    remaining = MIN_REQUEST_INTERVAL - time_since_last
    return max(0, remaining)

def make_api_request(chat_session, message, uploaded_files=None):
    """Make an API request with rate limiting and retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            # Check rate limit
            if not can_make_request():
                wait_time = get_wait_time()
                st.warning(f"⏱️ Rate limit protection: Please wait {int(wait_time)} seconds before making another request.")
                return None
            
            # Send uploaded files first if provided
            if uploaded_files:
                if uploaded_files.get("tier2"):
                    chat_session.send_message(uploaded_files["tier2"])
                    time.sleep(2)  # Small delay between file uploads
                if uploaded_files.get("tier3"):
                    chat_session.send_message(uploaded_files["tier3"])
                    time.sleep(2)
            
            # Send the actual message
            response = chat_session.send_message(message)
            st.session_state.last_request_time = time.time()
            st.session_state.request_count += 1
            st.session_state.debug.append(f"Request {st.session_state.request_count} successful")
            return response
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                st.session_state.debug.append(f"Rate limit hit on attempt {attempt + 1}")
                if attempt < MAX_RETRIES - 1:
                    st.warning(f"⏱️ Rate limit reached. Waiting {RETRY_DELAY} seconds before retry {attempt + 2}/{MAX_RETRIES}...")
                    time.sleep(RETRY_DELAY)
                else:
                    st.error("❌ Rate limit exceeded. Please wait at least 2 minutes before trying again.")
                    return None
            else:
                st.error(f"API Error: {error_str}")
                st.session_state.debug.append(f"API error: {error_str}")
                return None
    
    return None

# Display image
image_path = 'Tier 2 and Tier 3 Intervention Grid Search.jpg'
try:
    image = Image.open(image_path)
    col1, col2, col3 = st.columns([1,6,1])
    with col2:
        st.image(image, use_container_width=True)
        st.markdown("<div style='text-align: center;'><small style='color: rgb(128, 128, 128);'>Created by Rebecca Sherod (2024)</small></div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><small style='color: rgb(128, 128, 128);'>This work was supported, in part, by ASU's Mary Lou Fulton Teachers College (MLFTC). The opinions and findings expressed in this document are those of the author and do not necessarily reflect those of the funding agency.</small></div>", unsafe_allow_html=True)
except Exception as e:
    st.error(f"Error loading image: {e}")

# Title and BotDescription 
st.subheader("Welcome to the Intervention Grid Searcher!")
st.write("The goal of this bot is to help you find Tier 2 and Tier 3 Interventions from the intervention grids at your school. \n\nDirections: Use the panel on the left to upload the Tier 2 and Tier 3 Intervention Grid from your school. Then, answer the questions about the student or group of students you are interested in selecting an intervention for. When you are ready, hit 'Submit Responses' to begin the process.")
st.caption("Note: This Bot can make mistakes. Make sure you refer back to the intervention grid to determine if it is a good fit for the student or students.")

# Rate limit status indicator
if st.session_state.last_request_time:
    wait_time = get_wait_time()
    if wait_time > 0:
        st.info(f"⏱️ Rate limit cooldown: {int(wait_time)} seconds remaining")
    else:
        st.success("✅ Ready to make requests")

# Initialize Gemini client
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Sidebar for model and temperature selection
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>Settings</h1>", unsafe_allow_html=True)
    st.caption("Note: Different models have different request rate limits. Please refer to Google AI documentation for details.")
    
    model_option = st.selectbox(
        "Select Model:", ["gemini-2.0-flash", "gemini-2.0-pro-exp-02-05"],  # Reordered to have flash first
        index=0  # Default to first option (flash)
    )
    
    if model_option != st.session_state.model_name:
        st.session_state.model_name = model_option
        st.session_state.messages = []
        st.session_state.chat_session = None

    # Display current rate limit status
    st.markdown("### Rate Limit Status")
    if st.session_state.request_count > 0:
        st.write(f"Requests made: {st.session_state.request_count}")
        if st.session_state.last_request_time:
            last_request = datetime.fromtimestamp(st.session_state.last_request_time)
            st.write(f"Last request: {last_request.strftime('%H:%M:%S')}")
            wait_time = get_wait_time()
            if wait_time > 0:
                st.write(f"⏱️ Cooldown: {int(wait_time)}s")
            else:
                st.write("✅ Ready")

    # File upload section
    st.markdown("<h1 style='text-align: center;'>Upload Intervention Grid</h1>", unsafe_allow_html=True)
    st.subheader("Upload Your Intervention Documents")
    st.caption("Note: If your school has separate documents for Tier 2 and Tier 3 interventions, you can upload both. If you have a single combined document, you can upload it to either field.")
    
    tier2_pdf = st.file_uploader("Upload Tier 2 (Secondary) Interventions:", type=["pdf"])
    tier3_pdf = st.file_uploader("Upload Tier 3 (Tertiary) Interventions:", type=["pdf"])

    upload_success = False
    
    # Process Tier 2 document
    if tier2_pdf:
        try:
            tier2_file = genai.upload_file(tier2_pdf, mime_type="application/pdf")
            st.session_state.uploaded_files["tier2"] = tier2_file
            upload_success = True
        except Exception as e:
            st.error(f"Error uploading Tier 2 document: {str(e)}")
            st.session_state.debug.append(f"Tier 2 upload error: {str(e)}")

    # Process Tier 3 document
    if tier3_pdf:
        try:
            tier3_file = genai.upload_file(tier3_pdf, mime_type="application/pdf")
            st.session_state.uploaded_files["tier3"] = tier3_file
            upload_success = True
        except Exception as e:
            st.error(f"Error uploading Tier 3 document: {str(e)}")
            st.session_state.debug.append(f"Tier 3 upload error: {str(e)}")

    if upload_success:
        st.session_state.pdf_uploaded = True
        st.success("✅ Intervention Grid(s) uploaded successfully!")
        st.session_state.debug.append("PDF(s) uploaded and stored in session state")
    
    # Student Information Form
    st.markdown("<h1 style='text-align: center;'>Student Information</h1>", unsafe_allow_html=True)

    if 'form_responses' not in st.session_state:
        st.session_state.form_responses = {}

    with st.form("user_form"):
        st.session_state.form_responses['Academic_read'] = st.selectbox(
            "Student <b>Reading</b> Performance:", 
            options=["Click to select", "below average", "average", "above average"], 
            key="Academic_read"
        )

        st.session_state.form_responses['Academic_math'] = st.selectbox(
            "Student Math Performance:", 
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
            elif not can_make_request():
                wait_time = get_wait_time()
                st.error(f"⏱️ Please wait {int(wait_time)} seconds before submitting (rate limit protection)")
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
        st.session_state.uploaded_files = {"tier2": None, "tier3": None}
        st.session_state.last_request_time = None
        st.session_state.request_count = 0
        st.success("Chat cleared!")
        st.experimental_rerun()

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

            # Use the new rate-limited API request function
            response = make_api_request(
                st.session_state.chat_session, 
                current_message["content"], 
                st.session_state.uploaded_files
            )
            
            if response:
                full_response = response.text
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.debug.append("Assistant response generated")
            else:
                message_placeholder.markdown("❌ Unable to generate response due to rate limiting. Please try again in a few minutes.")

        st.session_state.should_generate_response = False
        st.rerun()

# User input handling
user_input = st.chat_input("Type here:")

if user_input:
    if not can_make_request():
        wait_time = get_wait_time()
        st.error(f"⏱️ Please wait {int(wait_time)} seconds before sending another message (rate limit protection)")
    else:
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

            # Use the new rate-limited API request function
            response = make_api_request(st.session_state.chat_session, user_input)
            
            if response:
                full_response = response.text
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.debug.append("Assistant response generated")
            else:
                message_placeholder.markdown("❌ Unable to generate response due to rate limiting. Please try again in a few minutes.")

        st.rerun()

# Debug information
st.sidebar.title("Debug Info")
for debug_msg in st.session_state.debug:
    st.sidebar.text(debug_msg)
