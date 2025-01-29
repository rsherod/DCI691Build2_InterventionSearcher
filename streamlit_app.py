# DCI 691 Build 2 - Intervention Grid Searcher (R. Sherod, fall 2024)
import streamlit as st
import google.generativeai as genai
from PIL import Image

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
    st.session_state.model_name = "gemini-exp-1206"
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
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

# Display image
image_path = 'Tier 2 and Tier 3 Intervention Grid Search.jpg'
try:
    image = Image.open(image_path)
    st.image(image, caption='Created by Rebecca Sherod (2024)<br>This work was supported, in part, by ASU\'s Mary Lou Fulton Teachers College (MLFTC). The opinions and findings expressed in this document are those of the author and do not necessarily reflect those of the funding agency.', use_column_width=True)
except Exception as e:
    st.error(f"Error loading image: {e}")

# Title and BotDescription 
st.header("Welcome to the Intervention Grid Searcher!")
st.write("The goal of this bot is to help you find Tier 2 and Tier 3 Interventions from the grids at your school. \n\nDirections: Use the panel on the left to upload the Tier 2 and Tier 3 Intervention Grid from your school. Then, answer the questions about the student or group of students you are interested in selecting an intervention for. When you are ready, hit 'Submit Responses' to begin the process.")
st.caption("Note: This Bot can make mistakes. Make sure you refer back to the intervention grid to determine if it is a good fit for the student or students.")

# Initialize Gemini client
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Sidebar for model and temperature selection
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>Settings</h1>", unsafe_allow_html=True)
    st.caption("Note: Different models have different request rate limits. Please refer to Google AI documentation for details.")
    
    model_option = st.selectbox(
        "Select Model:", ["gemini-pro", "gemini-pro-vision"]
    )
    
    if model_option != st.session_state.model_name:
        st.session_state.model_name = model_option
        st.session_state.messages = []
        st.session_state.chat_session = None
   
    # Improved File upload section
    st.markdown("<h1 style='text-align: center;'>Upload Intervention Grid</h1>", unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader("Upload:", type=["pdf"])

    if uploaded_pdf:
        try:
            # Read PDF content using PyPDF2
            pdf_reader = PyPDF2.PdfReader(uploaded_pdf)
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            
            # Store PDF content in session state
            st.session_state.pdf_content = pdf_text
            st.session_state.pdf_uploaded = True
            
            # Prepare file for Gemini
            uploaded_file = genai.upload_file(uploaded_pdf, mime_type="application/pdf")
            st.session_state.uploaded_file = uploaded_file
            
            st.success("✅ Intervention Grid uploaded and processed successfully!")
            
            # Add debug information
            st.session_state.debug.append("PDF processed and stored in session state")
            st.session_state.debug.append(f"PDF length: {len(pdf_text)} characters")
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.session_state.debug.append(f"File processing error: {str(e)}")
            # Reset states on error
            st.session_state.pdf_content = ""
            st.session_state.pdf_uploaded = False
            st.session_state.uploaded_file = None
    
    # Create a form to capture student background information
    st.markdown("<h1 style='text-align: center;'>Student Information</h1>", unsafe_allow_html=True)

    if 'form_responses' not in st.session_state:
        st.session_state.form_responses = {}

    with st.form("user_form"):
        # Dropdown for Reading Performance
        st.session_state.form_responses['Academic_read'] = st.selectbox(
            "Student Reading Performance:", 
            options=["Click to select", "below average", "average", "above average"], 
            key="Academic_read"
        )

        # Dropdown for Math Performance
        st.session_state.form_responses['Academic_math'] = st.selectbox(
            "Student Math Performance:", 
            options=["Click to select", "below average", "average", "above average"], 
            key="Academic_math"
        )

        # Dropdown for SRSS-Internalizing Score
        st.session_state.form_responses['SRSS_I'] = st.selectbox(
            "SRSS-Internalizing Score:", 
            options=["Click to select", "Low", "Moderate", "High"], 
            key="SRSS_I"
        )

        # Dropdown for SRSS-Externalizing Score
        st.session_state.form_responses['SRSS_E'] = st.selectbox(
            "SRSS-Externalizing Score:", 
            options=["Click to select", "Low", "Moderate", "High"], 
            key="SRSS_E"
        )

        # Dropdown for Days Missed
        st.session_state.form_responses['Days_missed'] = st.selectbox(
            "Number of Days Student has Missed:", 
            options=["Click to select", "0-5 days", "6-10 days", "11-15 days", "16+ days"], 
            key="Days_missed"
        )

        # Dropdown for Office Discipline Referrals
        st.session_state.form_responses['ODRs'] = st.selectbox(
            "Number of Office Discipline Referrals Earned:", 
            options=["Click to select", "0-1 referrals", "2-3 referrals", "4-5 referrals", "6+ referrals"], 
            key="ODRs"
        )

        # Submit button for the form
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
        st.session_state.pdf_content = ""
        st.session_state.chat_session = None
        st.session_state.pdf_uploaded = False
        st.session_state.uploaded_file = None
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
                    
                    if st.session_state.pdf_content:
                        initial_messages.extend([
                            {"role": "user", "parts": [f"Here is the intervention grid content to use for analysis:\n\n{st.session_state.pdf_content}"]},
                            {"role": "model", "parts": ["I have received the intervention grid content and will use it for analysis."]}
                        ])
                    
                    st.session_state.chat_session = model.start_chat(history=initial_messages)
                    st.session_state.debug.append("Chat session initialized successfully")
                except Exception as e:
                    st.error(f"Error initializing chat session: {str(e)}")
                    st.session_state.debug.append(f"Chat initialization error: {str(e)}")
                    st.stop()  # Use st.stop() instead of return

            # Generate response with error handling
            try:
                response = st.session_state.chat_session.send_message(combined_prompt)
                full_response = response.text
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                st.session_state.debug.append("Assistant response generated")
            except Exception as e:
                st.error(f"An error occurred while generating the response: {str(e)}")
                st.session_state.debug.append(f"Response generation error: {str(e)}")

        st.session_state.should_generate_response = False
        st.rerun()

# User input handling
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
                
                if st.session_state.pdf_content:
                    initial_messages.extend([
                        {"role": "user", "parts": [f"Here is the intervention grid content to use for analysis:\n\n{st.session_state.pdf_content}"]},
                        {"role": "model", "parts": ["I have received the intervention grid content and will use it for analysis."]}
                    ])
                
                st.session_state.chat_session = model.start_chat(history=initial_messages)
                st.session_state.debug.append("Chat session initialized successfully")
            except Exception as e:
                st.error(f"Error initializing chat session: {str(e)}")
                st.session_state.debug.append(f"Chat initialization error: {str(e)}")
                st.stop()  # Use st.stop() instead of return

        try:
            response = st.session_state.chat_session.send_message(user_input)
            full_response = response.text
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.debug.append("Assistant response generated")
        except Exception as e:
            st.error(f"An error occurred while generating the response: {str(e)}")
            st.session_state.debug.append(f"Response generation error: {str(e)}")

    st.rerun()

# Debug information
st.sidebar.title("Debug Info")
for debug_msg in st.session_state.debug:
    st.sidebar.text(debug_msg)
