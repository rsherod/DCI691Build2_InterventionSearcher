# DCI 691 Build 2 - Intervention Grid Searcher (R. Sherod, fall 2024)
import streamlit as st
import google.generativeai as genai
from PIL import Image

# Streamlit configuration
st.set_page_config(page_title="Streamlit Chatbot", layout="wide")

# Add this code between st.set_page_config(page_title="Streamlit Chatbot", layout="wide") and Display image code block
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "form_responses" not in st.session_state:
    st.session_state.form_responses = {}
if "should_generate_response" not in st.session_state:
    st.session_state.should_generate_response = False

# Display image
# This code attempts to open and display an image file named 'Build2.png'.
# If successful, it shows the image with a caption. If there's an error, it displays an error message instead.
# You can customize this by changing the image file name and path. Supported image types include .png, .jpg, .jpeg, and .gif.
# To use a different image, replace 'Build2.png' with your desired image file name (e.g., 'my_custom_image.jpg').
image_path = 'Tier 2 and Tier 3 Intervention Grid Search.jpg'
try:
    image = Image.open(image_path)
    st.image(image, caption='Created by Rebecca Sherod (2024)', use_column_width=True)
except Exception as e:
    st.error(f"Error loading image: {e}")

# Title and BotDescription 
# You can customize the title, description, and caption by modifying the text within the quotes.
st.title("Welcome to the Intervention Grid Searcher!")
st.write("The goal of this bot is to help you find Tier 2 and Tier 3 Interventions from the grids at your school. \n\nDirections: Use the panel on the left to upload the Tier 2 and Tier 3 Intervention Grid from your school. Then, answer the questions about the student or group of students you are interested in selecting an intervention for.")
st.caption("Note: This Bot can make mistakes. Make sure you refer back to the intervention grid to determine if it is a good fit for the student or studnets.")

# Initialize Gemini client
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "model_name" not in st.session_state:
    st.session_state.model_name = "gemini-1.5-pro-002"
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.5
if "debug" not in st.session_state:
    st.session_state.debug = []
if "pdf_content" not in st.session_state:
    st.session_state.pdf_content = ""
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

# Sidebar for model and temperature selection
with st.sidebar:
    st.title("Settings")
    st.caption("Note: Gemini-1.5-pro-002 can only handle 2 requests per minute, gemini-1.5-flash-002 can handle 15 per minute")
    model_option = st.selectbox(
        "Select Model:", ["gemini-1.5-flash-002", "gemini-1.5-pro-002"]
    )
    if model_option != st.session_state.model_name:
        st.session_state.model_name = model_option
        st.session_state.messages = []
        st.session_state.chat_session = None
    temperature = st.slider("Temperature:", 0.0, 1.0, st.session_state.temperature, 0.1)
    st.session_state.temperature = temperature

# Modify the info e.g., ['Bot_Name'] and "Bot Name:" for your purposes. You can also add/delete questions to fit your goals.
    st.title("Enter Background Information Here")
    with st.form("user_form"):
        st.session_state.form_responses['Academic_read'] = st.text_input("Student Reading Performance - below average, average, above average:", key="Academic_read")
        st.session_state.form_responses['Academic_math'] = st.text_input("Student Math Performance - below average, average, above average:", key="Academic_math")
        st.session_state.form_responses['SRSS_I'] = st.text_input("SRSS-Internalizing Score:", key="SRSS_I")
        st.session_state.form_responses['SRSS-E'] = st.text_input("SRSS-Externalizing Score:", key="SRSS-E")
        st.session_state.form_responses['Days_missed'] = st.text_input("Number of Days Student has Missed:", key="Days_missed")
        st.session_state.form_responses['ODRs'] = st.text_input("Number of Office Discipline Referrals Earned:", key="ODRs")
        
        submit_button = st.form_submit_button("Submit Responses")
        if submit_button:
            st.session_state.form_submitted = True
            st.session_state.should_generate_response = True
    
    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    clear_button = st.button("Clear Chat")

