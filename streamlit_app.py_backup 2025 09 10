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
# Modified to store file URI and upload timestamp
if "uploaded_files_metadata" not in st.session_state:
    st.session_state.uploaded_files_metadata = {"tier2": None, "tier3": None}
if "last_request_time" not in st.session_state:
    st.session_state.last_request_time = None
if "request_count" not in st.session_state:
    st.session_state.request_count = 0

# Rate limiting configuration
MIN_REQUEST_INTERVAL = 65  # 65 seconds between requests to be safe
MAX_RETRIES = 3
RETRY_DELAY = 70  # 70 seconds between retries
FILE_UPLOAD_EXPIRY_MINUTES = 10 # Custom expiry time for uploaded files

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

def is_file_expired(upload_timestamp):
    """Check if the uploaded file has expired based on FILE_UPLOAD_EXPIRY_MINUTES"""
    if upload_timestamp is None:
        return True
    return datetime.now() - upload_timestamp > timedelta(minutes=FILE_UPLOAD_EXPIRY_MINUTES)

def handle_file_upload(uploaded_file, file_key):
    """
    Uploads a file to Gemini API if it's new, expired, or the first upload.
    Returns the file object (URI) and its upload timestamp, or None if not uploaded.
    """
    if uploaded_file is None:
        return None, None

    current_file_metadata = st.session_state.uploaded_files_metadata.get(file_key)
    file_uri = None
    upload_timestamp = None

    if current_file_metadata and not is_file_expired(current_file_metadata.get("timestamp")):
        # File exists and is not expired, reuse it
        file_uri = current_file_metadata.get("uri")
        upload_timestamp = current_file_metadata.get("timestamp")
        st.session_state.debug.append(f"Reusing existing file URI for {file_key}.")
    else:
        # File is new, expired, or first upload, attempt to upload
        try:
            st.session_state.debug.append(f"Attempting to upload file for {file_key}...")
            genai_file = genai.upload_file(uploaded_file, mime_type="application/pdf")
            file_uri = genai_file.uri
            upload_timestamp = datetime.now()
            st.session_state.uploaded_files_metadata[file_key] = {
                "uri": file_uri,
                "timestamp": upload_timestamp
            }
            st.session_state.debug.append(f"File {file_key} uploaded successfully. URI: {file_uri}")
            st.success(f"✅ {file_key.capitalize()} Intervention Grid uploaded successfully!")
            st.session_state.pdf_uploaded = True # Mark as uploaded
        except Exception as e:
            st.error(f"Error uploading {file_key} document: {str(e)}")
            st.session_state.debug.append(f"Error uploading {file_key}: {str(e)}")
            # Clear potentially stale metadata if upload fails
            st.session_state.uploaded_files_metadata[file_key] = None
            st.session_state.pdf_uploaded = False
    return file_uri, upload_timestamp

