# Add a form or input information to the side bar that gets sent to the model. 


# Initialize session state for form responses
# Add this code between st.set_page_config(page_title="Streamlit Chatbot", layout="wide") and Display image code block
if "form_submitted" not in st.session_state:
    st.session_state.form_submitted = False
if "form_responses" not in st.session_state:
    st.session_state.form_responses = {}
if "should_generate_response" not in st.session_state:
    st.session_state.should_generate_response = False


# Add form to sidebar
# In sidebar Add this code AFTER st.session_state.temperature = temperature  
# And BEFORE uploaded_pdf = st.file_uploader("Upload PDF", type=["pdf"])
# Modify the info e.g., ['Bot_Name'] and "Bot Name:" for your purposes. You can also add/delete questions to fit your goals.
    st.title("Complete this form first")
    with st.form("user_form"):
        st.session_state.form_responses['Bot_Name'] = st.text_input("Bot Name:", key="Bot_Name")
        st.session_state.form_responses['Bot_Role'] = st.text_input("Role of Bot:", key="Bot_Role")
        st.session_state.form_responses['Goal'] = st.text_input("Goal of Bot:", key="Goal")
        st.session_state.form_responses['Knowledge'] = st.text_input("Background Knowledge:", key="Knowledge")
        st.session_state.form_responses['Steps'] = st.text_input("Steps to follow:", key="Steps")
        st.session_state.form_responses['Guidelines'] = st.text_input("Guidelines for interaction:", key="Guidelines")
        
        submit_button = st.form_submit_button("Submit Responses")
        if submit_button:
            st.session_state.form_submitted = True
            st.session_state.should_generate_response = True

# Handle form submission and generate response
# Add this code AFTER display chat message code block and BEFORE user_input = st.chat_input("Your message:")
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
