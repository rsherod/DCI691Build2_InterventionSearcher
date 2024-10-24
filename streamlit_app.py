# DCI 691 Build 2 - Streamlit Bot (R. Beghetto, fall 2024)
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image

# Streamlit configuration
st.set_page_config(page_title="Streamlit Chatbot", layout="wide")

# Display image
# This code attempts to open and display an image file named 'Build2.png'.
# If successful, it shows the image with a caption. If there's an error, it displays an error message instead.
# You can customize this by changing the image file name and path. Supported image types include .png, .jpg, .jpeg, and .gif.
# To use a different image, replace 'Build2.png' with your desired image file name (e.g., 'my_custom_image.jpg').
image_path = 'Build2.png'
try:
    image = Image.open(image_path)
    st.image(image, caption='Created by YOUR NAME (2024)', use_column_width=True)
except Exception as e:
    st.error(f"Error loading image: {e}")

# Title and BotDescription 
# You can customize the title, description, and caption by modifying the text within the quotes.
st.title("Welcome Build 2 Bot!")
st.write("[Provide a description of your own bot for the user]")
st.caption("Note: This Bot can make mistakes. Check all important information.")

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
    uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
    clear_button = st.button("Clear Chat")

# Process uploaded PDF
if uploaded_pdf:
    try:
        pdf_reader = PdfReader(uploaded_pdf)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text() + "\n"
        st.session_state.pdf_content = pdf_text
        st.session_state.debug.append(f"PDF processed: {len(pdf_text)} characters")
        # Reset chat session when new PDF is uploaded
        st.session_state.chat_session = None
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
        st.session_state.debug.append(f"PDF processing error: {e}")

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

# User input
# The placeholder text "Your message:" can be customized to any desired prompt, e.g., "Message Creative Assistant...".
user_input = st.chat_input("Your message:")

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
