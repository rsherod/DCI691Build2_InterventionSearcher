# DCI 691 Build 2 - Intervention Grid Searcher (R. Sherod, fall 2024)
import streamlit as st
import google.generativeai as genai
from PIL import Image
import PyPDF2 
import io 

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
    st.session_state.model_name = "gemini-2.0-pro-exp-02-05"
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
# New session state variable for tracking both Tier 2 and Tier 3 files
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {"tier2": None, "tier3": None}
if "chat_session" not in st.session_state:
    st.session_state.chat_session = None

# Display image
image_path = 'Tier 2 and Tier 3 Intervention Grid Search.jpg'
try:
    image = Image.open(image_path)
    # Create three columns with the middle one being wider
    col1, col2, col3 = st.columns([1,6,1])
    # Display the image in the middle column
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

# Initialize Gemini client
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# Sidebar for model and temperature selection and file uploads
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>Settings</h1>", unsafe_allow_html=True)
    st.caption("Note: Different models have different request rate limits. Please refer to Google AI documentation for details.")
    
    model_option = st.selectbox(
        "Select Model:", ["gemini-2.0-pro-exp-02-05", "gemini-2.0-flash"]
    )
    
    if model_option != st.session_state.model_name:
        st.session_state.model_name = model_option
        st.session_state.messages = []
        st.session_state.chat_session = None
   
    # Define the process_pdf function for handling PDF uploads
    def process_pdf(uploaded_pdf):
        try:
            # Create a PyPDF2 reader object from the uploaded file
            pdf_bytes = io.BytesIO(uploaded_pdf.read())
            pdf_reader = PyPDF2.PdfReader(pdf_bytes)
            
            # Extract text from all pages
            pdf_text = ""
            for page in pdf_reader.pages:
                pdf_text += page.extract_text()
            
            # Reset file pointer for potential reuse
            pdf_bytes.seek(0)
            uploaded_pdf.seek(0)
            
            return pdf_text, None  # Return None as error if successful
        except Exception as e:
            return None, str(e)  # Return the error message if failed

    # File upload section with separate uploaders for Tier 2 and Tier 3
    st.markdown("<h1 style='text-align: center;'>Upload Intervention Grid</h1>", unsafe_allow_html=True)
    st.subheader("Upload Your Intervention Documents")
    st.caption("Note: If your school has separate documents for Tier 2 and Tier 3 interventions, you can upload both. If you have a single combined document, you can upload it to either field.")
    
    # Create separate uploaders for Tier 2 and Tier 3
    tier2_pdf = st.file_uploader("Upload Tier 2 (Secondary) Interventions:", type=["pdf"])
    tier3_pdf = st.file_uploader("Upload Tier 3 (Tertiary) Interventions:", type=["pdf"])

    # Initialize variables to store content
    combined_pdf_text = ""
    upload_success = False

    # Process Tier 2 document if provided
    if tier2_pdf:
        tier2_text, error = process_pdf(tier2_pdf)
        if error:
            st.error(f"Error processing Tier 2 document: {error}")
            st.session_state.debug.append(f"Tier 2 processing error: {error}")
        else:
            combined_pdf_text += "--- Tier 2 Interventions ---\n" + tier2_text
            upload_success = True
            st.session_state.uploaded_files["tier2"] = tier2_pdf

    # Process Tier 3 document if provided
    if tier3_pdf:
        tier3_text, error = process_pdf(tier3_pdf)
        if error:
            st.error(f"Error processing Tier 3 document: {error}")
            st.session_state.debug.append(f"Tier 3 processing error: {error}")
        else:
            combined_pdf_text += "\n\n--- Tier 3 Interventions ---\n" + tier3_text
            upload_success = True
            st.session_state.uploaded_files["tier3"] = tier3_pdf

    # Update session state if any upload was successful
    if upload_success:
        st.session_state.pdf_content = combined_pdf_text
        st.session_state.pdf_uploaded = True
        st.success("✅ Intervention Grid(s) uploaded and processed successfully!")
        st.session_state.debug.append("PDF(s) processed and stored in session state")
        st.session_state.debug.append(f"Combined PDF length: {len(combined_pdf_text)} characters")
    
    # Student Information Form Section
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
    
    # Clear chat functionality - now also clears both PDF uploads
    clear_button = st.button("Clear Chat")
    if clear_button:
        st.session_state.messages = []
        st.session_state.debug = []
        st.session_state.pdf_content = ""
        st.session_state.chat_session = None
        st.session_state.pdf_uploaded = False
        st.session_state.uploaded_files = {"tier2": None, "tier3": None}
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
                    st.stop()

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
