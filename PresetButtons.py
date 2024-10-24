# Add Three Preset Buttons in Your Chat Window

# Paste directly ABOVE #display chat messages and AFTER system_prompt = load_text_file('instructions.txt')

# Create a container for the buttons - MOVED UP before chat messages display
button_container = st.container()
with button_container:
    # Create columns for button layout
    col1, col2, col3 = st.columns(3)
    
    # Define button configurations
    button_configs = [
        {
            "column": col1,
            "label": "Generate Summary",
            "prompt": "Please generate a concise summary of our entire discussion so far.",
        },
        {
            "column": col2,
            "label": "Extract Key Points",
            "prompt": "Please extract and list the main key points from our discussion.",
        },
        {
            "column": col3,
            "label": "Suggest Next Steps",
            "prompt": "Based on our discussion, what are the recommended next steps?",
        },
    ]

    # Function to handle button clicks
    def handle_button_click(prompt):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Use the same initialization logic as the chat input
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
            
            try:
                response = st.session_state.chat_session.send_message(prompt)
                full_response = response.text
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            except Exception as e:
                st.error(f"An error occurred: {e}")
        
        st.rerun()

    # Create buttons using the configurations
    for config in button_configs:
        if config["column"].button(config["label"]):
            handle_button_click(config["prompt"])