# Process uploaded PDF
if uploaded_pdf:
    try:
        # Upload file using File API with mime_type specified
        uploaded_file = genai.upload_file(uploaded_pdf, mime_type="application/pdf")
        st.session_state.uploaded_file = uploaded_file
        st.success("File uploaded successfully!")
                  
    except Exception as e:
        st.error(f"Error uploading file: {e}")
        st.session_state.debug.append(f"File upload error: {e}")

# Clear chat function
if clear_button:
    st.session_state.messages = []
    st.session_state.debug = []
    st.session_state.pdf_content = ""
    st.session_state.chat_session = None
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
    # Create combined prompt from responses
    combined_prompt = "Form Responses:\n"
    for q, a in st.session_state.form_responses.items():
        combined_prompt += f"{q}: {a}\n"
    
    # Add user message to chat history
    current_message = {"role": "user", "content": combined_prompt}
    st.session_state.messages.append(current_message)

    with st.chat_message("user"):
        st.markdown(current_message["content"])

    # Generate and display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # Initialize chat session if needed
        if st.session_state.chat_session is None:
            generation_config = {
                "temperature": st.session_state.temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            model = genai.GenerativeModel(
                model_name=st.session_state.model_name,
                generation_config=generation_config,
            )
            
            initial_messages = [
                {"role": "user", "parts": [f"System: {system_prompt}"]},
                {"role": "model", "parts": ["Understood. I will follow these instructions."]},
            ]
            
            if st.session_state.pdf_content:
                initial_messages.extend([
                    {"role": "user", "parts": [f"The following is the content of an uploaded PDF document. Please consider this information when responding to user queries:\n\n{st.session_state.pdf_content}"]},
                    {"role": "model", "parts": ["I have received and will consider the PDF content in our conversation."]}
                ])
            
            st.session_state.chat_session = model.start_chat(history=initial_messages)

        # Generate response with error handling
        try:
            response = st.session_state.chat_session.send_message(current_message["content"])
            full_response = response.text
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.debug.append("Assistant response generated")
        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
            st.session_state.debug.append(f"Error: {e}")

    st.session_state.should_generate_response = False
    st.rerun()

# User input
# The placeholder text "Your message:" can be customized to any desired prompt, e.g., "Message Creative Assistant...".
user_input = st.chat_input("Type here:")

if user_input:
    # Add user message to chat history
    current_message = {"role": "user", "content": user_input}
    st.session_state.messages.append(current_message)

    with st.chat_message("user"):
        st.markdown(current_message["content"])

    # Generate and display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # Prepare messages for Gemini API
        if st.session_state.chat_session is None:
            generation_config = {
                "temperature": st.session_state.temperature,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            }
            model = genai.GenerativeModel(
                model_name=st.session_state.model_name,
                generation_config=generation_config,
            )
            
            # Initialize chat with system prompt and PDF content
            initial_messages = [
                {"role": "user", "parts": [f"System: {system_prompt}"]},
                {"role": "model", "parts": ["Understood. I will follow these instructions."]},
            ]
            
            if st.session_state.pdf_content:
                initial_messages.extend([
                    {"role": "user", "parts": [f"The following is the content of an uploaded PDF document. Please consider this information when responding to user queries:\n\n{st.session_state.pdf_content}"]},
                    {"role": "model", "parts": ["I have received and will consider the PDF content in our conversation."]}
                ])
            
            st.session_state.chat_session = model.start_chat(history=initial_messages)

        # Generate response with error handling
        try:
            if st.session_state.uploaded_file:
                # If there's an uploaded file, include it in the generation
                response = st.session_state.chat_session.send_message([
                    st.session_state.uploaded_file,
                    current_message["content"]
                ])
            else:
                # Otherwise, just use the text prompt
                response = st.session_state.chat_session.send_message(current_message["content"])

            full_response = response.text
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.debug.append("Assistant response generated")

        except Exception as e:
            st.error(f"An error occurred while generating the response: {e}")
            st.session_state.debug.append(f"Error: {e}")

    st.rerun()

# Debug information
# You can remove this by adding # in front of each line

st.sidebar.title("Debug Info")
for debug_msg in st.session_state.debug:
    st.sidebar.text(debug_msg)
