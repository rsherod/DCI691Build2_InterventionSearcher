# DCI 691 Build 2 - Streamlit Bot (R. Beghetto, fall 2024)
# Importing necessary libraries
# This section brings in external code libraries that add functionality to our program.
# Streamlit (st) is used to create web applications, google.generativeai helps with AI text generation,
# PyPDF2 allows reading PDF files, and PIL (Python Imaging Library) helps with image processing.
import streamlit as st
import google.generativeai as genai
from PyPDF2 import PdfReader
from PIL import Image

# Streamlit configuration
# This sets up the basic properties of the web application.
# It sets the title that appears in the browser tab and makes the layout use the full width of the screen.
# You can customize the page title (e.g., Creative Assistant" and layout by modifying these parameters.
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
# This adds a main title to the web page and a description of the chatbot.
# It also includes a note to remind users that the bot can make mistakes.
# You can customize the title, description, and caption by modifying the text within the quotes.
st.title("Welcome Build 2 Bot!")
st.write("[Provide a description of your own bot for the user]")
st.caption("Note: This Bot can make mistakes. Check all important information.")

# Initialize Gemini client
# This sets up the connection to the Gemini AI service using an API key.
# The API key is a secret code that allows our application to use the Gemini service.
# You need to set up their own API key in the Streamlit secrets management system.
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Initialize session state
# This creates variables that persist across multiple interactions with the web application.
# These variables store things like chat messages, AI model settings, and uploaded PDF content.
# You can add new session state variables here if they want to store additional information.
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
# This creates a sidebar on the web page with controls for the user to adjust settings.
# Users can select different AI models and adjust the "temperature" which affects how creative the AI's responses are.
# To add more customization options, users can add new input elements (e.g., buttons, sliders) to this sidebar.
# For example, to add a new button: clear_button = st.sidebar.button("New Custom Action")
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
# This section handles the PDF file that a user might upload.
# It reads the text content of the PDF and stores it for the chatbot to use in responses.
# You can upload any PDF file, and the system will extract its text content.

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
# This function is triggered when the user clicks the "Clear Chat" button.
# It resets all the chat-related variables, effectively starting a new conversation.
# You can modify this function to clear additional custom variables if needed.
if clear_button:
    st.session_state.messages = []
    st.session_state.debug = []
    st.session_state.pdf_content = ""
    st.session_state.chat_session = None
    st.rerun()

# Load system prompt
# This function reads a text file containing instructions for the chatbot.
# These instructions guide how the chatbot should behave and respond to user inputs.
# You can customize the chatbot's behavior by modifying the content of the 'instructions.txt' file.
# This file should contain the desired system prompt or instructions for the AI model.
def load_text_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        st.error(f"Error loading text file: {e}")
        return ""

system_prompt = load_text_file('instructions.txt')

# Display chat messages
# This section shows all the messages exchanged between the user and the chatbot.
# It creates a visual representation of the conversation on the web page.
# You can customize the appearance of messages by modifying the Streamlit markdown styling.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
# This creates a text input field where users can type their messages to the chatbot.
# The placeholder text "Your message:" can be customized to any desired prompt, e.g., "Message Creative Assistant...".
user_input = st.chat_input("Your message:")

if user_input:
    # Add user message to chat history
    # This stores the user's message in the conversation history.
    current_message = {"role": "user", "content": user_input}
    st.session_state.messages.append(current_message)

    with st.chat_message("user"):
        st.markdown(current_message["content"])

    # Generate and display assistant response
    # This section handles the chatbot's response to the user's input.
    # It uses the Gemini AI model to generate responses based on the conversation history and system prompt.
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        # Prepare messages for Gemini API
        # This part sets up the AI model with the chosen settings if it hasn't been done yet.
        # You can modify the generation_config parameters to fine-tune the AI's behavior.
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
            # The system prompt contains instructions for how the chatbot should behave.
            # If a PDF was uploaded, its content is also included to give the chatbot context.
            # You can modify this section to add additional context or instructions for the AI model.
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
        # This tries to get a response from the AI model and display it.
        # If there's an error, it shows an error message instead.
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
# This displays technical information about what's happening in the application.
# It's useful for developers to understand how the program is working or to identify issues.
# If errors occur, users can copy the error message and the full code, then paste it into AI assistants like Claude,
# ChatGPT, or Google Gemini for debugging help. These AI tools can suggest fixes or explain the error.
# Youcan also ask these AI assistants for help with customizing the interface, such as adding new buttons to the sidebar or modifying the layout. 
# Simply describe the desired changes and ask for code suggestions.

st.sidebar.title("Debug Info")
for debug_msg in st.session_state.debug:
    st.sidebar.text(debug_msg)