def make_api_request(chat_session, prompt_message, files_to_send=None):
    """Make an API request with rate limiting and retry logic, including file references."""
    for attempt in range(MAX_RETRIES):
        try:
            # Check rate limit before any API interaction
            if not can_make_request():
                wait_time = get_wait_time()
                st.warning(f"⏱️ Rate limit protection: Please wait {int(wait_time)} seconds before making another request.")
                return None

            # Prepare content for the API call
            content = []
            if files_to_send:
                for file_info in files_to_send.values():
                    if file_info and file_info.get("uri"):
                        # Referencing the uploaded file by its URI
                        content.append(file_info["uri"])
                        st.session_state.debug.append(f"Adding file URI to prompt: {file_info['uri']}")

            content.append(prompt_message)

            # Send the actual message with potential file references
            response = chat_session.send_message(content)
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
                    st.session_state.debug.append("MAX_RETRIES exceeded for rate limit error.")
                    return None
            else:
                st.error(f"API Error: {error_str}")
                st.session_state.debug.append(f"API error: {error_str}")
                return None

    return None # Should not be reached if MAX_RETRIES > 0, but good practice

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

    tier2_pdf_uploader = st.file_uploader("Upload Tier 2 (Secondary) Interventions:", type=["pdf"], key="tier2_uploader")
    tier3_pdf_uploader = st.file_uploader("Upload Tier 3 (Tertiary) Interventions:", type=["pdf"], key="tier3_uploader")

    # Process uploads using the new handler
    file2_uri, file2_ts = handle_file_upload(tier2_pdf_uploader, "tier2")
    file3_uri, file3_ts = handle_file_upload(tier3_pdf_uploader, "tier3")

    # Update the main pdf_uploaded flag based on whether we have valid URIs
    st.session_state.pdf_uploaded = (file2_uri is not None) or (file3_uri is not None)

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
            # Check if at least one file is uploaded and not expired
            has_valid_file = False
            if st.session_state.uploaded_files_metadata.get("tier2") and not is_file_expired(st.session_state.uploaded_files_metadata["tier2"].get("timestamp")):
                has_valid_file = True
            if st.session_state.uploaded_files_metadata.get("tier3") and not is_file_expired(st.session_state.uploaded_files_metadata["tier3"].get("timestamp")):
                has_valid_file = True

            if not has_valid_file:
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
        st.session_state.uploaded_files_metadata = {"tier2": None, "tier3": None} # Clear file metadata
        st.session_state.last_request_time = None
        st.session_state.request_count = 0
        st.session_state.pdf_uploaded = False # Reset upload status
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
    # Construct the prompt for analysis
    combined_prompt = f"""Using the uploaded intervention grid, please analyze the following student information:

Form Responses:
"""
    for q, a in st.session_state.form_responses.items():
        combined_prompt += f"{q}: {a}\n"

    combined_prompt += "\nPlease analyze this information against the intervention grid and suggest appropriate interventions. Provide the output as two markdown tables: one for Tier 2 Interventions and one for Tier 3 Interventions, following the exact format specified in the system instructions."

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

                # Initialize chat session with system prompt
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

        # Prepare files metadata for the API request
        files_for_api = {}
        if st.session_state.uploaded_files_metadata.get("tier2") and not is_file_expired(st.session_state.uploaded_files_metadata["tier2"].get("timestamp")):
            files_for_api["tier2"] = st.session_state.uploaded_files_metadata["tier2"]
        if st.session_state.uploaded_files_metadata.get("tier3") and not is_file_expired(st.session_state.uploaded_files_metadata["tier3"].get("timestamp")):
            files_for_api["tier3"] = st.session_state.uploaded_files_metadata["tier3"]

        # Use the new rate-limited API request function with file references
        response = make_api_request(
            st.session_state.chat_session,
            combined_prompt, # Pass the combined prompt
            files_for_api # Pass the file metadata (URI and timestamp)
        )

        if response:
            full_response = response.text
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.debug.append("Assistant response generated")
        else:
            message_placeholder.markdown("❌ Unable to generate response due to rate limiting or file processing issues. Please try again in a few minutes.")

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

            # Prepare files metadata for the API request
            files_for_api = {}
            if st.session_state.uploaded_files_metadata.get("tier2") and not is_file_expired(st.session_state.uploaded_files_metadata["tier2"].get("timestamp")):
                files_for_api["tier2"] = st.session_state.uploaded_files_metadata["tier2"]
            if st.session_state.uploaded_files_metadata.get("tier3") and not is_file_expired(st.session_state.uploaded_files_metadata["tier3"].get("timestamp")):
                files_for_api["tier3"] = st.session_state.uploaded_files_metadata["tier3"]

            # Use the new rate-limited API request function with file references
            response = make_api_request(
                st.session_state.chat_session,
                user_input, # Pass the user's input as the prompt
                files_for_api # Pass the file metadata
            )

            if response:
                full_response = response.text
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.debug.append("Assistant response generated")
            else:
                message_placeholder.markdown("❌ Unable to generate response due to rate limiting or file processing issues. Please try again in a few minutes.")

        st.rerun()

# Debug information
st.sidebar.title("Debug Info")
for debug_msg in st.session_state.debug:
    st.sidebar.text(debug_msg)
